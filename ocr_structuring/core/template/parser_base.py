# encoding=utf-8
import copy
import datetime as dt
import functools
from collections import OrderedDict
from datetime import datetime
from typing import Dict

import numpy as np
from numpy import ndarray

from .tp_fg_item import FGItem, EnlargeSearchStrategy
from .tp_node_item import TpNodeItem
from .tp_region_item import RegionItem
from ..models.structure_item import StructureItem
from ..utils import str_util, date_util
from ..utils.crnn.crnn_util import CRNNUtil

from ..utils.debug_data import DebugData
from ..utils.exception import ConfigException
from ..utils.node_item_group import NodeItemGroup
from ..utils.structuring_viz.viz_special_method import viz_post_crnn_date
from ocr_structuring.utils.logging import logger


class ParseBase:
    """
    该类中仅存放和模板解析流程相关的函数，不存放任何业务代码
    """

    subclasses = {}

    # need python 3.6: https://stackoverflow.com/questions/5189232/how-to-auto-register-a-class-when-its-defined
    def __init_subclass__(cls, **kwargs):
        """
        注册所有子类
        """
        super().__init_subclass__(**kwargs)

        parser_name = str_util.camel_to_underline(cls.__name__)
        if (
            "common_parser" not in parser_name
            and "dummy_test_parser" not in parser_name
        ):
            cls.subclasses[parser_name] = cls

    def __init__(self, class_name: str, conf: Dict):

        """
        :param conf:
        """
        self.class_name = class_name
        self.conf = copy.deepcopy(conf)
        # 是否为 OCR 训练平台生成的配置文件
        self.is_tp_conf = self.conf.get("is_tp_conf", False)
        self.fg_items = self._init_fg_items(class_name, conf)
        self.region_items = self._init_region_items(class_name, conf)
        self._crnn_util = CRNNUtil()

        self._other_parser_info = {}  # 用一个字典来记录所有的中间过程中的信息

    def parse_template(
        self,
        node_items: Dict[int, TpNodeItem],
        img: np.ndarray,
        debug_data: DebugData = None,
    ):
        """
        :param node_items:
        :param img: ndarray BGR image 在某些环节中可能有重识别的步骤，需要用到原始图片
        :return: dict[StructureItem]
        """
        structure_items = {}
        for fg_item in self.fg_items.values():
            fg_item.load_data(node_items)
            item_result = fg_item.run_parse(img, debug_data=debug_data)
            if item_result is None:
                content, scores = "", [0]
            else:
                content, scores = item_result

            si = StructureItem(
                item_name=fg_item.item_name,
                show_name=fg_item.show_name,
                content=content,
                scores=scores,
            )

            structure_items[fg_item.item_name] = si

        for region_item in self.region_items.values():
            region_item.load_data(node_items)
            region_item.run_parse(img, structure_items)

        # 通过structure_items 传入image，防止在后处理阶段可能会使用到图片相关的信息
        structure_items = self.tmpl_post_proc(structure_items, self.fg_items, img)

        # 删除 should_output 为 false 的结构化结果
        for fg_item in self.fg_items.values():
            if fg_item.item_name not in structure_items:
                continue

            if fg_item.should_output is False:
                logger.info(
                    f"Delete structure item should not output: {fg_item.item_name}"
                )
                del structure_items[fg_item.item_name]

        return structure_items

    def tmpl_post_proc(self, structure_items, fg_items, img):
        """
        在 item post func 之后调用。
        - 有些字段可能要从其它字段中获取
        - 有些字段可能是由多个字段合成的
        :param structure_items: dict[StructureItem]
        :return:
        """
        return structure_items

    def _init_fg_items(self, class_name: str, conf: Dict) -> Dict[str, FGItem]:
        """
        处理函数加载优先级：
        1. 配置文件配置了 item_pre_func/item_post_func，寻找指定的函数
        2. 配置文件没有配置 item_pre_func/item_post_func，按照约定找：_pre_func_{item_name} / _post_func_{item_name}
        - 预处理：如果不存在则没有预处理函数
        - 后处理：如果不存在则使用 _post_func_max_w_regex

        Args:
            class_name:
            conf:

        Returns:

        """
        if "fg_items" not in conf:
            raise ConfigException(f"fg_items not exist in {class_name}.yml")

        res = {}
        for item in conf["fg_items"]:
            item_name = item.get("item_name", None)
            item_show_name = item.get("show_name", None)

            if item_name is None:
                raise ConfigException(
                    f"[{class_name}] FG item [{item_name}] miss [item_name] key"
                )

            item_pre_func = self._get_pre_post_func(item, "item_pre_func", class_name)
            item_post_func = self._get_pre_post_func(item, "item_post_func", class_name)

            # 如果模板没有填后处理函数，则默认使用 _post_func_max_w_regex 作为后处理函数
            if item_post_func is None:
                item_post_func = self._get_item_func("_post_func_max_w_regex")

            # 获得 filters
            if self.is_tp_conf:
                filter_areas = []
                if "area" in item:
                    filter_areas.append(
                        {
                            "area": item["area"],
                            "w": 1,
                            "ioo_thresh": item.get("ioo_thresh", 0),
                        }
                    )

                if len(filter_areas) == 0:
                    filter_areas = None

                filter_regexs = item.get("filter_regexs", [])
                for r in filter_regexs:
                    r["w"] = 1

                filter_confs = {
                    "filter_areas": filter_areas,
                    "filter_contents": item.get("filter_contents", None),
                    "filter_regexs": filter_regexs,
                }
            else:
                filter_confs = {
                    "filter_areas": item.get("filter_areas", None),
                    "filter_contents": item.get("filter_contents", None),
                    "filter_regexs": item.get("filter_regexs", None),
                }

            # 获取 search_strategy 的参数
            search_strategy = None
            search_strategy_item = item.get("search_strategy", None)
            if search_strategy_item is not None:
                search_mode = search_strategy_item.get("mode", None)
                if search_mode is None:
                    s = f"[{class_name}] FG item [{item_name}] set search_strategy, but not set [mode] key"
                    raise ConfigException(s)

                w_pad = search_strategy_item.get("w_pad", 0)
                h_pad = search_strategy_item.get("h_pad", 0)
                logger.debug(
                    f"Enlarge {class_name} [{item_name}] search area: w_pad {w_pad} h_pad {h_pad}"
                )
                search_strategy = EnlargeSearchStrategy(w_pad, h_pad)

            post_regex_filter_func_name = item.get("item_post_regex_filter_func")
            post_regex_filter_func = self._get_item_func(post_regex_filter_func_name)

            res[item_name] = FGItem(
                item_name,
                item_show_name,
                filter_confs,
                item_pre_func,
                item_post_func,
                post_regex_filter_func,
                should_output=item.get("should_output", True),
                search_strategy=search_strategy,
            )

        return res

    def _get_pre_post_func(self, item, func_key_name: str, class_name: str):
        """
        1. 从 parser 中获得 item_pre_func/item_post_func 对应的函数，如果
           配置文件中没有配置，则会尝试去找 _pre_func_{item_name}/_post_func_{item_name}
        2. 读取配置文件中 kwargs 参数，并使用 partial 传递这些参数

        Args:
            item: fg_item
            func_key_name: item_pre_func/item_post_func
            class_name:

        Returns:

        """
        item_name = item.get("item_name")

        is_pre_func = func_key_name.split("_")[1] == "pre"
        func_key_exist = func_key_name in item
        if func_key_exist:
            item_func_para = item.get(func_key_name)
            if item_func_para == {}:
                item_func_para = None
        else:
            # 配置文件中没有预处理、后处理函数配置，尝试加载以 item_name 为后缀的预处理/后处理函数
            if is_pre_func:
                item_func_para = f"_pre_func_{item_name}"
            else:
                item_func_para = f"_post_func_{item_name}"

        if type(item_func_para) == dict:
            try:
                item_func_name = item_func_para["func"]
            except KeyError:
                raise ConfigException(
                    f"[{class_name}] FG item [{item_name}] [{func_key_name}] must set 'func' key"
                )
        else:
            item_func_name = item_func_para

        if self.is_tp_conf:
            if (
                item_func_name.replace("_pre_func_", "").replace("_post_func_", "")
                != item_name
            ):
                raise ConfigException(
                    f"{item_func_name} was not found in [{class_name}] parser"
                )

        try:
            item_func = self._get_item_func(item_func_name, print_err=False)
        except ConfigException as e:
            # 预处理函数加载失败表示没有任何预处理
            # 后处理函数加载失败表示使用默认后处理 _post_func_max_w_regex
            return None

        if type(item_func_para) == dict:
            if not item_func:
                # item_func 无效时直接返回
                return item_func
            other_kwargs = item_func_para.get("kwargs", None)
            if other_kwargs:
                item_func = functools.partial(item_func, **other_kwargs)

        return item_func

    def _init_region_items(self, class_name: str, conf: Dict) -> Dict[str, RegionItem]:
        """
        处理函数加载优先级：
        1. 配置文件配置了 region_post_func/region_func，寻找指定的函数，找不到抛异常
        2. 配置文件没有配置 region_post_func/region_func 按照约定找：_region_func_{item_name}，找不到抛异常

        Args:
            class_name:
            conf:

        Returns:

        """
        region_items = conf.get("region_items", None)
        if not region_items:
            return {}

        out = {}
        for item in region_items:
            item_name = item.get("item_name", None)
            if item_name is None:
                raise ConfigException(
                    f"[{class_name}] Region item [{item_name}] miss [item_name] key"
                )

            if self.is_tp_conf:
                filter_confs = {
                    "filter_areas": [
                        {
                            "area": item.get("area"),
                            "ioo_thresh": item.get("ioo_thresh", 0),
                        }
                    ]
                }
            else:
                filter_confs = {"filter_areas": item.get("filter_areas")}

            region_func = item.get("region_post_func")
            if region_func is None:
                region_func = item.get("region_func")

            if region_func is None:
                region_func = f"_region_func_{item_name}"

            if isinstance(region_func, dict):
                args = region_func.get("args")
                kwargs = region_func.get("kwargs")

                func = region_func.get("func")

                if func is None:
                    raise ConfigException(
                        f"[{class_name}] Region item [{region_func}] miss [func] key"
                    )

                region_func = self._get_item_func(func)

                if args:
                    region_func = functools.partial(region_func, *args)
                if kwargs:
                    region_func = functools.partial(region_func, **kwargs)

            else:
                region_func = self._get_item_func(region_func)

            out[item_name] = RegionItem(item_name, filter_confs, post_func=region_func)

        return out

    def _get_item_func(self, func_name, print_err: bool = True):
        func = None
        if func_name is not None and func_name != "":
            try:
                func = getattr(self, func_name)
            except Exception:
                if print_err:
                    raise ConfigException(
                        f"{self.__class__.__name__} item function [{func_name}] not found"
                    )
                else:
                    raise ConfigException()

        return func

    def _post_func_return_const_val(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
        const_val: "",
    ):
        """
        用于返回一个固定的值，例如医疗发票的 city 字段，在确定了模板类型以后可以返回固定值
        如果使用了该 post 函数，必须在 fg_item 的配置项目中添加 post_func_const_val 项
        """
        return const_val, [1]

    def _pre_func_serialnumber(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: ndarray,
        min_length: int,
    ):
        filtered_rect_data_dict = self._filter_by_min_length(passed_nodes, min_length)
        self._pre_func_crnn_num_bigeng(
            item_name, filtered_rect_data_dict, node_items, img
        )

    def _filter_by_min_length(
        self,
        rect_data_dict: Dict[str, TpNodeItem],
        min_length,
        consider_space=False,
        not_contain_chn=True,
    ):
        """
        仅返回 rect_data.content 长度大于 min_length 的 rect_data
        """

        filtered_rect_data_dict = OrderedDict()
        for rect_data_id in rect_data_dict:
            rect_data = rect_data_dict[rect_data_id]
            if consider_space:
                text = rect_data.text
            else:
                text = str_util.remove_space(rect_data.text)
            if not_contain_chn:
                text = str_util.filter_num_eng(text)
            if len(text) > min_length:
                filtered_rect_data_dict[rect_data_id] = rect_data
        return filtered_rect_data_dict

    def _pre_func_crnn_num_bigeng(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
    ):

        for node in passed_nodes.values():
            roi = node.bbox
            crnn_res, scores = self._crnn_util.run_number_capital_eng(img, roi.rect)
            if crnn_res != node.text:
                logger.debug("item_name: {} crnn_num_bigeng:".format(item_name))
                logger.debug("\tOrigin: {}".format(node))
                logger.debug("\tCRNN result: {}".format(crnn_res))
            if crnn_res is not None:
                node.text = crnn_res
                node.scores = scores

    @viz_post_crnn_date
    def _post_func_crnn_date(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
    ):
        """
        对日期字段的候选框进行 merge，然后使用 carnn 进行重识别
        """
        # TO-DO,viz now is not supported
        # DEBUG_VIZ = False
        # 对这种情况做处理 '2017-11-28_9:20:38日'
        origin_text = ""
        for node in passed_nodes.values():
            origin_text += node.text

        # 首先，clean 掉所有的 可能的类似于 含有时分秒的问题,'2017-11-28_9:20:38'
        changed_res = date_util.filter_year_month_day(passed_nodes)
        if changed_res:
            for row in changed_res:
                logger.debug(
                    f"[{item_name}] change {row[0]} to {row[1]} due to it has sec and hour info"
                )

        # 这里应该是要过滤掉所有的数字部分过多的，一看就是序列号一类的node
        # 这个方法会对如同 '2017._00___82___84付___2017' 的情形过滤掉
        passed_nodes = OrderedDict(
            filter(
                lambda x: str_util.count_max_continous_num(x[1].text) < 8,
                passed_nodes.items(),
            )
        )

        if len(passed_nodes) == 0:
            return

        # 将在一行上的bbox找出
        nodes_in_line = NodeItemGroup.find_row_lines(passed_nodes, y_thresh=0.6)
        # 先把有number的过滤出来
        nodes_in_line = list(
            filter(
                lambda x: date_util.contain_number(x.content())
                or "年" in x.content()
                or "日" in x.content(),
                nodes_in_line,
            )
        )

        # crnn 识别区域为，y的范围参考有数字的部分的区域，x的范围为所有区域的xmin，xmax 的最值
        if len(nodes_in_line) == 0:
            return

        crnn_xmin = min([node.bbox.rect[0] for node in nodes_in_line])
        crnn_xmax = max([node.bbox.rect[2] for node in nodes_in_line])

        if len(nodes_in_line) == 1:
            nodes_in_line = nodes_in_line[0]
        else:
            # 选择合并后宽度最长，且有数字的那一个作为nodes_in_line来获得数字
            nodes_in_line = list(
                filter(lambda x: date_util.contain_number(x.content()), nodes_in_line)
            )
            nodes_in_line = max(nodes_in_line, key=lambda x: x.bbox.width)
        crnn_ymin = nodes_in_line.bbox.rect[1]
        crnn_ymax = nodes_in_line.bbox.rect[3]
        # 重识别的 rect 坐标要用原图坐标

        crnn_res, scores = self._crnn_util.run_number_space(
            img, [crnn_xmin, crnn_ymin, crnn_xmax, crnn_ymax]
        )

        crnn_res, scores = self.check_crnn_res_and_rerecognize(
            crnn_res, scores, img, crnn_xmin, crnn_ymin, crnn_xmax, crnn_ymax
        )

        date_info = [split for split in crnn_res.split("_") if split]
        useful_info = date_util.get_useful_info(crnn_res.replace("_", " "))
        if len(date_info) >= 3:
            # 如果node 能够形成完美的格式，即年份识别出四个字算1 ， 如果识别出两个字，算1/2
            split_res = date_util.parse_date(crnn_res, min_year=2000, max_year=2040)
            if split_res.most_possible_item:
                res = split_res.most_possible_item.to_string()
                logger.debug(f"{item_name} res {crnn_res} is formated to {res}")
            else:
                res = None

            crnn_scores = str_util.date_format_scores(*date_info[:3])  # 现在只对前三的内容做处理

        if len(date_info) < 3 or res is None:
            logger.debug(
                f"{item_name}  res {crnn_res} can not format , use normal method"
            )
            res = date_util.get_format_data_from_crnn_num_model_res(
                crnn_res.replace("_", "")
            )
            crnn_scores = str_util.date_format_scores(
                useful_info["useful_year"],
                useful_info["useful_month"],
                useful_info["useful_day"],
            )

        # 如果 crnn 的结果失败了，再使用原来的方法跑一边
        if res is None or not date_util.is_legal_format_date_str(res):
            nodes = NodeItemGroup.recover_node_item_dict(nodes_in_line.node_items)
            split_res = self._post_func_date(item_name, nodes, node_items, img)

            if split_res is not None:
                # recover year of split_res
                split_res_date = datetime.strptime(split_res[0], "%Y-%m-%d")
                if not date_util.is_legal_year(split_res_date.year):
                    predict_year = NodeItemGroup.get_year_predict(node_items)
                    predict_date = str(split_res_date.replace(year=predict_year).date())
                    split_res = (predict_date, split_res[1])
                recover_from_crnn = date_util.recover_info_from_useful_info(
                    split_res, useful_info
                )
                logger.debug(
                    "recover from crnn , org is {} , recover res is {}".format(
                        split_res, recover_from_crnn
                    )
                )
                split_res = recover_from_crnn
            else:
                if (
                    useful_info.get("useful_month", None) is not None
                    and useful_info.get("useful_day", None) is not None
                ):
                    # 尝试从所有的 node_items 中找到前三年的相关信息:
                    max_count_year = None
                    max_count = -1
                    cur_year = datetime.now().year
                    for year in range(cur_year - 3, cur_year + 1):
                        count_of_year = NodeItemGroup.regex_filter_count(
                            node_items, str(year)
                        )
                        if count_of_year > max_count:
                            max_count = count_of_year
                            max_count_year = year
                    if max_count != -1:
                        # find a year
                        predict_date = dt.date(
                            year=max_count_year,
                            month=int(useful_info["useful_month"]),
                            day=int(useful_info["useful_day"]),
                        )
                        predict_date = str(predict_date)
                        # 尝试从use_ful_info 中恢复部分数据
                        split_res = (predict_date, [1])
                        logger.debug(
                            "[{}] predict date from crnn , {}".format(
                                item_name, predict_date
                            )
                        )
            logger.debug(
                "[{}] Origin texts: {},"
                "CRNN result: {},"
                "Merge result: {},"
                "Split result: {}".format(
                    item_name, origin_text, crnn_res, res, split_res
                )
            )

            # name = item_name + str(self.global_test)
            # viz_crnn_debug(passed_nodes, nodes_in_line, img,name,origin_text)
            # self.global_test+=1

            return split_res

        # TODO: get_format_data_from_crnn_num_model_res 中需要返回到底用了哪几个位置的数字
        mean_score = NodeItemGroup.cal_mean_score(nodes_in_line)
        # return res, [mean_score]
        return res, crnn_scores

    def check_crnn_res_and_rerecognize(
        self, crnn_res, scores, img, crnn_xmin, crnn_ymin, crnn_xmax, crnn_ymax
    ):
        # 识别结果中，很容易出现如 _09_08 这种情况， 这种本质是因为重识别区域没有正确的找到信息，需要重新定位重识别区域

        def is_format_date(crnn_res):
            crnn_info_part = crnn_res.strip("_").split("_")
            crnn_info_part = [i for i in crnn_info_part if i]
            flag = (
                len(crnn_info_part) == 3
                and len(crnn_info_part[0]) == 4
                and len(crnn_info_part[1]) <= 2
                and len(crnn_info_part[2]) <= 2
            )
            return flag

        flag = is_format_date(crnn_res)
        if flag:
            return crnn_res, scores
        else:
            # 说明不够识别区域不够大导致识别效果不佳
            strategys = [(3, 1 / 5), (1.5, 2), (1.5, 1.5)]
            img_height, img_width = img.shape[:2]
            for strat_before, strat_after in strategys:

                width = crnn_xmax - crnn_xmin
                center = (crnn_xmax + crnn_xmin) / 2
                enlarge_x_min = max(0, int(center - width * strat_before / 2))
                enlarge_x_max = min(img_width, int(center + width * strat_after / 2))

                rerecog_res, rerecog_score = self._crnn_util.run_number_space(
                    img, [enlarge_x_min, crnn_ymin, enlarge_x_max, crnn_ymax]
                )
                if is_format_date(rerecog_res):
                    return rerecog_res, rerecog_score

            return crnn_res, scores

    def _post_func_date(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
    ):
        """
        根据日期字段分离的候选框组合出完整的日期
        """
        if type(passed_nodes) == list:
            passed_nodes = NodeItemGroup.recover_node_item_dict(passed_nodes)

        filter_of_node_item, _ = NodeItemGroup.remove_overlap(passed_nodes, 0.8)
        list_of_node_item = NodeItemGroup.sort_by_x(filter_of_node_item)

        nums = []
        for rect_data in list_of_node_item:
            # print rect_data.rect_center_xy, rect_data.content.encode('utf8')
            tmp = ""
            for c in rect_data.text:
                if "0" <= c <= "9":
                    tmp += c
                elif tmp:
                    nums.append(int(tmp))
                    tmp = ""
            if tmp:
                nums.append(int(tmp))
        res = None
        for yi in range(len(nums)):
            if res or nums[yi] < 2000 or nums[yi] > 2050:
                continue
            for mi in range(yi + 1, len(nums)):
                if res or nums[mi] < 1 or nums[mi] > 12:
                    continue
                for di in range(mi + 1, len(nums)):
                    if res or nums[di] < 1 or nums[di] > 31:
                        continue
                    res = "{}-{:02}-{:02}".format(nums[yi], nums[mi], nums[di])

        if res is None:
            return

        # TODO: 根据使用的候选框位置获得 scores
        # cal_mean_score
        mean_score = NodeItemGroup.cal_mean_score(passed_nodes)
        return res, [mean_score]
