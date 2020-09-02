import typing
from typing import List, Dict

import numpy as np

from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.core.utils.node_item_group import NodeItemGroup


class Paragraph(NodeItemGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def content(self, join_char=' '):
        return join_char.join([it.text for it in self.node_items])


class Line(NodeItemGroup):
    # 对处于一行的节点，构造行变量
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ParagraphHandler:

    @staticmethod
    def end_parag_condition(it: NodeItem, parag: NodeItemGroup):
        return (it.bbox.top - parag.bbox.bottom) >= parag.avg_height

    @staticmethod
    def in_parag_condition(it, parag):
        return abs(parag.bbox.left - it.bbox.left) < parag.avg_height and (
                it.bbox.right - parag.bbox.left) > 0.1 * it.bbox.width

    @staticmethod
    def in_row_condition(it, row: NodeItemGroup):
        """
        判断这个it 是否在对应的行当中
        :param it: 新的node_item
        :param row: 行NodeItemGroup
        :return: bool
        """
        # it 的top 和 row 的top 差距不能大于0.5个row 高度
        return abs(it.bbox.cy - row.bbox.cy) < 0.5 * row.avg_height

    @staticmethod
    def end_row_condition(it, row: NodeItemGroup):
        """
        当it 和row 满足这个条件时，这个row 就结束了

        :param it:
        :param row:
        :return:
        """
        return it.bbox.top > row.bbox.bottom

    @staticmethod
    def cal_angle(bbox1, bbox2, angle_of_line):
        angle = 999
        for xpos, ypos in zip(['left', 'cx', 'right'], ['top', 'cy', 'bottom']):
            header1_cx = getattr(bbox1, xpos)
            header1_cy = getattr(bbox1, ypos)

            header2_cx = getattr(bbox2, xpos)
            header2_cy = getattr(bbox2, ypos)

            if header1_cx > header2_cx:
                header1_cx, header1_cy, header2_cx, header2_cy = header2_cx, header2_cy, header1_cx, header1_cy
            cur_angle = np.arctan2([header2_cy - header1_cy], [header2_cx - header1_cx])[0] / np.pi * 180
            if abs(cur_angle - angle_of_line) < abs(angle - angle_of_line):
                angle = cur_angle
        return angle

    @staticmethod
    def cal_rangle(rbox1, rbox2, angle_of_line):
        angle = 999
        for loc in ['up_left', 'up_right', 'down_left', 'down_right']:
            if rbox1.cx > rbox2.cx:
                rbox1, rbox2 = rbox2, rbox1

            loc1 = getattr(rbox1, loc)
            loc2 = getattr(rbox2, loc)

            cur_angle = np.arctan2([loc2[1] - loc1[1]], [loc2[0] - loc1[0]])[0] / np.pi * 180
            if abs(cur_angle - angle_of_line) < abs(angle - angle_of_line):
                angle = cur_angle
        return angle

    @staticmethod
    def line_condition(it, rows, angle_of_line):
        # 基本判断方法，选择和其中iou 小于一定阈值的，rows当中最近的框计算angle
        useful_row = []
        for node in rows.node_items:
            if it.bbox.cal_iou(node.bbox) < 0.3:
                useful_row.append((node, (it.bbox.cx - node.bbox.cx) ** 2 + (it.bbox.cy - node.bbox.cy) ** 2))
        if len(useful_row) == 0:
            # 说明这个框和上一行的node 高度重合,并入这一行
            return 0
        first_dist_node = sorted(useful_row, key=lambda x: x[1])[0][0]

        if getattr(it, 'rbox'):
            angle = ParagraphHandler.cal_rangle(it.rbox, first_dist_node.rbox, angle_of_line)
        else:
            angle = ParagraphHandler.cal_angle(it.bbox, first_dist_node.bbox, angle_of_line)

        # print('angle', it.text, first_dist_node.text, angle)
        return angle

    @staticmethod
    def line_condition_adaptive(it, rows, angle_of_line_or_func, mean_height):
        if callable(angle_of_line_or_func):
            angle_of_line = angle_of_line_or_func(it.bbox.cy)
        else:
            angle_of_line = angle_of_line_or_func

        def evaluation(x):
            diff = [
                it.bbox.cy - x[0].bbox.cy,
                it.bbox.top - x[0].bbox.top,
                it.bbox.bottom - x[0].bbox.bottom
            ]
            y_diff = diff[np.argmin([abs(d) for d in diff])]
            return abs(np.tan(angle_of_line / 180 * np.pi) * (x[0].bbox.cx - it.bbox.cx) + y_diff)

        # 基本判断方法，选择和其中iou 小于一定阈值的，rows当中最近的框计算angle
        useful_row = []
        for node in rows.node_items:
            if it.bbox.cal_iou(node.bbox) < 0.3:
                useful_row.append((node, (it.bbox.cx - node.bbox.cx) ** 2 + (it.bbox.cy - node.bbox.cy) ** 2))
        if len(useful_row) == 0:
            # 说明这个框和上一行的node 高度重合,并入这一行
            return 0
        # first_dist_node = sorted(useful_row, key=evaluation)[0][0]
        first_dist_node = sorted(useful_row, key=lambda x: x[1])[0][0]
        # 自适应的做法，基于first_dist_node 来找行
        y_offset = np.tan(angle_of_line / 180 * np.pi) * (it.bbox.cx - first_dist_node.bbox.cx)
        pred_cy = y_offset + first_dist_node.bbox.cy
        pred_top = y_offset + first_dist_node.bbox.top
        pred_bottom = y_offset + first_dist_node.bbox.bottom
        #
        # print('debugger', first_dist_node.text, it.text, mean_height, angle_of_line ,
        #       min(abs(it.bbox.cy - pred_cy), abs(it.bbox.top - pred_top), abs(it.bbox.bottom - pred_bottom)))
        return min(abs(it.bbox.cy - pred_cy), abs(it.bbox.top - pred_top), abs(it.bbox.bottom - pred_bottom))

    @staticmethod
    def in_line_condition(angle_of_line, angle_merge_thresh=2):

        def func(it, rows: NodeItemGroup, return_score=False):
            # "score 越低越好"
            angle = ParagraphHandler.line_condition(it, rows, angle_of_line)

            if return_score:
                return abs(angle - angle_of_line), abs(angle - angle_of_line) < angle_merge_thresh

            if abs(angle - angle_of_line) < angle_merge_thresh:
                return True
            else:
                return False

        return func

    @staticmethod
    def in_line_condition_adaptive(angle_of_line, mean_height):
        # mean_height : 行高

        def func(it, rows: NodeItemGroup, return_score=False):
            h_offset = ParagraphHandler.line_condition_adaptive(it, rows, angle_of_line, mean_height)
            if return_score:

                return abs(h_offset), h_offset < mean_height * 0.5
            else:
                return h_offset < mean_height * 0.5

        return func

    @staticmethod
    def group_into(Paragraph_type: typing.Type[NodeItemGroup], node_items: Dict[str, NodeItem], end_condition,
                   in_condition) -> List[NodeItemGroup]:
        """
        输入一系列的node_items ,将这些node_items 按照左对齐的方式，区分成一系列的paragraph
        :return:
        """
        node_items = sorted(node_items.items(), key=lambda x: x[1].bbox.top)

        paragraphs: List[NodeItemGroup] = []
        pool: List[NodeItemGroup] = []

        for uid, it in node_items:
            appended = False
            ended_parags_idx_in_pool = []

            for j, parag in enumerate(pool):
                # 退出parag 的条件
                if end_condition(it, parag):
                    ended_parags_idx_in_pool.append(j)
                    continue

                # 进入parag 的条件
                if in_condition(it, parag):
                    parag.append(it)
                    appended = True

            # 要从最后一项开始 pop，必须先 sort
            ended_parags_idx_in_pool.sort(reverse=True)
            for j in ended_parags_idx_in_pool:
                paragraphs.append(pool.pop(j))

            # 如果 node item 没有归类为任何一个段落则创建一个新的段落
            if not appended:
                p = Paragraph_type()
                p.append(it)
                pool.append(p)

        paragraphs.extend(pool)
        return paragraphs

    @staticmethod
    def group_into_for_rotate(Paragraph_type: typing.Type[NodeItemGroup], node_items: Dict[str, NodeItem],
                              in_condition) -> List[NodeItemGroup]:
        """
        当纸张出现倾斜的时候，就很难利用退出条件退出，只能暴力搜索
        :param Paragraph_type:
        :param node_items:
        :param end_condition:
        :param in_condition:
        :return:
        """

        node_items = sorted(node_items.items(), key=lambda x: x[1].bbox.top)

        paragraphs: List[NodeItemGroup] = []

        for uid, it in node_items:
            # 遍历所有的paragraphs ，如果存在一个可以加入的，加入，如果不可以加入，新建
            appended = False

            satisfy_list = []
            for idx, parag in enumerate(paragraphs):
                score, satisfy = in_condition(it, parag, return_score=True)
                if satisfy:
                    satisfy_list.append((idx, score))
            if len(satisfy_list) > 0:
                appended = True
                most_satisfy = sorted(satisfy_list, key=lambda x: x[1])[0][0]
                paragraphs[most_satisfy].append(it)

            if not appended:
                p = Paragraph_type()
                p.append(it)
                paragraphs.append(p)
        return paragraphs

    @staticmethod
    def group_info_paragraphs(node_items):
        return ParagraphHandler.group_into(Paragraph,
                                           node_items,
                                           ParagraphHandler.end_parag_condition,
                                           ParagraphHandler.in_parag_condition
                                           )

    @staticmethod
    def group_into_rows(node_items):
        return ParagraphHandler.group_into(Line,
                                           node_items,
                                           ParagraphHandler.end_row_condition,
                                           ParagraphHandler.in_row_condition
                                           )

    @staticmethod
    def group_into_lines(node_items, angle_of_line, angle_merge_thresh):
        """

        :param node_items: 待分行的node_items
        :param angle_of_line: 每行的角度
        :return:
        """
        return ParagraphHandler.group_into_for_rotate(
            Line,
            node_items,
            ParagraphHandler.in_line_condition(angle_of_line, angle_merge_thresh)
        )

    @staticmethod
    def group_into_lines_adaptive(node_items, angle_of_line, ratio=1.5):
        """
        尝试采用自适应的方式找共行
        :param node_items:
        :param angle_of_line: 一个用于计算角度的函数，或者一个常数
        :param ratio : 行距，标准行距默认是1.5
        :return:
        """
        # 首先在这里尝试计算表格node 的平均行高
        # step1 从左到右排序
        nodes = list(node_items.values())
        if getattr(nodes[0], 'rbox'):
            node_height = np.mean([node.rbox.height for node in nodes])
        else:
            node_height = np.mean([node.bbox.height for node in nodes])

        if ratio == -1:
            # 自适应的确定行高
            # 首先简单的找行，然后确认行和行之间的距离
            easy_rows = ParagraphHandler.group_into_rows(node_items)
            # 计算一下diff
            line_center = [line.bbox.cy for line in easy_rows]
            line_center.sort()
            line_diff = np.diff(line_center)
            line_diff_ = line_diff[
                (line_diff > np.percentile(line_diff, 15)) * (line_diff < np.percentile(line_diff, 85))]
            line_interval = line_diff_.mean() if line_diff_.shape[0] > 0 else line_diff.mean()
            ratio = line_interval / node_height * 0.6

        return ParagraphHandler.group_into_for_rotate(
            Line,
            node_items,
            ParagraphHandler.in_line_condition_adaptive(angle_of_line, node_height * ratio)

        )
