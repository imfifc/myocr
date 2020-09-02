import copy
import re
import uuid
from collections import OrderedDict
from datetime import datetime
from enum import Enum, auto
from itertools import combinations
from typing import Dict, List, Tuple, Callable, Union, Optional

import cv2
import numpy as np

from ..template.tp_node_item import TpNodeItem
from ..utils import str_util
from ..utils.bbox import BBox
from ..utils.node_item import NodeItem


class Match(Enum):
    CONTAIN = auto()
    COMPLETE = auto()


def _bbox(node: NodeItem, default_value=None):
    """
    不同的 NodeItem 可能有不同的 bbox，这里写对应的规则
    :param node:
    :return:
    """
    return getattr(node, "trans_bbox", getattr(node, "bbox", default_value))


class NodeItemGroup:
    def __init__(
        self, node_item: NodeItem or List[NodeItem] or Dict[str, NodeItem] = None
    ):
        self.node_items = []
        self.avg_height = 0
        self.bbox: BBox = None
        self.uid = uuid.uuid1().hex

        if node_item is not None:
            if isinstance(node_item, list) or isinstance(node_item, tuple):
                for it in node_item:
                    self.append(it)
            elif isinstance(node_item, dict):
                for it in node_item.values():
                    self.append(it)
            else:
                self.append(node_item)

    def append(self, node_item: NodeItem):
        if len(self.node_items) == 0:
            self.bbox = copy.deepcopy(node_item.bbox)
        else:
            self.bbox.merge_(node_item.bbox)

        self.node_items.append(node_item)
        self.avg_height = self.cal_avg_height()

    def extend(self, other: 'NodeItemGroup'):
        """合并其他的group"""
        for node in other:
            self.append(node)

    def sort(self, key, reverse=False):
        self.node_items.sort(key=key, reverse=reverse)

    def gen_raw_node(self, text_join_char="") -> List:
        # TODO handle ltrb
        text = []
        scores = []
        for it in self.node_items:
            text.append(it.text)
            scores.extend(it.scores)

        text = text_join_char.join(text)

        return [text, *self.bbox, -1, *scores]

    @property
    def raw_node(self):
        # 不要修改这个函数名！
        text = []
        scores = []
        points = []
        for it in self.node_items:
            text.append(it.text)
            scores.extend(it.scores)
            points.extend([
                (int(it.rbox.x1), int(it.rbox.y1)),
                (int(it.rbox.x2), int(it.rbox.y2)),
                (int(it.rbox.x3), int(it.rbox.y3)),
                (int(it.rbox.x4), int(it.rbox.y4)),
            ])
        quad = cv2.minAreaRect(np.array(points).astype(np.int))
        pnts = cv2.boxPoints(quad)
        return ["_".join(text), *pnts.flatten().astype(np.int).tolist(), quad[-1], 0, *scores]

    def cal_avg_height(self):
        return sum([it.bbox.height for it in self.node_items]) / len(self.node_items)

    def content(self, join_char=""):
        return join_char.join([it.text for it in self.node_items])

    def cn_text(self, join_char=""):
        return join_char.join([it.cn_text for it in self.node_items])

    def scores(self):
        out = []
        for it in self.node_items:
            out.extend(it.scores)
        return out

    def find_x_segs(self, x_thresh=1) -> List["NodeItemGroup"]:
        """
        根据 x 方向的阈值找到水平方向上的段落
        :param x_thresh: 默认使用平均高度作为 thresh
        :return:
        """
        if not self.node_items:
            return []

        sum_h = 0.0
        for it in self.node_items:
            sum_h += it.bbox.height
        x_thresh = (sum_h / len(self.node_items)) * x_thresh

        self.node_items.sort(key=lambda x: x.bbox.cx)

        groups = []
        for it in self.node_items:
            if len(groups) == 0:
                groups.append(NodeItemGroup(it))
            else:
                x_dis = it.bbox.left - groups[-1].bbox.right

                if x_dis < x_thresh:
                    # 比较近，认为是一个 seg
                    groups[-1].append(it)
                else:
                    groups.append(NodeItemGroup(it))
        return groups

    @staticmethod
    def clear_ignore(
        node_items: Dict[str, "NodeItem"],
        ignore_texts: List[str],
        flag=Match.CONTAIN,
        remove_symbols=True,
        remove_space=True,
        clear_same_line=False,
        clear_same_line_thresh=0.15,
        clear_same_line_x_intersect=False,
    ) -> List[str]:
        """
        根据 ignore_texts 和匹配的策略清空某些 node_item
        :param node_items:
        :param ignore_texts:
        :param flag: 匹配策略 CONTAIN: 只要包含了 ignore_texts 中的字符串就清空； COMPLETE：与 ignore_texts 中的字符串完全匹配时清空
        :param remove_symbols: 匹配时是否移除空格再匹配
        :param remove_space: 匹配时是否移除符号再匹配
        :param clear_same_line: 是否清空与被清空元素共行的 node_item
        :param clear_same_line_thresh: 判断共行的阈值，平均高度的百分比
        :param clear_same_line_x_intersect: 是否仅在 x 方向相交时才清空共行
        :return: 被清空元素的 uid
        """
        if len(ignore_texts) == 0:
            return []

        ignore_uids = NodeItemGroup.find_uids(
            node_items, ignore_texts, flag, remove_symbols, remove_space
        )

        if clear_same_line:
            ignore_same_uids = []
            for uid in ignore_uids:
                ignore_node = node_items[uid]
                for node in node_items.values():
                    if uid == node.uid:
                        continue

                    if not node.text:
                        continue

                    same_line = False

                    if _bbox(node).is_same_line(
                        _bbox(ignore_node), thresh=clear_same_line_thresh
                    ):
                        same_line = True

                    if clear_same_line_x_intersect:
                        if not _bbox(node).is_x_overlap(_bbox(node)):
                            same_line = False

                    if same_line:
                        ignore_same_uids.append(node.uid)
                        node.clear()

            ignore_uids.extend(ignore_same_uids)

        for uid in ignore_uids:
            node_items[uid].clear()

        return ignore_uids

    @staticmethod
    def clear_above(
        node_items: Dict[str, NodeItem],
        anchor_text: str,
        flag=Match.CONTAIN,
        y_thresh=1,
    ) -> List[str]:
        """
        清除中心点位于 anchor_text 上方，且 x 方向上偏差不超过 mean_width/2 的 nodes 内容

        当且仅当只找到一个锚点时才会进行操作
        :param node_items:
        :param anchor_text:
        :param flag:
        :param y_thresh: 阈值越大，is_above 判断的越严格
        :return:
        """
        nodes = NodeItemGroup.find_nodes(node_items, [anchor_text], flag)
        if len(nodes) != 1:
            return []

        anchor = nodes[0]
        width_thresh = _bbox(anchor).width / 2
        cleared_uids = []
        for node in node_items.values():
            if not node.text:
                continue

            is_above = _bbox(node).is_above(_bbox(anchor), thresh=y_thresh)
            is_x_close = abs(_bbox(node).cx - _bbox(anchor).cx) < width_thresh

            if is_above and is_x_close:
                node.clear()
                cleared_uids.append(node.uid)

        return cleared_uids

    @staticmethod
    def find_uids(
        node_items: Dict[str, NodeItem],
        texts: List[str],
        flag=Match.CONTAIN,
        remove_symbols=True,
        remove_space=True,
    ) -> List[str]:
        """
        根据 texts 找 uid
        :param node_items:
        :param texts:
        :param flag:
        :param remove_symbols:
        :param remove_space:
        :return:
        """

        def clear(_text):
            if remove_symbols:
                _text = str_util.remove_symbols(_text)
            if remove_space:
                _text = str_util.remove_space(_text)
            return _text

        texts = list(filter(clear, texts))

        uids = []
        for uid, node in node_items.items():
            for text in texts:
                match = False
                node_text = clear(node.text)

                if flag == Match.CONTAIN:
                    if text in node_text:
                        match = True
                elif flag == Match.COMPLETE:
                    if text == node_text:
                        match = True

                if match:
                    uids.append(uid)
                    break
        return uids

    @staticmethod
    def find_nodes(
        node_items: Dict[str, NodeItem],
        texts: List[str],
        flag=Match.CONTAIN,
        remove_symbols=True,
        remove_space=True,
    ) -> List[NodeItem]:
        uids = NodeItemGroup.find_uids(
            node_items, texts, flag, remove_symbols, remove_space
        )
        return [node_items[uid] for uid in uids]

    @staticmethod
    def find_row_lines(
        node_items: Dict[str, NodeItem] or List[NodeItem], y_thresh=0.15
    ) -> List["NodeItemGroup"]:
        """
        1. 对 node_items 从上到下排序
        2. 找到共行节点
        3. 对每一行的节点从左到右排序

        :param node_items:
        :param y_thresh: 默认使用平均高度的 0.15 作为 thresh
        :return:
        """
        if len(node_items) == 0:
            return []

        if isinstance(node_items, list):
            node_items = {it.uid: it for it in node_items}

        sum_h = 0.0
        for it in node_items.values():
            sum_h += _bbox(it).height
        y_thresh = (sum_h / len(node_items)) * y_thresh

        node_items = sorted(node_items.items(), key=lambda x: _bbox(x[1]).cy)

        line_groups = []
        for uid, it in node_items:
            if len(line_groups) == 0:
                line_groups.append(NodeItemGroup(it))
                continue

            appended = False
            for group in line_groups:
                if len(group) != 0:
                    # 一行当中最后一个节点的 cy 坐标
                    cy = _bbox(group[-1]).cy
                    now_cy = _bbox(it).cy
                    diff = abs(now_cy - cy)
                    if diff < y_thresh:
                        group.append(it)
                        appended = True
                        break

            if not appended:
                line_groups.append(NodeItemGroup(it))

        for it in line_groups:
            it.sort(lambda x: _bbox(x).cx)

        return line_groups

    @staticmethod
    def find_col_lines(
        node_items: Dict[str, NodeItem] or List[NodeItem], x_thresh=1
    ) -> List["NodeItemGroup"]:
        """
        1. 对 node_items 从左到右排序
        2. 找到共列节点
        3. 对每一列的节点从上到下排序

        :param node_items:
        :param x_thresh: 默认使用平均高度的 1 作为 thresh
        :return:
        """
        if len(node_items) == 0:
            return []

        if isinstance(node_items, list):
            node_items = {it.uid: it for it in node_items}

        sum_h = 0.0
        for it in node_items.values():
            sum_h += _bbox(it).height
        x_thresh = (sum_h / len(node_items)) * x_thresh

        node_items = sorted(node_items.items(), key=lambda x: _bbox(x[1]).cx)

        line_groups = []
        for uid, it in node_items:
            if len(line_groups) == 0:
                line_groups.append(NodeItemGroup(it))
                continue

            appended = False
            for group in line_groups:
                if len(group) != 0:
                    # 一行当中最后一个节点的 cx 坐标
                    cx = _bbox(group[-1]).cx
                    now_cx = _bbox(it).cx
                    diff = abs(now_cx - cx)
                    if diff < x_thresh:
                        group.append(it)
                        appended = True
                        break

            if not appended:
                line_groups.append(NodeItemGroup(it))

        for it in line_groups:
            it.sort(lambda x: _bbox(x).cy)

        return line_groups

    @staticmethod
    def recover_node_item_dict(node_items_list: List[NodeItem]) -> Dict[str, NodeItem]:
        node_items_uid = [node.uid for node in node_items_list]
        return OrderedDict(zip(node_items_uid, node_items_list))

    @staticmethod
    def clear_overlap(node_items: Dict[str, NodeItem], ioo_thresh=0.9) -> List[str]:
        """
        计算 ioo，清空 ioo 重叠较大的检测框
        :param node_items:
        :param ioo_thresh:
        :return:
        """
        remove_uids = NodeItemGroup.find_overlap(node_items, ioo_thresh)
        for uid in remove_uids:
            node_items[uid].clear()
        return remove_uids

    @staticmethod
    def find_overlap(node_items: Dict[str, NodeItem], ioo_thresh=0.9) -> List[str]:
        """
        计算 ioo，找到 ioo 重叠较大的
        :param node_items:
        :param ioo_thresh:
        :return:
        """
        remove = {uid: False for uid in node_items.keys()}

        for node1 in node_items.values():
            area1 = _bbox(node1).area
            for node2 in node_items.values():
                if node1.uid == node2.uid or remove[node2.uid]:
                    continue

                area2 = _bbox(node2).area
                ioo = _bbox(node1).cal_ioo(_bbox(node2))
                if area1 < area2 and ioo >= ioo_thresh:
                    remove[node1.uid] = True
                    break

        remove_uids = [uid for uid, v in remove.items() if v]
        return remove_uids

    @staticmethod
    def remove_overlap(
        node_items: Dict[str, NodeItem], ioo_thresh=0.9
    ) -> Tuple[Dict[str, NodeItem], List[str]]:
        """
        移除 node_items 中与其他框 ioo 重叠较大的，返回一个新的数据
        :param node_items:
        :param ioo_thresh:
        :return:
        """
        remove_uids = NodeItemGroup.find_overlap(node_items, ioo_thresh)

        out = {}
        for node in node_items.values():
            if node.uid not in remove_uids:
                out[node.uid] = node

        return out, remove_uids

    @staticmethod
    def max_area_node(
        node_items: Union[Dict[str, NodeItem], List[NodeItem]]
    ) -> Optional[NodeItem]:
        if isinstance(node_items, Dict):
            node_items = list(node_items.values())
        if len(node_items) == 0:
            return None
        return max(node_items, key=lambda x: x.bbox.area)

    @staticmethod
    def regex_filter_count(node_items: Dict[str, NodeItem], regex):
        count = 0
        for node in node_items.values():
            res = re.search(regex, node.text)
            if res is not None:
                count += 1
        return count

    @staticmethod
    def filter_large_space_with_less_char(node_items: Dict[str, TpNodeItem], char_mean):
        filter_nodes = []
        for node in node_items.values():
            if node.text == "":
                continue
            char_len = (node.trans_bbox.rect[2] - node.trans_bbox.rect[0]) / len(
                node.text
            )
            if char_len > char_mean:
                continue
            else:
                filter_nodes.append(node)
        passed_nodes = NodeItemGroup.recover_node_item_dict(filter_nodes)
        return passed_nodes

    @staticmethod
    def get_year_predict(node_items: Dict[str, NodeItem]):
        max_count_year = None
        max_count = -1
        cur_year = datetime.now().year
        for year in range(cur_year - 3, cur_year + 1):
            count_of_year = NodeItemGroup.regex_filter_count(node_items, str(year))
            if count_of_year > max_count:
                max_count = count_of_year
                max_count_year = year
        return max_count_year

    @staticmethod
    def cal_mean_score(node_items: Dict[str, NodeItem]) -> float:
        """
        求出所有 node_item 分数的均值
        """
        if node_items is None:
            return 0

        scores = []
        if type(node_items) == dict or type(node_items) == OrderedDict:
            node_items = node_items.values()
        for node in node_items:
            scores.extend(node.scores)

        if len(scores) == 0:
            return 0

        return sum(scores) / len(scores)

    @staticmethod
    def sort_by_y(node_items: Dict[str, NodeItem], reverse=False) -> List[NodeItem]:
        return sorted(node_items.values(), key=lambda x: _bbox(x).cy, reverse=reverse)

    @staticmethod
    def sort_by_x(node_items: Dict[str, NodeItem], reverse=False) -> List[NodeItem]:
        return sorted(node_items.values(), key=lambda x: _bbox(x).cx, reverse=reverse)

    @staticmethod
    def get_possible_node(
        node_items: Dict[str, NodeItem],
        config,
        thresh_x=2,
        thresh_y=2,
        match_count=3,
        return_node=False,
    ):
        """
        1. 本段代码的作用：
            在区域过滤后，如果一张图片的前景偏移出现问题，极有可能出现某些fg 在完成区域过滤后就已经找不到相关的节点了
            此时，所有的后处理部分都跳过了
            因此，此段代码的目的是，根据一定的删选规则，对 node_item 重新进行一轮筛选，对认为可以使用的node，将其 is_filter_by_area 设置为false

        2. 使用方法如下：
           定义一个 config， config 定义 对指定的前景字段，其上下左右的字段需要满足的正则表达式
           thres 会定义一个寻找区域，thres 越大，寻找范围越大
        def _post_area_filter_func(self, item_name, node_items):
            config = {'left': ['交易流水号', '交易.水号', '实时结算', '流水号', '.{1,3}流.号'],
                      'right': ['医保实时结算', '医疗机构类型'],
                      'up': None,
                      'down': ['[0-9,A-Z,a-z]{17,}', '性别', '男|女']
                      }
            NodeItemGroup.get_possible_node(node_items, config,thres_x = 2)

        3. 具体实现方法为：
        遍历每一个possible_node:
            遍历每一个方向：
                遍历其他的other_node，如果这个node在 possible_node的对应的方向：
                    如果other_node满足在这一方向的正则表达式，记录

        如果找打这样的possible_node,node能够在各个方向都找到匹配正则表达式的节点
        则认为这个node是一个可能的node，使得 filter_by_area = False

        """

        def _search_node_for_direction(
            possible_node: Dict[str, NodeItem], node_items: NodeItem, config, direct
        ):
            # thres 对应搜索的范围
            nonlocal thresh_x, thresh_y
            matched_text = []
            for surround_node in node_items.values():
                if surround_node.uid != possible_node.uid:
                    if (
                        getattr(possible_node, "bg_scaled_bbox", None) is not None
                        and getattr(surround_node, "bg_scaled_bbox", None) is not None
                    ):
                        relation = possible_node.bg_scaled_bbox.relation_to_other(
                            surround_node.bg_scaled_bbox, thresh_x, thresh_y
                        )
                    elif getattr(possible_node, "trans_bbox", None) is not None:
                        relation = possible_node.trans_bbox.relation_to_other(
                            surround_node.trans_bbox,
                            thresh_x=thresh_x,
                            thresh_y=thresh_y,
                        )
                    else:
                        # 对于非模板方法，不具有 trans_bbox
                        relation = possible_node.bbox.relation_to_other(
                            surround_node.bbox, thresh_x=thresh_x, thresh_y=thresh_y
                        )

                    match = relation[direct]
                    if not match:
                        continue
                    is_matched_node = False
                    # 找打的节点是在这个possible_node的左边的，尝试下规则匹配
                    for rule in config[direct]:
                        if re.search(rule, surround_node.text):
                            is_matched_node = True
                            break

                    if is_matched_node:
                        matched_text.append(surround_node.text)
            if matched_text:
                return matched_text[0]
            else:
                return None

        log_info = []
        for possible_node in node_items.values():
            # 对每一个可能的节点
            consider_direction = 0
            succeed_match_count = 0
            search_res_list = []
            for direct in config:
                if not config[direct]:
                    continue
                consider_direction += 1
                search_res = _search_node_for_direction(
                    possible_node, node_items, config, direct
                )
                if search_res:
                    succeed_match_count += 1
                    search_res_list.append({direct: search_res})
            if succeed_match_count >= match_count:
                possible_node.is_filtered_by_area = False
                possible_node.is_filtered_by_regex = False
                possible_node.is_filtered_by_content = False
                if return_node:
                    log_info.append((possible_node, search_res_list))
                else:
                    log_info.append((possible_node.text, search_res_list))

        return log_info

    @staticmethod
    def post_regexes_func_finder(node_items, rule, thresh=0.5, return_nodes=False):
        """

        :param node_items: 所有的节点
        :param rule:  一些列的正则表达式，用于找到背景字
        :return:
        """

        target_node = None
        for node in node_items.values():
            for rl in rule:
                if re.search(rl, node.text):
                    target_node = node
                    break
        if target_node:
            if str_util.only_keep_money_char(target_node.text) != "":
                target_node.is_filtered_by_regex = False
                target_node.is_filtered_by_area = False
                target_node.is_filtered_by_content = False

            node_text = str_util.keep_amountinwords_char(target_node.text)
            # 找到所有其他的，在他的右侧的节点
            node_returned = []
            for node in node_items.values():
                if node.uid == target_node.uid:
                    continue
                if (
                    node.bbox.is_same_line(target_node.bbox, thresh=thresh)
                    and node.bbox.cx > target_node.bbox.cx
                ):
                    node.is_filtered_by_regex = False
                    node.is_filtered_by_area = False
                    node.is_filtered_by_content = False
                    node_returned.append(node)
            if return_nodes:
                return node_returned

    @staticmethod
    def find_node_in_region(
        anchor_box: BBox, node_items, xoffset=(-1, 3), yoffset=(-2, 4), filter_rule=None
    ) -> List[NodeItem]:
        """
        寻找中心在 anchor box 上下左右一个范围内的 node_items
        :param anchor_box:
        :param node_items:
        :param xoffset:
        :param yoffset:
        :return:
        """
        left_top_box = anchor_box.get_offset_box(xoffset[0], yoffset[0])
        right_bot_box = anchor_box.get_offset_box(xoffset[1], yoffset[1])
        xmin, ymin = left_top_box.cx, left_top_box.cy
        xmax, ymax = right_bot_box.cx, right_bot_box.cy
        nodes_in_region = []

        if isinstance(node_items, dict):
            _iter = node_items.values()
        else:
            _iter = node_items

        for node in _iter:
            if node.bbox.is_center_in([xmin, ymin, xmax, ymax]):
                if filter_rule:
                    if filter_rule(node.text):
                        nodes_in_region.append(node)
                    else:
                        continue
                else:
                    nodes_in_region.append(node)
        return nodes_in_region

    @staticmethod
    def find_min_dis_node(
        target_rect, node_items, dis_func: Callable = None
    ) -> NodeItem:
        """
        在 node_items 中找到和 target_rect 距离最近的 node，默认使用中心点的距离
        """
        if isinstance(node_items, dict):
            _iter = node_items.values()
        else:
            _iter = node_items

        min_dis = float("inf")
        result = None
        for it in _iter:
            if dis_func is not None:
                dis = dis_func(it.bbox, target_rect)
            else:
                dis = it.bbox.center_dis(target_rect)

            if dis < min_dis:
                min_dis = dis
                result = it
        return result

    def get_min_bbox(self) -> BBox:
        min_left, min_top, max_right, max_bottom = None, None, None, None
        for ni in self.node_items:
            left, top, right, bottom = ni.bbox
            if min_left is None or left < min_left:
                min_left = left
            if min_top is None or top < min_top:
                min_top = top
            if max_right is None or right > max_right:
                max_right = right
            if max_bottom is None or bottom > max_bottom:
                max_bottom = bottom
        return BBox([min_left, min_top, max_right, max_bottom])


    @staticmethod
    def is_same_line(node_items, thresh=0.15)->bool:
        if len(node_items) == 1:
            return True

        if isinstance(node_items, dict):
            _iter = node_items.values()
        else:
            _iter = node_items

        for comb in combinations(_iter,2):
            if not comb[0].bbox.is_same_line(comb[1].bbox, thresh=thresh):
                return False
        return True

    @staticmethod
    def boundary(node_items: Union[Dict[str, NodeItem], List[NodeItem]]) -> BBox:
        if isinstance(node_items, dict):
            _iter = node_items.values()
        else:
            _iter = node_items

        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = 0, 0

        for it in _iter:
            if it.bbox.left < min_x:
                min_x = it.bbox.left

            if it.bbox.right > max_x:
                max_x = it.bbox.right

            if it.bbox.top < min_y:
                min_y = it.bbox.top

            if it.bbox.bottom > max_y:
                max_y = it.bbox.bottom

        return BBox([min_x, min_y, max_x, max_y])

    def __getitem__(self, item):
        return self.node_items[item]

    def __len__(self):
        return len(self.node_items)

    def __str__(self):
        return "%s [%d %d %d %d]" % (
            self.content(),
            self.bbox.left,
            self.bbox.top,
            self.bbox.right,
            self.bbox.bottom,
        )
