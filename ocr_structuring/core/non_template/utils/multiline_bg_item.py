from enum import Enum, auto
from itertools import product
from typing import Dict, List

import numpy as np

from ocr_structuring.core.non_template.utils.bg_item import BgItem
from ocr_structuring.core.non_template.utils.bol_utils.utils.time_counter import record_time
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.core.utils.node_item_group import NodeItemGroup


class MultiHeaderAlign(Enum):
    """
    如果一个表头有多行，多行的对齐方式
    """
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()
    NONE = auto  # 如果不需要配置多行表头，该参数设置为None


class RowBGItem(NodeItemGroup):
    def content(self, join_char='_'):
        # 修改默认的连接方法
        return super(RowBGItem, self).content(join_char)


class MultiRowItem():
    # 用于存储多行的信息
    def __init__(self, rows: List[RowBGItem]):
        assert len(rows) > 0, 'row can not be empty'
        self.rows = list(rows)
        self.update_bbox()

    def update_bbox(self):
        bbox = []
        for row in self.rows:
            bbox.append(row.bbox.rect)
        bbox = np.array(bbox)
        xmin = bbox[:, 0].min()
        ymin = bbox[:, 1].min()
        xmax = bbox[:, 2].max()
        ymax = bbox[:, 3].max()
        bbox = BBox([xmin, ymin, xmax, ymax])
        self.bbox = bbox

    @property
    def node_items(self):
        nodes = []
        for row in self.rows:
            nodes.extend(row.node_items)
        return nodes

    @property
    def avg_height(self):
        return np.mean([row.avg_height for row in self.rows])

    @property
    def cut_nodes_count(self):
        # 反应组成MultiRowItem 的，有多少是 被裁剪出来的
        count = 0
        for row in self.rows:
            count += sum([getattr(node, 'is_cuted_node', False) for node in row.node_items])
        return count

    @property
    def cut_nodes_set(self):
        cut_nodes = set()
        for row in self.rows:
            for node in row.node_items:
                if node.is_cuted_node:
                    cut_nodes.add(node.uid)
        return cut_nodes

    @property
    def count_nodes(self):
        count = 0
        for row in self.rows:
            count += len(row.node_items)
        return count

    @property
    def content(self):
        return '_'.join([row.content() for row in self.rows])

    def is_valid_multi_row_item(self, align_method: MultiHeaderAlign):
        if len(self.rows) == 0:
            return False
        if len(self.rows) == 1:
            return True
        # 首先按照rows 在y 方向进行排序
        sorted_node = sorted(self.rows, key=lambda x: x.bbox.top)

        is_valid = True
        for i in range(1, len(sorted_node)):
            uppper_node = sorted_node[i - 1]
            lower_node = sorted_node[i]

            if not uppper_node.bbox.is_close_up(lower_node.bbox):
                is_valid = False

            align_score = min(
                abs(uppper_node.bbox.cx - lower_node.bbox.cx),
                abs(uppper_node.bbox.left - lower_node.bbox.left),
                abs(uppper_node.bbox.right - lower_node.bbox.right)
            )
            if align_score / max(min(uppper_node.bbox.width, lower_node.bbox.width),1) > 0.8:
                # 两者的中心位置差太多
                is_valid = False

        return is_valid

    def merge_(self, other_row):
        self.rows.extend(other_row.rows)
        self.update_bbox()


class MultiLineBGItem:
    """
    在某些表单数据当中，可能会出现，表头是由多行，多个字符组成的
    比如：
    ------------------------
    QTY| QTY | DESCRIPTION  |
    ORD| SHIP| ItemInfo| S/N|
    ------------------------
    对此，在匹配 key_node 的时候，就需要使用这个类别

    输入的config 类似于 ：
    config = [
        # 第一层的list 代表行数,如果header 的文字有两行，就设置为两行
        [
            # 第二层为这一行内的每个内容,一行内有多个内容，就配置多个元素
            [('DESCRIPTION',1),('Description',1)]
        ],
        [
            [('ItemInfo',1),('ITEMINFO',1) ],
            [('S/N',1)]
        ]
    ]
    clean_text_func: 输入到BgItem当中，用于清理数据
    align_method : 对于找到的内容，要求的对齐方式
    clean_bg_text: 设置为True 时，对背景字采用和node item 一致的处理方法(clean_text_func)
    """

    def __init__(self, config, clean_text_func, align_method, clean_bg_text=True,
                 merge_mode=BgItem.MATCH_MODE_HORIZONTAL_MERGE):
        assert merge_mode in [BgItem.MATCH_MODE_HORIZONTAL_MERGE, BgItem.MATCH_MODE_HORIZONTAL_SPLIT,
                              BgItem.MATCH_MODE_COMMON]
        self.bg_items, self.bg_nums = self.build_bg_items(config, clean_text_func, clean_bg_text, merge_mode)
        self.align_method = align_method

    def build_bg_items(self, config, clean_text_func, clean_bg_text, merge_mode):
        """
        :return:
            bg_items ： 对每个位置进行匹配的一系列的BGItems
            bg_nums: 用于记录每行上应该有多少个背景字
        """
        bg_items = []
        bg_nums = []
        assert len(config) > 0, 'multi line config must not be empty'
        for row in config:
            row_bg_item = []
            special_loc_count = 0  # 统计这一行上有多少的东西
            for special_loc in row:
                assert len(special_loc) > 0, 'each line must contain an bg text'
                special_loc_count += 1

                special_loc_items = []
                for bg_text in special_loc:
                    if isinstance(bg_text, tuple):
                        ed_thresh = bg_text[1]
                        bg_text = bg_text[0]
                    else:
                        ed_thresh = -1
                    max_interval = 1 if len(bg_text) <= 3 else 2
                    bg_text = clean_text_func(bg_text) if clean_bg_text else bg_text
                    special_loc_items.append(
                        BgItem(bg_text, merge_mode, ed_thresh,
                               h_split_pre_func=clean_text_func,
                               h_split_max_interval=max_interval
                               )
                    )
                row_bg_item.append(
                    special_loc_items
                )
            bg_nums.append(special_loc_count)
            bg_items.append(row_bg_item)
        return bg_items, bg_nums

    def match(self, node_items: Dict[str, NodeItem]) -> List[MultiRowItem]:
        # match 方法，如果有存在一组或者多组能够符合条件的node ，按照config 设计的结构返回这些node
        # 首先，对每一个调用 match 方法
        finded_possible_nodes, prob_node_list = self.find_node_for_each_bg(node_items)
        if finded_possible_nodes:
            matched_nodes_group = self.get_valid_groups(prob_node_list, node_items)
            if len(matched_nodes_group) > 0:
                return matched_nodes_group
            return []
        return []

    def get_valid_groups(self, prob_node_list, node_items):
        # 首先，检查是否每个位置都匹配上了内容
        if not self.check_bg_all_finded(prob_node_list):
            return []
        # 现在，在这个表头的每个位置上都有找到可能的node_items
        # 需要将他们一组一组的弄出来
        valid_row_group = []
        for row in prob_node_list:
            row_group = self.find_valid_row_group(row, node_items)
            if row_group == []:
                # 说明这一行无法找到合理的内容
                return []
            valid_row_group.append(row_group)
        # 接下来，找到可能的node 组合
        valid_multi_line_group = self.find_multi_line_group(valid_row_group)
        return valid_multi_line_group

    def find_multi_line_group(self, valid_row_group):
        """

        :param valid_row_group: 输入的元素，每个元素为一行上， 所有可能的组合
        :return:
        """
        if len(valid_row_group) == 1:
            # 说明只有一行，
            first_row = valid_row_group[0]
            # first_row 是一个List ，对应着所有可能的RowItem
            return [MultiRowItem([possible_row]) for possible_row in first_row]

        valid_multi_line_group = []
        for comb in product(*valid_row_group):
            prob_Multiline_group = MultiRowItem(comb)
            if prob_Multiline_group.is_valid_multi_row_item(self.align_method):
                valid_multi_line_group.append(prob_Multiline_group)
        return valid_multi_line_group

    def find_valid_row_group(self, row: List[Dict[str, NodeItem]], node_items):
        """

        :param row: 对每行，如果有多个配置，需要检查多个配置中，满足从左至右侧，并且挨着的内容
        :return: 返回元素为 List[  List[Dict[str,NodeItem]] ]
                 返回的每个内容为一组，每组是一个可能的行,行内信息用NodeItemGroup 包括起来，使得程序更简洁一些
        """
        num_item = len(row)

        row = [list(special_loc.values()) for special_loc in row]

        if len(row) == 1:
            # 一行只有一个loc ,直接return
            first_loc = row[0]

            return [RowBGItem(loc) for loc in first_loc]

        valid_rows = []
        for comb in product(*row):
            # 按照顺序，应该保证从左到右，且右侧的node 的left 应该在左侧的right 右边
            valid_comb = True
            for i in range(1, len(comb)):
                left_node = comb[i - 1]
                right_node = comb[i]
                if not left_node.bbox.is_same_line(right_node.bbox, thresh=0.5) or not left_node.bbox.is_close_left(
                        right_node.bbox, thresh=1):
                    valid_comb = False
            if valid_comb:
                valid_rows.append(RowBGItem(comb))

        return valid_rows

    def check_bg_all_finded(self, prob_node_list):
        """

        :param prob_node_list: 对config 的每个位置都找到的对应的node_item
        :return: 判断是否config 涉及到的所有的位置都找到了可能的 node_item
        """
        valid = True
        for res_in_row, num_in_row in zip(prob_node_list, self.bg_nums):
            valid_res_in_specific_loc = 0
            for res_in_specific_loc in res_in_row:
                if len(res_in_specific_loc) > 0:
                    valid_res_in_specific_loc += 1
            if valid_res_in_specific_loc != num_in_row:
                valid = False
        return valid

    @record_time
    def find_node_for_each_bg(self, node_items):
        matched_node_info = []
        global_status = True
        # 一旦有一个位置一个都没有找到，后面的部分也不进行尝试了，用于减少时间

        for row in self.bg_items:
            row_matched = []
            for special_loc in row:
                matched_nodes = dict()
                if not global_status:
                    # global_status 是False，说明在这个位置之前，已经有一个位置没有找到内容了
                    row_matched.append(matched_nodes)
                for bg_item in special_loc:

                    if bg_item.mode == BgItem.MATCH_MODE_HORIZONTAL_SPLIT:
                        _matched_nodes, _matched_ed_dist, _rest_nodes = bg_item.match(node_items)
                        _rest_nodes = self.post_bg_h_split(_rest_nodes)

                        for node in _matched_nodes:
                            if getattr(node, 'is_cuted_node', None) is not None:
                                # 已经是被切过的了：
                                matched_nodes.update({node.uid: node})
                            else:
                                node.is_cuted_node = True if node.uid in node_items else False
                                matched_nodes.update({node.uid: node})

                        _rest_nodes.extend(_matched_nodes)

                        all_loc_of_nodes = set(
                            ['-'.join([str(loc) for loc in node.bbox.rect]) for node in node_items.values()])
                        for node in _rest_nodes:
                            if node.uid not in node_items:
                                node_loc = '-'.join([str(loc) for loc in node.bbox.rect])
                                if node_loc in all_loc_of_nodes:
                                    continue
                                # 加入进入的node ，也要记得设置成is_cuted_node
                                node.is_cuted_node = True
                                node_items.update({node.uid: node})

                    else:
                        _matched_nodes, _matched_ed_dist = bg_item.match(node_items)
                        for node in _matched_nodes:
                            node.is_cuted_node = False
                            matched_nodes.update({node.uid: node})
                    # if len(matched_nodes) > 0:
                    #     # 找到一个匹配的了，就不继续找了
                    #     break
                if len(matched_nodes) == 0:
                    # 如果存在没有找到的情形
                    global_status = False
                row_matched.append(matched_nodes)
            matched_node_info.append(row_matched)
        return global_status, matched_node_info

    def post_bg_h_split(self, _rest_nodes):
        for node in _rest_nodes:
            node.text = node.text.strip('_')
        return _rest_nodes
