from collections import defaultdict
from itertools import combinations

import numpy as np

from ocr_structuring.utils.logging import logger
from .medical_table_config import replace_map, RE_RECOGNIZE_MONEY
from ...template.tp_node_item import TpNodeItem
from ...utils import str_util
from ...utils.crnn import crnn_util


# 首先，从所有的node中找到left的节点
class Node:
    def __init__(self, node_item: TpNodeItem, row_num):
        # 输入找到的node_item
        self.node_item = node_item
        self.row_num = row_num
        self.height = node_item.trans_bbox.height
        self.cy = node_item.trans_bbox.cy
        self.cx = node_item.trans_bbox.cx
        self.left = node_item.trans_bbox.left
        self.right = node_item.trans_bbox.right
        self.top = node_item.trans_bbox.top
        self.down = node_item.trans_bbox.bottom


class Column:
    def __init__(self, row_num):
        # 预先定义好需要有几行
        self.row_num = row_num
        self.nodes = [None] * self.row_num

    def _insert_row(self, node: Node):
        # 把node 插入在相应的行当中
        self.nodes[node.row_num] = node

    def clean_node(self):
        # TODO 如果某一个点的 位置比较异常，则将其踢出出去
        pass

    def _clean_invalid_row(self):
        # 对于那些异常的点，将其进行清理
        if not self.nodes:
            return

    def _get_not_none_row_num(self):
        count = 0
        for node in self.nodes:
            if node:
                count += 1
        return count

    def _get_table_height(self):
        # 利用填入的row的高度信息，推断出表格应该有多高
        row_has_content = list(filter(lambda x: x is not None, self.nodes))
        row_has_content = sorted(row_has_content, key=lambda x: x.row_num)
        first_row = row_has_content[0]
        last_row = row_has_content[-1]
        # 推断出表格的高度
        start_of_table = 0
        # 推断开始的位置
        if first_row.row_num != 0:
            dy = (last_row.cy - first_row.cy)
            mean_height = dy / (last_row.row_num - first_row.row_num)
            start_of_table = first_row.cy - mean_height * first_row.row_num - mean_height / 2
        else:
            start_of_table = first_row.top

        end_of_table = 0
        # 推断开始的位置
        if last_row.row_num != self.row_num - 1:
            dy = (last_row.cy - first_row.cy)
            mean_height = dy / (last_row.row_num - first_row.row_num)
            end_of_table = last_row.cy + mean_height * (
                    self.row_num - 1 - last_row.row_num) + mean_height / 2
        else:
            end_of_table = last_row.down

        return start_of_table, end_of_table

    def _get_mean_height(self):
        ymin, ymax = self._get_table_height()
        return (ymax - ymin) / self.row_num, ymin, ymax

    def _get_row_top_bottom(self, row):
        assert row <= self.row_num - 1
        mean_height, ymin, ymax = self._get_mean_height()
        row_start = ymin + row * mean_height
        row_end = ymin + ((row + 1) * mean_height)
        return row_start, row_end


class LeftColumn(Column):
    def __init__(self, row_num):
        super(LeftColumn, self).__init__(row_num)

    def _get_table_width(self, thres=1.5):
        # 设置根据长宽比推断表格的右侧应该是什么位置
        ymin, ymax = self._get_table_height()
        width = thres * (ymax - ymin)
        # 计算表的开始位置
        row_has_content = list(filter(lambda x: x is not None, self.nodes))
        mean_start = np.mean([row.left for row in row_has_content])
        mean_end = mean_start + width
        return mean_start, mean_end

    def _get_table_location(self, thres=0.01, thres_x=1.5):
        ymin, ymax = self._get_table_height()
        height = ymax - ymin
        ymin = ymin - height * thres / 2
        ymax = ymax + height * thres / 2
        xmin, xmax = self._get_table_width(thres_x)
        return xmin, int(ymin), xmax, int(ymax)

    def _get_left_bound(self):
        row_has_content = list(filter(lambda x: x is not None, self.nodes))
        row_left_bound = np.mean([node.right for node in row_has_content])
        return row_left_bound


class RightColumn(Column):
    def __init__(self, row_num):
        super(RightColumn, self).__init__(row_num)
        self.right_nodes = self.nodes
        self.matched_value = [None] * row_num

    def _get_right_bound(self):
        row_has_content = list(filter(lambda x: x is not None, self.nodes))
        row_right_bound = np.max([node.right for node in row_has_content])
        return row_right_bound

    def _clean_node_beyond_right(self, right_nodes):

        mean_right = self._get_right_bound()

        filter_nodes = []
        for node in right_nodes:
            if node.trans_bbox.left > mean_right:
                continue
            filter_nodes.append(node)
        return filter_nodes

    def _clean_node_by_rule(self, right_nodes):
        filter_node = []
        for node in right_nodes:
            if str_util.keep_eng_num_char(node.text) == '':
                continue
            if len(node.text) == 1:
                continue
            filter_node.append(node)
        return filter_node

    def _clean_node(self, right_nodes):
        clean_by_right = self._clean_node_beyond_right(right_nodes)
        clean_by_rule = self._clean_node_by_rule(clean_by_right)
        return clean_by_rule


class Matcher:
    def __init__(self, row_num, left_col: LeftColumn, clean_nodes: LeftColumn, right_col: RightColumn = None,
                 image: np.ndarray = None, re_recog=False):
        self.left_col = left_col
        self.right_col = right_col
        self.clean_nodes = clean_nodes
        self._clean_again()
        self.row_num = row_num
        self.match_node = [None] * row_num
        self.image = image
        self.re_recog = re_recog

    def _clean_again(self):
        # 在 _matcher_by_right_col 的匹配模式中， filter_node中是不应该有right_uid包含的node的
        # 但是在 _matcher_by_rule 的模式中，filter_node 和 right_node 应该被综合考虑
        left_uid = [left_row.node_item.uid for left_row in self.left_col.nodes if left_row is not None]
        right_uid = [right_row.node_item.uid for right_row in self.right_col.nodes if right_row is not None]
        filter_node = []
        for node in self.clean_nodes:
            if node.uid in left_uid or node.uid in right_uid:
                continue
            else:
                filter_node.append(node)

        # 通过如下方法对node进行清理，如果一个节点的横坐标没有比任何一个left_ndoe的横坐标大，则认为这个节点应该被清理
        filter_by_axis = []
        left_nodes_not_none = [node.node_item for node in self.left_col.nodes if node is not None]
        for node in filter_node:
            is_right = False
            for left_node in left_nodes_not_none:
                if node.trans_bbox.left > left_node.trans_bbox.cx + left_node.trans_bbox.width * 0.1:
                    is_right = True
                    break
            if is_right:
                filter_by_axis.append(node)
        self.clean_nodes = filter_by_axis

    def _add_right_to_clean_node(self):
        right_nodes = [node.node_item for node in self.right_col.nodes if node is not None]
        self.clean_nodes.extend(right_nodes)

    def matcher(self):

        if self.right_col and self.right_col._get_not_none_row_num() > 1 and self.left_col._get_not_none_row_num() > 1:
            return self._matcher_by_right_col()
        elif self.left_col._get_not_none_row_num() > 1:
            self._add_right_to_clean_node()
            return self._matcher_by_rule()
        else:
            return [None] * self.row_num

    def _format_right_node_text(self, node: TpNodeItem, re_recognize=True, reset_node_text=False):
        """

        :param node:  传入可能存在数字的节点
        :param re_recognize: 是否进行重识别
        :param reset_node_text:  是否要将重识别的结果赋值给node，注意到赋值会影响后续的识别过程
        :return:
        """
        if self.re_recog and self.image is not None and not node.is_re_recognized:
            # 在这里进行重识别
            # config中区域框的目的是为了更好的寻找前景，在这一步对于数值部分，如果没有重识别，补充进行重识别
            org_rect = node.bbox.rect

            crnn_res, _ = crnn_util.run_number_amount(self.image, org_rect)
            if crnn_res:
                # logger.debug(f'crnn_res : {crnn_res}, org is : {node.text}')
                if reset_node_text:
                    node.text = crnn_res
                text = crnn_res
            else:
                text = node.text

        else:
            text = node.text
        for key_map in replace_map:
            text = text.replace(key_map, replace_map[key_map])
        text = str_util.only_keep_start_money_char(text)
        if not text:
            return text
        text = str_util.remove_last_dot(text)
        text = str_util.remove_extra_dot(text)
        only_zero = str_util.contain_only_special(text, '0')
        if only_zero:
            text = '0.00'
        else:
            if str_util.keep_num_char(text) == text:
                if len(text) >= 3:
                    # 说明这个text 没有小数点，贪心的在最后加入两个
                    text = text[:-2] + '.' + text[-2:]
                else:
                    text = '0.' + text[:2]
        return text

    def _sorted_clean_node(self):
        # 按照y轴排序

        return sorted(self.clean_nodes, key=lambda node: node.trans_bbox.cy)

    def _matcher_by_rule(self):
        # 首先，获得所有可能的nod
        # list(combinations(A, 4))
        # 首先，建立一个关系矩阵，判断每个node和近邻的关系
        node_sorted = self._sorted_clean_node()

        # 如果node_sorted 只能找到一个，那就判断他和左侧的哪一个关系更好
        if len(node_sorted) == 1:
            res_node = node_sorted[0]
            best_match = None
            best_match_dis = 999
            for idx, left_node in enumerate(self.left_col.nodes):
                if left_node:
                    diff = abs(res_node.trans_bbox.cy - left_node.node_item.trans_bbox.cy)
                    if diff < best_match_dis:
                        best_match_dis = diff
                        best_match = idx
            if best_match_dis < 10:
                res = [None] * self.row_num
                res[best_match] = res_node.text
                return res
            else:
                res = [None] * self.row_num
                return res

        node_relation = defaultdict(dict)
        # 对每一个node,计算这个node上移、下移一个单位，和别的节点的ioo
        # 如果一个和他上移、下移一个格子的ioo大于阈值，认为这个格子和他是在一列的
        for node in node_sorted:
            node_box = node.trans_bbox
            node_above_box = node_box.get_offset_box(col_offset=0, row_offset=-1)
            node_below_box = node_box.get_offset_box(col_offset=0, row_offset=1)
            # 计算剩余框和这些box的iou
            for other_node in node_sorted:
                if other_node.uid != node.uid:
                    # 计算他们的iou
                    iou1 = node_below_box.cal_iou(other_node.trans_bbox)
                    iou2 = node_above_box.cal_iou(other_node.trans_bbox)
                    iou = max(iou1, iou2)
                    if iou > 0.4:
                        node_relation[node.uid][other_node.uid] = 1
        # 对每一个node，统计和他相邻的其他node的个数，对那些有两个相邻的node，将其取出
        right_col_node = set()
        for node_uid in node_relation:
            if sum(node_relation[node_uid].values()) >= 2:
                # 认为这个node在对应的列上
                right_col_node.update((node_uid,))
                right_col_node.update(set(node_relation[node_uid].keys()))
        if len(right_col_node) == self.row_num:
            # 正确的将所有的部分都取出来了
            # 现在的话，默认的处理方式为，把数字从上到下的进行排列，如果找到了大于row_num的个数
            # 简单的只取上方的row_num 个
            right_col_node = [node for node in node_sorted if node.uid in right_col_node]
            right_col_node = sorted(right_col_node, key=lambda node: node.trans_bbox.cy)
            return [self._format_right_node_text(node, RE_RECOGNIZE_MONEY) for node in right_col_node][:self.row_num]
        else:
            # right_col_node 构成了右侧的列的部分，但是有的内容没有检测出来
            # 此时的处理防范为，首先把右侧找到的数据中，和左侧的行的信息中有对应关系的，找出来
            # 然后根据它自己在第几行，推断出第一行和最后一样的框的位置，上移，下移若干个单位，找到列对应区域
            # 利用这些区域把所有的位置捞出来
            # 然后遍历所有可能的排列情形，进行align

            # 首先，获得每一个左行匹配到的右侧的node，虽然可能会匹配不准，但是这一步主要是
            # 为了获得右侧的列的大致位置
            left_row_not_none = [left_node.node_item for left_node in self.left_col.nodes if left_node is not None]
            # 首先完成对left node 的匹配
            best_match_y_dis = 999
            best_match_pair = None
            for possible_match_res in combinations(node_sorted, self.left_col._get_not_none_row_num()):
                # 让possible_res 和 left_col 作比较
                cur_dis = 0
                logic_match = True
                for match_res, node in zip(possible_match_res, left_row_not_none):
                    cur_dis += abs(match_res.trans_bbox.cy - node.trans_bbox.cy)
                    if match_res.trans_bbox.cx <= node.trans_bbox.cx + node.trans_bbox.width * 0.1:
                        logic_match = False
                if not logic_match:
                    continue
                if cur_dis < best_match_y_dis:
                    # 去除所有的节点中的数字部分
                    match_res_text = [self._format_right_node_text(res, RE_RECOGNIZE_MONEY) for res in
                                      possible_match_res]
                    best_match_pair = [node for idx, node in enumerate(possible_match_res) if match_res_text[idx]]
                    best_match_y_dis = cur_dis
            if not best_match_pair:
                return [None] * self.row_num

            right_col_x_start = np.median([node.trans_bbox.left for node in best_match_pair])
            right_col_x_end = np.median([node.trans_bbox.right for node in best_match_pair])
            right_col_y_start, right_col_y_end = self.left_col._get_table_height()
            right_rect = [right_col_x_start, right_col_y_start, right_col_x_end, right_col_y_end]
            # 考虑到会有透视变换，这里将搜索区域的y值扩大一定程度
            right_rect[1] = right_rect[1] - 0.1 * (right_rect[3] - right_rect[1])
            right_rect[3] = right_rect[3] + 0.1 * (right_rect[3] - right_rect[1])
            node_in_region = []
            for node in node_sorted:
                if node.trans_bbox.is_center_in(right_rect):
                    node_in_region.append(node)

            # node_in_region = sorted(node_in_region,key = lambda x: x.trans_bbox.cy)
            if len(node_in_region) == self.row_num:
                return [self._format_right_node_text(node, RE_RECOGNIZE_MONEY) for node in node_in_region]
            elif len(node_in_region) <= 1:
                # 只找到两个低话，基本等于没救了
                return [None] * self.row_num
            # 现在 node_in_region的个数不足6个，首先检查是否存在大的间隔

            node_in_region_with_pad = [node_in_region[0]]
            mean_height = np.mean([node.trans_bbox.height for node in node_in_region])
            for idx in range(1, len(node_in_region)):
                node_diff = node_in_region[idx].trans_bbox.top - node_in_region[idx - 1].trans_bbox.bottom
                if node_diff / mean_height <= 1:
                    # 认为间隔小于平均高度，则认为这些点是紧挨的
                    node_in_region_with_pad.append(node_in_region[idx])
                else:
                    pad_num = int(node_diff / mean_height)
                    node_in_region_with_pad.extend([None] * pad_num)
                    node_in_region_with_pad.append(node_in_region[idx])

            # 如果找到了row_num个，则认为搞定了
            if len(node_in_region_with_pad) == self.row_num:
                for idx, value in enumerate(node_in_region_with_pad):
                    if value:
                        node_in_region_with_pad[idx] = self._format_right_node_text(value, RE_RECOGNIZE_MONEY)
                return node_in_region_with_pad
            # 走到这一步骤，还没有搞定的，就是找到了连续的比如四个，五个，但是缺失了开头或者结尾的那几个
            # TODO 因为这批检测效果较好，这种情况比较少，暂时不考虑
            # 这时候，一定是在上方和下放存在着空格的部分
            need_to_pad = self.row_num - len(node_in_region_with_pad)
            diff_on_top = max(0, node_in_region_with_pad[0].trans_bbox.top - right_rect[1])
            diff_on_bottom = max(0, right_rect[3] - node_in_region_with_pad[-1].trans_bbox.bottom)
            diff_all = diff_on_top + diff_on_bottom

            if diff_on_bottom > diff_on_top:
                # 如果diff_on_bottom > diff_on_top , 说明下面空的比较多
                # 则先把下面填充起来
                pad_on_bottom = int(diff_on_bottom / mean_height) if int(
                    diff_on_bottom / mean_height) <= need_to_pad else need_to_pad
                pad_on_top = need_to_pad - pad_on_bottom
            else:
                pad_on_top = int(diff_on_top / mean_height) if int(
                    diff_on_top / mean_height) <= need_to_pad else need_to_pad
                pad_on_bottom = need_to_pad - pad_on_top
            node_in_region_with_pad = [None] * pad_on_top + node_in_region_with_pad + [None] * pad_on_bottom

            for idx, value in enumerate(node_in_region_with_pad):
                if value:
                    node_in_region_with_pad[idx] = self._format_right_node_text(value, RE_RECOGNIZE_MONEY)
            return node_in_region_with_pad

    def _matcher_by_right_col(self):
        # 首先，如果有值，就尝试着填进去
        for right_node in self.right_col.right_nodes:
            if not right_node:
                # 即这个地方没有找到合理的关键字段，暂时先不考虑
                continue
            # 首先，尝试用clean_node中间的内容去匹配right_node
            for possible_node in self.clean_nodes:
                if possible_node.uid == right_node.node_item.uid:
                    continue
                if possible_node.trans_bbox.is_same_line(right_node.node_item.trans_bbox, thresh=0.3):
                    self.match_node[right_node.row_num] = self._format_right_node_text(possible_node,
                                                                                       RE_RECOGNIZE_MONEY)
                    self.clean_nodes.remove(possible_node)
                    break
            # 其次，判断是否成功的进行了赋值
            if not self.match_node[right_node.row_num]:
                format_right = self._format_right_node_text(right_node.node_item, RE_RECOGNIZE_MONEY)
                # 其次，如果没有值，就尝试着把每个字段的一部分内容进行格式化填进去
                if format_right:
                    self.match_node[right_node.row_num] = format_right

        if sum([not match_res is None for match_res in self.match_node]) != self.row_num:
            # 说明结果有问题，剩下的任务，是对右侧关键字缺失的字段进行合理的推断
            # 在剩下的node中，判断剩下的node，是否有处于确实的高度范围内的node，对node进行数字化，选择结果
            for idx, content in enumerate(self.match_node):
                if not content:
                    possible_text = ''
                    left_infer_ymin, left_infer_ymax = self.left_col._get_row_top_bottom(idx)
                    right_infer_ymin, right_infer_ymax = self.right_col._get_row_top_bottom(idx)
                    ymin = min(left_infer_ymin, right_infer_ymin)
                    ymax = max(left_infer_ymax, right_infer_ymax)
                    xmin = self.left_col._get_left_bound()
                    xmax = self.right_col._get_right_bound()

                    for node in self.clean_nodes:
                        if node.trans_bbox.is_center_in([xmin, ymin, xmax, ymax]):
                            possible_text = self._format_right_node_text(node, RE_RECOGNIZE_MONEY)
                            break
                    if possible_text:
                        self.match_node[idx] = possible_text
        return self.match_node
