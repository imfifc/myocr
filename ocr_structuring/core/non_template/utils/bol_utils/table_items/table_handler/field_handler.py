import uuid
from collections import OrderedDict
from typing import Dict, List

from ocr_structuring.core.non_template.utils.bol_utils.table_items.header.header_items import HeaderGroup, HeaderItem
from ocr_structuring.core.non_template.utils.bol_utils.utils.time_counter import record_time
from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.core.utils.node_item_group import NodeItemGroup
from .paragraph_handler import ParagraphHandler


class Field:
    # 一列作为一个Filed
    def __init__(self, header: HeaderItem, search_region: List):
        """

        :param header:
        :param search_region: 用于记录每个Field 的 (xmin,xmax)的搜索范围
        """
        self.header = header
        self.search_region = search_region
        self.uid = uuid.uuid1().hex

        self.nodes_in_field = NodeItemGroup()

    def insert_node(self, node):
        self.nodes_in_field.append(node)

    def insert_paragraph(self, paragraph: NodeItemGroup):
        paragraph.sort(lambda x: x.bbox.rect[0])
        for node in paragraph.node_items:
            self.nodes_in_field.append(node)

    @property
    def bbox(self):
        return self.nodes_in_field.bbox


class FieldGroup:
    # 若干列称为若干个Field， 用Group 统一管理
    def __init__(self, cfg, header_group):
        self.cfg = cfg
        self.header_group = header_group
        self.field_list = self.build_field_list(header_group)

    def build_field_list(self, header_group: HeaderGroup):
        field_list = []
        for header, search_region in zip(header_group.finded_header, header_group.get_header_region()):
            field_list.append(Field(header, search_region))
        return field_list

    @record_time
    def assign_fields(self, node_items: Dict[str, NodeItem]):
        """
        # 基本思路为：
        # 首先，第一步对每个node_item 划分为paragraph ，按照paragraph 分field 信息
        # 然后把field 信息分配给node_items


        :param node_items: 输入一系列的检测结果
        :return:  返回结果1： Dict[str,str] 返回每个node 属于的 列的 id
                  返回结果2： Dict[str, Field] 每个 列的id 对应的列
        """
        if self.cfg.FIELD_HANDLER.assign_by_paragraph:
            node_info, fields = self.assign_by_paragraph(node_items)
        else:
            node_info, fields = self.assign_by_node(node_items)

        # 删除不包含任何node的列
        for fid, field in fields.copy().items():
            if len(field.nodes_in_field.node_items) <= 0:
                del fields[fid]

        node_info, fields = self.recheck_fields(node_info, fields)
        return node_info, fields

    def recheck_fields(self, node_info, fields):
        """
        # 避免错分：

        # rule1 从左到右，如果每个列，右侧的列，列的最左侧部分具有一大堆左对齐的数据，基本可以认为是这个列的边界
        # 则对于本列当中的左边界在其内的node 重新分配组
        :param node_info: 对每个node 分配的信息
        :param fields: 对每个fields 分配所属的node
        :return:
        """
        fields = sorted(fields.items(), key=lambda x: x[1].header.bbox.rect[0])

        for i in range(0, len(fields) - 1):
            left_id, left_fields = fields[i]
            right_id, right_fields = fields[i + 1]

            # 检查左对齐
            xmin_of_right = right_fields.bbox[0]
            count = 0
            for node in right_fields.nodes_in_field.node_items:
                if node.bbox.rect[0] < xmin_of_right + right_fields.nodes_in_field.avg_height * 0.8:
                    count += 1
            if count > 5:
                # 在这一列里，有至少5行左对齐
                # 需要重新检查分配结果
                for idx in range(len(left_fields.nodes_in_field.node_items.copy()) - 1, -1, -1):
                    node = left_fields.nodes_in_field.node_items[idx]
                    if node.bbox.left > xmin_of_right:
                        # 需要重新assign
                        node_info[node.uid] = right_id
                        right_fields.nodes_in_field.append(node)
                        del left_fields.nodes_in_field.node_items[idx]
        return node_info, OrderedDict(fields)

    def assign_by_paragraph(self, node_items):
        # step1 group into paragraph
        paragraphs = ParagraphHandler.group_info_paragraphs(node_items)
        node_list = []
        node_field = []
        node_idx = []

        for paragraph in paragraphs:
            field_id = self.assign_field_for_each_paragraph(paragraph)
            # print('debug paragraph',paragraph.content())
            for node in paragraph.node_items:
                node_list.append(node)
                node_field.append(field_id)
                node_idx.append(node.uid)
        node_info = {uid: fid for uid, fid in zip(node_idx, node_field)}
        return node_info, {field.uid: field for field in self.field_list}

    def assign_by_node(self, node_items):
        node_list = []
        node_field = []
        node_idx = []
        for uid, node in node_items.items():
            filed_id = self.assign_field_for_each_node(node)
            node_list.append(node)
            node_field.append(filed_id)
            node_idx.append(uid)

        node_info = {uid: fid for uid, fid in zip(node_idx, node_field)}
        return node_info, {field.uid: field for field in self.field_list}

    def assign_field_for_each_node(self, node: NodeItem):
        # if getattr(node, 'rbox'):
        #     return self.assign_field_for_each_node_by_rbox(node)
        for field in self.field_list:
            if node.bbox.cx <= field.search_region[1] and node.bbox.cx > field.search_region[0]:
                field.insert_node(node)
                return field.uid

    def assign_field_for_each_node_by_rbox(self, node):
        # 获得rbox
        pass

    def assign_field_for_each_paragraph(self, paragraph: NodeItemGroup):
        for field in self.field_list:
            if paragraph.bbox.cx <= field.search_region[1] and paragraph.bbox.cx > field.search_region[0]:
                field.insert_paragraph(paragraph)
                return field.uid
