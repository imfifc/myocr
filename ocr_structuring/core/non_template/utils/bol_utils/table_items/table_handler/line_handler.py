# 在这里，写一些找行的代码
import uuid
from typing import Dict, List, Set

import numpy as np

from ocr_structuring.core.non_template.utils.bol_utils.table_items.header.header_items import HeaderGroup
from ocr_structuring.core.non_template.utils.bol_utils.utils.time_counter import record_time
from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.core.utils.node_item_group import NodeItemGroup
from ocr_structuring.utils.logging import logger
from .paragraph_handler import ParagraphHandler, Line


class LineGroup():
    def __init__(self, cfg, header_group: HeaderGroup):
        self.cfg = cfg
        self.header_group = header_group
        self.angle_of_header = self.header_group.get_header_angle()  # 平均斜率
        self.angle_of_header = float(self.angle_of_header)

    def make_node_info(self, rows, ):
        node_info = []
        node_id = []
        for row in rows:
            row.uid = uuid.uuid1().hex
            for node in row.node_items:
                node_info.append(row.uid)
                node_id.append(node.uid)
        assert len(node_id) == len(node_info)

        # 删除不包含任何node的行
        for idx in range(len(rows.copy()) - 1, -1, -1):
            row = rows[idx]
            if len(row.node_items) <= 0:
                del rows[idx]

        node_info = {uid: rid for uid, rid in zip(node_id, node_info)}
        row_map = {row.uid: row for row in rows}
        return node_info, row_map

    @record_time
    def assign_rows(self, node_items: Dict[str, NodeItem]):
        """
        在这里，对每一个node_items， 分配行信息
        """
        rows = self.group_into_rows(node_items)
        node_info, row_map = self.make_node_info(rows)

        if self.cfg.LINE_HANDLER.recheck_rows:
            node_info, row_map = self.recheck_rows_v2(node_info, row_map, node_items)

        return node_info, row_map

    def recheck_rows_v2(self, node_info, row_map, node_items, thresh=2):
        # 此方法不能解决所有的问题，仅针对品字形问题进行解决
        # 基本思路非常简单，对任意相邻的三行进行检查，如果存在第一行，第三行的两个点"紧挨"，而第二行有一个节点的高度
        # 和这两个紧挨点的中间高度差不多，则认为三行可以合并

        if len(row_map) <= 2:
            return node_info, row_map

        # 首先对row_map 从上往下进行排序
        ordered_row_map = sorted(row_map.items(), key=lambda x: x[1].bbox.top)

        # 初始化搜索位置
        new_row_group = []
        iter_mask = [False] * len(ordered_row_map)  # 用于记录哪些点已经被遍历过

        for i in range(0, len(ordered_row_map)):
            if i in [len(ordered_row_map) - 1, len(ordered_row_map) - 2]:
                iter_mask[i] = True
                new_row_group.append(ordered_row_map[i][1].node_items)
            # 移动三个节点的位置
            if iter_mask[i]:
                continue
            up_row, middle_row, down_row = ordered_row_map[i:i + 3]

            # 目前这个比较是由上往下的
            up_nodes = sorted(up_row[1].node_items, key=lambda x: x.bbox.left)
            down_nodes = sorted(down_row[1].node_items, key=lambda x: x.bbox.left)
            middle_nodes = sorted(middle_row[1].node_items, key=lambda x: x.bbox.left)

            benchmark_pair = None
            for up_node in up_nodes:
                find_pair = False
                for down_node in down_nodes:
                    left_to_right = down_node.bbox.left - up_node.bbox.right
                    if left_to_right > 0:
                        break
                    left_align = abs(up_node.bbox.left - down_node.bbox.left)
                    right_align = abs(up_node.bbox.right - down_node.bbox.right)
                    middle_align = abs(up_node.bbox.cx - down_node.bbox.cx)

                    if min(left_align, right_align, middle_align) > np.mean(
                            [up_node.bbox.height, down_node.bbox.height]):
                        continue
                    if abs(down_node.bbox.top - up_node.bbox.bottom) > 0.5 * np.mean(
                            [up_node.bbox.height, down_node.bbox.height]):
                        continue
                    find_pair = True
                    benchmark_pair = (up_node, down_node)
                    logger.info("find 品 shape pair {} , {}".format(up_node.text, down_node.text))
                    break
                if find_pair:
                    break
            # 计算中心位置
            if benchmark_pair is None:
                new_row_group.append(up_nodes)
                iter_mask[i] = True
                continue

            offset = abs(benchmark_pair[0].bbox.bottom - benchmark_pair[1].bbox.top) / 2
            center_y = min(benchmark_pair[0].bbox.bottom, benchmark_pair[1].bbox.top) + offset
            should_group = False
            for node in middle_nodes:
                if abs(node.bbox.cy - center_y) < node.bbox.height * 0.5:
                    should_group = True
                    break
            if should_group:
                new_group = up_nodes + middle_nodes + down_nodes
                new_row_group.append(new_group)
                iter_mask[i: i + 3] = True, True, True
            else:
                new_row_group.append(up_nodes)
                iter_mask[i] = True

        new_rows = []
        for row in new_row_group:
            new_rows.append(Line(row))

        node_info, row_map = self.make_node_info(new_rows)
        return node_info, row_map

    def recheck_rows(self, node_info, row_map, node_items):
        """
        基本思想，如果从上往下排序：
        1-2-3-4-5-6-7
        满足 ： 1和3 是上下紧挨着的，3和5是上下紧挨的
        原则上 （1-5）应该被视为一行，


        :param node_info:
        :param row_map:
        :param node_items:
        :return:
        """
        _CLOSE_NEXT_THRESH = 0.25

        # 首先，对所有的row 按照从上往下的顺序进行排序
        ordered_row_map = sorted(row_map.items(), key=lambda x: x[1].bbox.top)

        # 记录当前处理过的行
        # 注意，比如 1-2-3-4-5 ，如果在分析1的时候，注意到 1，2，3应该分为一组，此时parse_id 只记录到2，因为3可能还会和后面的可以合并
        row_group: List[Set] = [set()]  # 先放一个，方便些程序
        for idx, (rid, row) in enumerate(ordered_row_map):
            if idx == len(ordered_row_map) - 1:
                # 分析最后一个数据
                if idx in row_group[-1]:
                    # 已经分析过
                    continue
                else:
                    # 如果没有处理过，新加一个组
                    row_group.append(set([idx]))

            # 现在是idx 不是最后一个的情况
            # if idx in parsed_rid:
            #     continue
            # 分析interval 和 next

            interval_idxs = []  # 在紧挨着的下一个行和之间涉及到的idx
            closed_list = []
            has_close_next = False
            for next_idx in range(idx + 1, len(ordered_row_map)):
                # 判断是否有存在 "找到一个紧挨着的row ，且这个row 和 idx 之间还隔着一些 行"
                next_rid, next_row = ordered_row_map[next_idx]
                # 只有三种状态：
                # 1 不是紧挨，且在之间
                # 2 是紧挨着的
                # 3 没有相接触，直接更远
                next_median = np.median([node.bbox.top for node in next_row.node_items])
                cur_median = np.median([node.bbox.bottom for node in row.node_items])
                thresh = (next_median - cur_median) / ((row.avg_height + next_row.avg_height) / 2)

                row.sort(lambda x: x.bbox.left)
                next_row.sort(lambda x: x.bbox.left)
                if thresh > _CLOSE_NEXT_THRESH:
                    # 说明next_row 在它下面，且没有紧挨着
                    # 此时 has_close_next 为False ，所以不需要考虑合并
                    break
                elif thresh < -_CLOSE_NEXT_THRESH:
                    # 说明是一个居中的
                    # print('debugger near', idx, next_idx , row.content(), '->', next_row.content(), thresh)
                    interval_idxs.append(next_idx)
                else:
                    # 说明存在一个紧挨着的:
                    # print('debugger close', idx, next_idx , row.content(), '->', next_row.content(), thresh)
                    has_close_next = True
                    # 注意到每一行可能会有多个closed
                    closed_list.append(next_idx)

            can_merge = False
            if (len(interval_idxs) > 0 or len(closed_list) > 1) and has_close_next:
                # TODO 检查这些行能否合并
                can_merge = True

            # parsed_rid.add(idx)
            # 如果当前idx 已经出现在group 当中，则继续合并至最后一个group
            if idx not in row_group[-1]:
                # 没有出现过，是一个新的组，所以要新建一个组
                row_group.append(set([idx]))

            if can_merge:
                row_group[-1].update(set(interval_idxs))
                row_group[-1].update(set(closed_list))

        row_map = {}
        node_info = {}
        row_group = row_group[1:]
        for group in row_group:
            node_in_group = []
            for id in group:
                node_in_group.extend(ordered_row_map[id][1].node_items)
            new_row = NodeItemGroup(node_in_group)
            new_row.uid = uuid.uuid1().hex
            row_map.update({new_row.uid: new_row})
            node_info.update({node.uid: new_row.uid for node in new_row.node_items})

        return node_info, row_map

    def require_angle_from_node_items(self, node_items):
        node_item_list = [node for node in node_items.values() if len(node.text) > 4]
        if len(node_item_list) > 0:
            meaningfule_angle_list = np.array([node.rbox.meaningful_angle for node in node_item_list])
            # 去除角度为0的部分
            median_angle = np.median(meaningfule_angle_list)
            self.angle_of_header = median_angle

    def group_into_rows(self, node_items):
        # 如果 angle 是小的，则直接使用简单的流程
        logger.info('angle of header is {}'.format(self.angle_of_header))

        self.require_angle_from_node_items(node_items)

        if not self.cfg.LINE_HANDLER.consider_angle:
            # 大角度采用第二种方法
            rows = ParagraphHandler.group_into_rows(node_items)
        else:
            rows = ParagraphHandler.group_into_lines(node_items, self.angle_of_header,
                                                     self.cfg.LINE_HANDLER.angle_merge_thresh)

        return rows
