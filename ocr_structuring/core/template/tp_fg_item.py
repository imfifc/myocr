import copy
import re
from collections import OrderedDict
from functools import wraps
from typing import Dict, List

import numpy as np

from .models import FilterArea, FilterRegex
from .tp_node_item import TpNodeItem
from ..utils import str_util
from ..utils.bbox import BBox
from ..utils.debug_data import DebugData
from ocr_structuring.utils.logging import logger
from ..utils.structuring_viz.viz_fg_item import viz_area_filter, viz_regex_filter, viz_post_func, viz_pre_func
from ..utils.debug_data import DEBUG_FLAG_FILTER_NOT_RUN, debug_filter_wrapper, DebugData

class EnlargeSearchStrategy:
    """
    按照配置文件扩大一下匹配的区域
    """

    def __init__(self, w_pad, h_pad):
        """
        :param w_pad: 宽度方向单边 padding 的比例
        :param h_pad: 高度方向单片 padding 的比例
        """
        self.w_pad = w_pad
        self.h_pad = h_pad

    def apply(self, filter_areas):
        if not filter_areas:
            return

        for filter_area in filter_areas:
            _area = [it for it in filter_area.area]
            h = _area[3] - _area[1]
            w = _area[2] - _area[0]
            _area[0] = _area[0] - int(w * self.w_pad)
            _area[2] = _area[2] + int(w * self.w_pad)

            _area[1] = _area[1] - int(h * self.h_pad)
            _area[3] = _area[3] + int(h * self.h_pad)

            _area[0] = max(_area[0], 0)
            _area[1] = max(_area[1], 0)
            filter_area.area.update(_area)


class FGItem:
    NONE_RES = (None, [0])

    def __init__(self,
                 item_name,
                 show_name,
                 filter_confs,
                 pre_func=None,
                 post_func=None,
                 post_regex_filter_func=None,
                 should_output=True,
                 search_strategy=None,
                 debug_data: DebugData = None):

        """
        :param item_name: 对应模板文件当中的 item_name
        :param show_name: 对应模板文件当中的 show_name
        :param filter_confs: dict.
                key: filter_areas、filter_contents、filter_regexs、filter_thresh_w
                value: 配置文件中对应的值
        :param pre_func: 预处理函数，主要用来修改作用 node_item 里的文本类容，在 filter_regex 之前调用
        :param post_func: 后处理函数，返回每个字段结构化的最终结果、置信度等信息，在 filter_regex 之后调用
        :param search_strategy: 搜索策略
        """
        self.item_name = item_name
        self.show_name = show_name
        self.should_output = should_output

        filter_areas = filter_confs.get('filter_areas', None)
        if filter_areas is None:
            filter_areas = []

        self.filter_areas: List[FilterArea] = []
        for it in filter_areas:
            self.filter_areas.append(FilterArea(
                BBox(it['area']),
                it['w'],
                it.get('ioo_thresh', 0)
            ))
        # filter_contents 是List[str]
        self.filter_contents = filter_confs.get('filter_contents', None)

        filter_regexes = filter_confs.get('filter_regexs', None)
        if filter_regexes is None:
            filter_regexes = []

        self.filter_regexes: List[FilterRegex] = []
        for it in filter_regexes:
            self.filter_regexes.append(FilterRegex(
                it['regex'],
                it['w']
            ))

        self.pre_func = pre_func
        self.post_func = post_func
        self.post_regex_filter_func = post_regex_filter_func

        self.search_strategy = search_strategy

        self.node_items: Dict[int, TpNodeItem] = {}
        self.node_items_backup = {}

        self.regex_failed_tp_rects = []

        # 考虑到金额的识别中，pass_node中最终选定的内容往往和模板中的位置存在偏移
        # 而对于前景字，可以在以下的变量中记录偏移的情况,在后续处理中使用
        self.offset_value = None

        if isinstance(self.search_strategy, EnlargeSearchStrategy):
            self.search_strategy.apply(self.filter_areas)

    def load_data(self, node_items: Dict[int, TpNodeItem]):
        """
        深拷贝一份 node_items
        :param node_items: Dict[int, TpNodeItem]
        """
        self.node_items = copy.deepcopy(node_items)
        self.node_items_backup = copy.deepcopy(node_items)

    def run_parse(self, img: np.ndarray, debug_data: DebugData = None):
        """
        :param img: numpy 图片，在处理过程中注意不能对原图进行修改
        :return:
        """
        self.debug_data = debug_data

        res = None
        if self.filter_areas:
            # 对多个 filter_area 按照权重顺序进行搜索，如果搜索到正确结果就返回
            self.filter_areas.sort(key=lambda x: x.w, reverse=True)
            for area_item in self.filter_areas:
                res = self._run_parse(img, area_item)
                if res is None:
                    self.node_items = copy.deepcopy(self.node_items_backup)
                else:
                    break
        else:
            res = self._run_parse(img)

        return res

    def _run_parse(self, img: np.ndarray, area_item: FilterArea = None):

        self.filter_area(area_item=area_item)

        self.filter_content()

        self.run_pre_func(img)

        self.filter_regex()

        self.post_filter_regex(img)

        return self.run_post_func(img)

    @debug_filter_wrapper
    def filter_content(self):
        if not self.filter_contents:
            # 说明没有设置filter_contents，则什么都不处理
            return DEBUG_FLAG_FILTER_NOT_RUN

        # 遍历所有的node_items:
        for node_item in self.node_items.values():
            if node_item.is_filtered:
                continue
            # 判断node_item的内容是否在filter_contents中
            contain_filter_contents = False
            for content in self.filter_contents:
                if content in node_item.text:
                    contain_filter_contents = True
            # 如果最终仍然没有包含了指定的字符，则把其过滤掉
            if not contain_filter_contents:
                node_item.is_filtered_by_content = True

    @debug_filter_wrapper
    def filter_area(self, area_item: FilterArea = None):
        """
        :param area_item:
        :return:
        """
        if not area_item:
            return DEBUG_FLAG_FILTER_NOT_RUN

        for node_item in self.node_items.values():
            if node_item.is_filtered:
                continue
            if node_item.trans_bbox.cal_ioo(area_item.area) > area_item.ioo_thresh:
                node_item.filter_areas.append(area_item)
            else:
                node_item.is_filtered_by_area = True

            # if is_passed and tp_rect.text_type != LabelNode.TEXT_TYPE_BG:
            #     self.contents_after_filter_area.append(tp_rect.content)


    def post_filter_regex(self, img):
        """
        预处理函数，在 filter_area 之后调用，主要目的是防止area_filter 对错误的前景偏移后的图片把所有的node_item全部过滤掉
        处理的函数建议使用 每个 node_item的 背景缩放后的坐标进行分析， 并且对于可能被保留的pass_node ，将其  is_filtered_by_area 重新设置为False
        :param img: BGR numpy 原始图像
        :return TemplateParserData
        """
        if self.post_regex_filter_func is None:
            return

        passed_nodes = self.get_passed_nodes()

        if len(passed_nodes) == 0:
            try:
                self.post_regex_filter_func(self.item_name, node_items=self.node_items, img=img)
                passed_nodes = self.get_passed_nodes()
                if len(passed_nodes) != 0:
                    # 说明捞回来一些node
                    self.filter_content()
                    self.run_pre_func(img)
                    self.filter_regex()

            except Exception as e:
                logger.exception('Error run [%s] pre_func: %s since %s' % (self.item_name, self.pre_func, e))

    #@viz_regex_filter
    @debug_filter_wrapper
    def filter_regex(self):
        if not self.filter_regexes:
            return DEBUG_FLAG_FILTER_NOT_RUN

        for node_item in self.node_items.values():
            if node_item.is_filtered or node_item.is_bg_item:
                continue

            is_filtered_by_regex = True
            for f in self.filter_regexes:
                m = re.search(f.regex, node_item.text)
                if m:
                    scores = node_item.scores
                    if len(scores) > 0 and m.end(1) <= len(scores):
                        scores = scores[m.start(1):m.end(1)]

                    node_item.filter_regexes.append(f)
                    node_item.add_regex_match_res(f.w, m.group(1), scores)
                    is_filtered_by_regex = False

            node_item.is_filtered_by_regex = is_filtered_by_regex
            if is_filtered_by_regex:
                self.regex_failed_tp_rects.append(node_item)

    def run_pre_func(self, img: np.ndarray):
        """
        预处理函数，在 filter_regex 之前调用，主要目的是修改 node_items 中的 text
        :param img: BGR numpy 原始图像
        :return TemplateParserData
        """
        if self.pre_func is None:
            return

        passed_nodes = self.get_passed_nodes()

        if len(passed_nodes) == 0:
            return

        try:
            self.pre_func(self.item_name,
                          passed_nodes,
                          node_items=self.node_items,
                          img=img)
        except Exception as e:
            logger.exception('Error run [%s] pre_func: %s since %s' % (self.item_name, self.pre_func, e))

    def run_post_func(self, img: np.ndarray):
        """
        在 filter_regex 之后调用，这个函数会输出最后结构化以后的结果
        :param img: BGR ndarray 原始图像
        """
        if self.post_func is None:
            return

        passed_nodes = self.get_passed_nodes()

        if len(passed_nodes) == 0:
            return

        try:
            res = self.post_func(self.item_name,
                                 passed_nodes=passed_nodes,
                                 node_items=self.node_items,
                                 img=img)

            if res is None:
                return
        except Exception as e:
            logger.exception('Error run [%s] post_func: %s. Error: %s' % (self.item_name, self.post_func, e))
            return

        return res

    def get_passed_nodes(self):
        """
        返回 pass 了，并且不是背景的 node_items
        :return:
        """
        res = OrderedDict()
        for k, v in self.node_items.items():
            if v.is_filtered or v.is_bg_item or v.is_empty:
                continue

            res[k] = v
        return res
