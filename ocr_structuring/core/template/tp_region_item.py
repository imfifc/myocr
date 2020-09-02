import copy
from collections import OrderedDict
from typing import Dict, List
import numpy as np
from ..models.structure_item import StructureItem
from .models import FilterArea
from .tp_node_item import TpNodeItem
from ..utils.bbox import BBox
from ocr_structuring.utils.logging import logger


class RegionItem:
    def __init__(self,
                 item_name,
                 filter_confs,
                 post_func=None):
        """
        :param item_name: 对应模板文件当中的 show_name
        :param filter_confs: dict.
                key: filter_areas、filter_contents、filter_regexs、filter_thresh_w
                value: 配置文件中对应的值
        :param post_func: 后处理函数，返回每个字段结构化的最终结果、置信度等信息，在 filter_area 之后调用
        """
        self.item_name = item_name

        filter_areas = filter_confs.get('filter_areas', None)
        if filter_areas is None:
            filter_areas = []

        self.filter_areas: List[FilterArea] = []
        for it in filter_areas:
            self.filter_areas.append(FilterArea(
                BBox(it['area']),
                it.get('w', 1.0),
                it.get('ioo_thresh', 0)
            ))

        self.post_func = post_func

        self.node_items: Dict[int, TpNodeItem] = {}
        self.node_items_backup = {}

    def load_data(self, node_items: Dict[int, TpNodeItem]):
        """
        深拷贝一份 node_items
        :param node_items: Dict[int, TpNodeItem]
        """
        self.node_items = copy.deepcopy(node_items)
        self.node_items_backup = copy.deepcopy(node_items)

    def run_parse(self, img: np.ndarray, structure_items: Dict[str, StructureItem]):
        """
        :param img: numpy 图片，在处理过程中注意不能对原图进行修改
        :param structure_items:
        :return:
        """
        res = None
        if self.filter_areas:
            # 对多个 filter_area 按照权重顺序进行搜索，如果搜索到正确结果就返回
            self.filter_areas.sort(key=lambda x: x.w, reverse=True)
            for area_item in self.filter_areas:
                res = self._run_parse(img, structure_items, area_item)
                if res is None:
                    self.node_items = copy.deepcopy(self.node_items_backup)
                else:
                    break
        else:
            res = self._run_parse(img, structure_items)

        return res

    def _run_parse(self, img: np.ndarray, structure_items: Dict[str, StructureItem], area_item: FilterArea = None):
        self.filter_area(area_item=area_item)

        return self.run_post_func(img, structure_items)

    # @save_debug_data
    def filter_area(self, area_item: FilterArea = None):
        """
        :param area_item:
        :return:
        """
        if not area_item:
            return

        for node_item in self.node_items.values():
            if node_item.is_filtered:
                continue

            if node_item.trans_bbox.cal_ioo(area_item.area) > area_item.ioo_thresh:
                node_item.filter_areas.append(area_item)
            else:
                node_item.is_filtered_by_area = True

    def run_post_func(self, img: np.ndarray, structure_items: Dict[str, StructureItem]):
        """
        在 filter_area 之后调用，这个函数会输出 StructureItem
        :param img: BGR ndarray 原始图像
        :param structure_items:
        """
        if self.post_func is None:
            return

        passed_nodes = self.get_passed_nodes()

        if len(passed_nodes) == 0:
            return

        try:
            return self.post_func(self.item_name,
                                  passed_nodes=passed_nodes,
                                  node_items=self.node_items,
                                  img=img,
                                  structure_items=structure_items)
        except Exception as e:
            logger.exception('Error run [%s] post_func: %s. Error: %s' % (self.item_name, self.post_func, e))

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
