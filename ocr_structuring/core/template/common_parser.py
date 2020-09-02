import re
from typing import Dict

from numpy import ndarray

from . import parser_util
from . import post_funcs
from .parser_base import ParseBase
from .tp_node_item import TpNodeItem
from ..utils import str_util
from ..utils.amount_in_words import cn_amount_util
from ocr_structuring.utils.logging import logger
from ..utils.guess_gender import guess_gender
from ..utils.rules import person_name


# noinspection PyMethodMayBeStatic
class CommonParser(ParseBase):
    def __init__(self, class_name: str, conf: Dict):
        """
        :param conf:
        """
        super().__init__(class_name, conf)

    def tmpl_post_proc(self, structure_items, fg_items, img):
        """
        :param structure_items: dict. key: item_name value: StructureItem
        :return: 与 structure_items 的类型相同，可能会添加新的 item，或者修改原有 item 的值
        """
        return structure_items

    def _post_func_return_1_if_non_empty(self,
                                         item_name: str,
                                         passed_nodes: Dict[str, TpNodeItem],
                                         node_items: Dict[str, TpNodeItem],
                                         img: ndarray):
        """
        如果 rect_data_list 不为空则返回 1，否则返回 0
        """
        if passed_nodes:
            return 1, [1]
        else:
            return 0, [0]

    def _post_func_max_w_regex(self,
                               item_name: str,
                               passed_nodes: Dict[str, TpNodeItem],
                               node_items: Dict[str, TpNodeItem],
                               img: ndarray):
        return post_funcs.max_w_regex(item_name, passed_nodes, node_items, img)

    def _post_func_select_above(self,
                                item_name: str,
                                passed_nodes: Dict[str, TpNodeItem],
                                node_items: Dict[str, TpNodeItem],
                                img: ndarray):
        """
        选取 passed_nodes 中 y 值最小的，并返回正则表达式中优先级最高的匹配结果
        """
        passed_nodes = sorted(passed_nodes.values(), key=lambda x: x.bbox.cy)
        r = passed_nodes[0].get_max_match_regex_w_str()
        return r.text, r.scores

    def _post_func_select_down(self,
                               item_name: str,
                               passed_nodes: Dict[str, TpNodeItem],
                               node_items: Dict[str, TpNodeItem],
                               img: ndarray):
        """
        选取 passed_nodes 中 y 值最大的，并返回正则表达式中优先级最高的匹配结果
        """
        passed_nodes = sorted(passed_nodes.values(), key=lambda x: x.bbox.cy, reverse=True)
        r = passed_nodes[0].get_max_match_regex_w_str()
        return r.text, r.scores

    def _post_func_select_max_regex_above(self,
                                          item_name: str,
                                          passed_nodes: Dict[str, TpNodeItem],
                                          node_items: Dict[str, TpNodeItem],
                                          img: ndarray):
        """
        从 tp_rects 中正则权重最高的结果中，再从结果中算一个 y 值最小的
        """
        text, scores = parser_util.get_regex_max_w(passed_nodes, 'above')
        return text, scores

    def _post_func_select_max_regex_down(self,
                                         item_name: str,
                                         passed_nodes: Dict[str, TpNodeItem],
                                         node_items: Dict[str, TpNodeItem],
                                         img: ndarray):
        """
        从 tp_rects 中正则权重最高的结果中，再从结果中算一个 y 值最大的
        """
        text, scores = parser_util.get_regex_max_w(passed_nodes, 'down')
        return text, scores

    def _post_func_amount_in_words(self,
                                   item_name: str,
                                   passed_nodes: Dict[str, TpNodeItem],
                                   node_items: Dict[str, TpNodeItem],
                                   img: ndarray):
        """
        把中文大写金额转换成数字字符串
        """
        for node in passed_nodes.values():
            num = cn_amount_util.word2num(node.text)
            if num is not None:
                return num, node.get_scores()

    def _pre_func_person_name(self,
                              item_name: str,
                              passed_nodes: Dict[str, TpNodeItem],
                              node_items: Dict[str, TpNodeItem],
                              img: ndarray):
        # 姓名的检测框往往会和姓名两个字在一起，进行一些过滤
        replace_map = [
            '社名', '姓名', '姓.{0,2}名', '项目', '规格', '业务流水号', '性别', '金额', '单价'
        ]
        for node in passed_nodes.values():
            for rl in replace_map:
                if re.search(rl, node.text):
                    node.text = re.sub(rl, '', node.text)
                    node.text = node.cn_text

    def _post_func_person_name(self,
                               item_name: str,
                               passed_nodes: Dict[str, TpNodeItem],
                               node_items: Dict[str, TpNodeItem],
                               img: ndarray):
        """
        该函数会过滤掉置信度较低的人名结果，返回第一个满足人名置信度的结果
        """
        nodes = sorted(passed_nodes.values(), key=lambda x: x.get_final_w())

        thresh = 0.9
        for node in nodes:
            r = node.get_max_match_regex_w_str()
            # 重要：提高 name 的 keep_acc
            if person_name.get_person_name_confidence(r.text) < thresh:
                continue
            return r.text, node.get_scores()

    def _tmpl_post_guess_gender_from_name(self, structure_items):
        gender_item = structure_items.get('sex', None)
        name_item = structure_items.get('name', None)
        if gender_item is None or name_item is None:
            return

        if gender_item.content or not name_item.content:
            return

        gender, score = guess_gender(name_item.content)
        if score != 0:
            gender_item.content = gender
            gender_item.scores = name_item.scores[1:]

    def _pre_func_money(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray):

        # 首先，对一下三种数据进行处理：
        # 第一种，有一个逗号，一个小数点：
        for node in passed_nodes.values():
            text = node.text
            split_res = re.split(',|\.|_', text)
            split_res = [num for num in split_res if num]
            if len(split_res) == 3:
                new_text = split_res[0] + split_res[1] + '.' + split_res[2]
                node.text = new_text
            if len(split_res) == 2:
                new_text = split_res[0] + '.' + split_res[1]
                node.text = new_text

        replace_map = {'O': '0', '_': '', 'Q': '0', 'D': '0', '@': '0', 'B': '8', 'L': '1',
                       '~': '', ',': '.', ']': '1', '[': '1', '-': '', 'S': '5', ':': '', 'l': '1', 'G': '6', '￥': ''
                       }

        for data in passed_nodes.values():
            text = data.text
            for key in replace_map:
                if key in text:
                    text = text.replace(key, replace_map[key])
            if not text:
                continue
            if text[0] == 'Y':
                text = text[1:]
            else:
                text = text.replace('Y', '7')
            text = str_util.only_keep_money_char(text)
            text = str_util.remove_last_dot(text)
            text = str_util.remove_extra_dot(text)
            only_zero = str_util.contain_only_special(text, '0')
            if only_zero:
                data.text = '0.00'
            else:
                data.text = text

    def _pre_func_remove_space(self,
                               item_name: str,
                               passed_nodes: Dict[str, TpNodeItem],
                               node_items: Dict[str, TpNodeItem],
                               img: ndarray):
        """
        移除所有的空格，有的识别模型是使用下划线代替空格，remove_space 中会处理
        """
        for node in passed_nodes.values():
            node.text = str_util.remove_space(node.text)

    def _post_regex_filter_amountinwords(self,
                                         item_name: str,
                                         node_items: Dict[str, TpNodeItem],
                                         img: ndarray
                                         ):
        for node in node_items.values():
            if re.search('[零壹贰叁肆伍陆柒捌玖拾佰仟万亿圆元角分整]+', node.text):
                logger.debug('recover amount in words {} ...'.format(node.text))
                node.is_filtered_by_content = False
                node.is_filtered_by_area = False
                node.is_filtered_by_regex = False
