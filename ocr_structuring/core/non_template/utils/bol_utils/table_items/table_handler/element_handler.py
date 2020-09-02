import re
from collections import defaultdict
from typing import Dict, List

import editdistance as ed
import numpy as np
import pandas as pd

from ocr_structuring.core.non_template.utils.bol_utils.table_items.table_handler.keyrow_handler import KeyrowGroup
from ocr_structuring.core.non_template.utils.bol_utils.utils.time_counter import record_time
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.node_item_group import NodeItemGroup
from ocr_structuring.utils.logging import logger

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
from itertools import chain
from .field_handler import Field
from ocr_structuring.core.utils.node_item import NodeItem
from . import element_common_rules as element_common_rules
from collections import OrderedDict
from ocr_structuring.core.non_template.utils.bol_utils.utils.structures import ElementTextType

TOTAL_STATS_REGEX = [
    '(Total|TOTAL)s?_{,2}:[0-9\._]*L?',
    'TOTAL_{,2}:([0-9]*(PCS|KG)){1,}.*',
    'Total.{,4}Package. *',
    'Subtotal.{,2}Order.*Q.{,2}ty.*'
    'SUB-TOTAL',
    'TOTALCustomer',
    'Subtotal_Order_Q\'ty\  .',
    'Total:[0-9\.]*',
    'TOTAL_QUANTITY.*'
    'SAY.{,3}TOTAL.{,3}ONE'
]


class Block():
    def __init__(self, fid, row_order, header_name, header_type, line_content: List[str],
                 line_item: List[NodeItemGroup], update=True):
        self.fid = fid  # fid 记录了field 信息
        self.row_order = row_order
        self.header_name = header_name
        self.header_type = header_type
        self.line_content = line_content
        self.line_item = line_item
        self.node_items = list(chain(*[line.node_items for line in self.line_item]))

        if update:
            self.line_content, self.line_item = self.extract_text_from_node_items(node_items=self.node_items)

    @property
    def bbox(self):
        _bbox: BBox = self.line_item[0].bbox
        for i in range(1, len(self.line_item)):
            _bbox.merge_(self.line_item[i].bbox)
        return _bbox

    @property
    def content(self):
        return self.line_content
    
    def update_line_content(self):
        # 在更新过node_item 相关的信息之后，可以通过这个方法更新行内容
        self.line_content, self.line_item = self.extract_text_from_node_items(node_items=self.node_items)

    def extract_text_from_node_items(self, node_items, thresh=None):
        def h_dis(node1, node2):
            return abs(node1.bbox.cx - node2.bbox.cx)

        def v_algin(node1, node2, thresh):
            if abs(node1.bbox.cy - node2.bbox.cy) < thresh:
                return True
            return False

        if thresh is None:
            thresh = node_items[0].bbox.height // 2

        sorted_nodes = sorted(node_items, key=lambda x: x.bbox.top)
        rows = []
        while len(sorted_nodes) > 0:
            current_row = []
            delete_idxs = []

            node = sorted_nodes[0]
            del sorted_nodes[0]
            current_row.append(node)

            for idx, node in enumerate(sorted_nodes):
                target = sorted(current_row, key=lambda target: h_dis(target, node))[0]
                if v_algin(node, target, thresh):
                    current_row.append(node)
                    delete_idxs.append(idx)
            current_row = sorted(current_row, key=lambda x: x.bbox.left)
            rows.append(current_row)
            delete_idxs = sorted(delete_idxs, key=lambda x: -x)
            for idx in delete_idxs:
                del sorted_nodes[idx]

        row_texts = []
        for row in rows:
            texts = [it.text for it in row]
            split = '_'
            row_text = split.join(texts)
            row_texts.append(row_text)

        return row_texts, [NodeItemGroup(row) for row in rows]


class ElementGroup():
    def __init__(self, cfg, header_type, header_group, fields, rows, keyrow_config, filterrow_config,
                 block_update_config,
                 node_items: Dict[str, NodeItem],
                 company_name=None):
        # 初始化，给出很多表的基本信息
        self.cfg = cfg
        self.header_type = header_type
        self.header_group = header_group
        self.fields: List[Field] = fields
        self.rows = rows
        self.keyrow_config = keyrow_config
        self.keyrow_group = KeyrowGroup(keyrow_config, company_name=company_name)
        self.filterrow_config = filterrow_config
        self.node_items = node_items
        self.block_update_config: set = block_update_config

    @record_time
    def assign_block(self, row_info: Dict[str, str], fields_info: Dict[str, str]):
        """
        这个函数的作用，是对于每一个行抽取一系列的特征
        比如这一行包含了多少的field，之类的
        返回结果：
            block_info: Dict[str,str] ,记录着每个uid 属于哪一个block
            block_list: List[BlockItem] , 每个对应着一系列的nodes，对应的列号(不同的列会被划分为不同的block)


        :param 传入所有的node_item
        :param row_info: 记录着每个node_items 所属的行信息
        :param fields_info:  记录着每个node_items 所属的列信息
        :return:
        """

        # step1 建表
        # uid 是  node_items 的id
        # rid 是  row id，表示这个数据属于哪一行
        # fid 是  field id ，表示这个数据属于哪一个列
        node_info = pd.DataFrame(
            [
                (uid, row_idx, fields_info[uid]) for uid, row_idx in row_info.items()
            ],
            columns=['uid', 'rid', 'fid']
        )
        node_info.index = node_info.uid

        # 做一些相关信息的准备：
        node_info = self.preprocess_node_info(node_info)

        # 对每个行，在每个列涉及到的text 的信息进行记录
        self.row_content_in_each_fields = self.get_row_content_in_each_fields(node_info)

        # 尝试过滤掉表尾部的一些元素
        node_info = self.filter_redudant_content(node_info)

        # step2, 对每个行，检查是否是key row
        # 检查结果更新在node_info 这个dataframe 当中
        find_keyrow, possible_key_row = self.assign_keyrow(node_info)

        # step3，过滤掉possible_key_row 最大的那一个之后的内容
        if find_keyrow:
            start_filter_line = max(possible_key_row)
        else:
            start_filter_line = 0

        node_info, possible_key_row = self.filter_redudant_line(start_filter_line, node_info,
                                                                possible_key_row=possible_key_row)

        if len(self.row_content_in_each_fields) == 0:
            # 说明没有一条有用的记录
            return False, None, None
        # step4 ,如果有 key_row , 则按照key_row , 对node 进行分类
        if find_keyrow and len(possible_key_row) > 0:
            blocks_in_row = self.assign_row_to_block(possible_key_row, node_info)
        else:
            # 认为表头一下只有一行数据
            # 注意，要传入 应该是所有剩余有效行的最小的一行
            first_row_not_redundant = min([self.rows[rid].order for rid in self.row_content_in_each_fields])
            blocks_in_row = self.assign_row_to_block({first_row_not_redundant}, node_info)
            # 对于同一个fields，同一个row 的，会被分为一个block

        return True, possible_key_row, blocks_in_row

    def preprocess_node_info(self, node_info):
        # 获取每个node 的数据
        self.parse_element_info(node_info)
        self.parse_row_info(node_info)
        self.parse_field_info(node_info)
        return node_info

    def parse_element_info(self, node_info):
        node_info.loc[:, 'text'] = node_info.uid.map(lambda x: self.node_items[x].text)
        # node_info.loc[:, 'clean_text'] = node_info.text.map(lambda x: re.sub('[^0-9A-Za-z\-\.]', '', x))
        node_info.loc[:, 'xmin'] = node_info.uid.map(lambda x: self.node_items[x].bbox.left)

        def _text_type(text: str):
            text = text.lower()
            text = text.replace('_', '')
            if re.sub('[^0-9\-\./_]', '', text) == text:
                # 对于 4.23
                return ElementTextType.ALL_NUM
            if re.sub('[0-9]', '', text) == text:
                # 文本当中不存在数字;
                return ElementTextType.ALL_CHAR
            if re.sub('[0-9a-z]', '', text) == text:
                # 文本当中只包含特殊字符
                return ElementTextType.ALL_SPEC

            filter_spec = re.sub('[^0-9a-z]', '', text)
            # 如果filter_spec 前面全是数字，后面全是字母
            if re.match('^[0-9]{1,}[a-z]{1,}$', filter_spec):
                return ElementTextType.NUM2CHAR
            return ElementTextType.MIX_NUM_CHAR

        node_info.loc[:, 'text_type'] = node_info.text.map(lambda x: _text_type(x))

    def parse_row_info(self, node_info):
        # 对row 进行排序，获取row 从上至下的行数
        for idx, (row_id, row) in enumerate(sorted(self.rows.items(), key=lambda x: x[1].bbox.cy)):
            row.order = idx

        node_info.loc[:, 'row_order'] = node_info.rid.map(lambda x: self.rows[x].order)

        # 抽取一些统计信息
        # stats1 ： 每个行，涉及到的列数，总共对应的node 的数量
        node_info.loc[:, 'num_uid_in_row'] = node_info.rid.map(node_info.groupby('rid').uid.count())
        node_info.loc[:, 'num_fid_in_row'] = node_info.rid.map(
            node_info.groupby('rid').fid.apply(lambda x: len(x.unique()))
        )

        # 对row 当中的node_item 按照xmin 进行排序
        for rowid, row_item in self.rows.items():
            row_item.sort(lambda x: x.bbox.rect[0])

    def parse_field_info(self, node_info):
        # 对列，获取header
        node_info.loc[:, 'header_type'] = node_info.fid.map(lambda x: self.fields[x].header.head_type)
        node_info.loc[:, 'header_content'] = node_info.fid.map(lambda x: self.fields[x].header.key_node.content)

    def filter_redudant_content(self, node_info):

        useless_row_id = []
        for filter_config in self.filterrow_config['filter_content']:
            # 遍历所有的过滤配置
            regex_list = filter_config['regex']
            adaptive_fields = filter_config['adaptive_fields']

            for rid, rid_content in self.row_content_in_each_fields.copy().items():
                # 遍历所有的行
                for fid, content_info in rid_content.items():
                    # 遍历这些行涉及到的列
                    header_type = content_info['header_type']
                    if header_type not in adaptive_fields:
                        continue

                    row_content_in_field = content_info['content']
                    # print('debug, ', regex_list, row_content_in_field)
                    useless = False
                    for regex in regex_list:
                        if re.match(regex, row_content_in_field):
                            useless = True
                            break
                    if useless:
                        del self.row_content_in_each_fields[rid]
                        row_order = content_info['row_order']
                        logger.info('{} is not useful'.format(row_content_in_field))
                        useless_row_id.append(row_order)
                        break
        for rid, rid_content in self.rows.copy().items():
            row_content = rid_content.content()
            # print('debugger', row_content)
            need_ignore = False
            for regex in self.filterrow_config['filter_content_in_line']:
                if re.search(regex, row_content, re.IGNORECASE):
                    need_ignore = True
            if need_ignore:
                del self.row_content_in_each_fields[rid]
                useless_row_id.append(rid_content.order)

        useless_row_id = set(useless_row_id)
        if not useless_row_id:
            return node_info

        node_info = node_info[~node_info.row_order.isin(useless_row_id)]
        # TODO: 自适应的去除尾部的内容
        return node_info

    def filter_redudant_line(self, start_filter_line, node_info, possible_key_row=None):
        # 从行的角度筛选数据
        ignore_bg_lines = []
        for idx, (bg_texts, ed_thresh) in enumerate(self.filterrow_config['filter_lines']):
            bg_texts = re.sub('[^0-9A-Za-z]', '', bg_texts).lower()
            self.filterrow_config['filter_lines'][idx] = (bg_texts, ed_thresh)

        # 建立row_order 对于rid 的字典
        row_order_id_map = {self.rows[rid].order: rid for rid in self.row_content_in_each_fields}
        # 按照从小到大排序
        row_order_id_map = OrderedDict(sorted(row_order_id_map.items(), key=lambda x: x[0]))

        after_filter_row = False  # 在一个过滤行之后的所有内容， 会会被过滤掉
        for order, rid in row_order_id_map.items():
            # 遍历每一行

            if after_filter_row:
                ignore_bg_lines.append(order)
                del self.row_content_in_each_fields[rid]
                continue

            row = self.rows[rid]
            if row.order < start_filter_line:
                continue
            row_content = row.content()
            row_content = re.sub('[^0-9A-Za-z]', '', row_content).lower()
            logger.info('this print used to check rows need filter: {}'.format(row_content))
            filtered_by_line_rule = False
            # print('debug',row_content)
            for bg_texts, ed_thresh in self.filterrow_config['filter_lines']:
                dist = ed.eval(row_content, bg_texts)
                if dist < ed_thresh:
                    del self.row_content_in_each_fields[rid]
                    ignore_bg_lines.append(row.order)
                    after_filter_row = True
                    filtered_by_line_rule = True
                    break

            if filtered_by_line_rule:
                # 已经认为是一个需要过滤的行了，这里就不做考虑了
                continue

            for comb in self.filterrow_config['filter_comb']:
                # 拿到每一个comb 的配置
                matched_count = 0
                for header_type_list, regex_config in comb:
                    if isinstance(header_type_list, self.header_group.header_types):
                        header_type_list = [header_type_list]

                    at_least_succeed = False
                    for header_type in header_type_list:
                        # 遍历所有的在这次配置当中的header_type
                        if at_least_succeed:
                            break
                        if isinstance(regex_config, list):
                            # 如果对某个内容配置为list
                            regex_list = regex_config
                            # 获取这一行涉及到的这个类型的type
                            content = [fid_info['content'] for fid, fid_info in
                                       self.row_content_in_each_fields[rid].items()
                                       if fid_info['header_type'] == header_type]
                            for regex in regex_list:
                                if any([re.search(regex, text, re.IGNORECASE) is not None for text in content]):
                                    matched_count += 1
                                    break
                        elif isinstance(regex_config, dict):
                            regex_list = regex_config['content_regex']
                            header_regex_list = regex_config['header_regex']
                            content_list = [(fid, fid_info['content']) for fid, fid_info in
                                            self.row_content_in_each_fields[rid].items() if
                                            fid_info['header_type'] == header_type]

                            # 根据fid ，获取每个content 对应的header 的内容
                            content_list = [(self.fields[fid].header.key_node.content, fid_content) \
                                            for fid, fid_content in content_list]

                            # 从这些content 当中挑选 符合 header_regex_list 的内容
                            content_satisfy_header_regex = []
                            for header_content, field_content in content_list:
                                satisfy_regex = False
                                for header_regex in header_regex_list:
                                    if re.search(header_regex, header_content, re.IGNORECASE):
                                        satisfy_regex = True
                                        break
                                if satisfy_regex:
                                    content_satisfy_header_regex.append(field_content)
                            if len(content_satisfy_header_regex) == 0:
                                # 说明这一行没有一个列满足header_regex 的条件
                                continue
                            for regex in regex_list:
                                if any([re.search(regex, text, re.IGNORECASE) is not None for text in
                                        content_satisfy_header_regex]):
                                    matched_count += 1
                                    at_least_succeed = True
                                    break

                if matched_count == len(comb):
                    logger.info('filtered {} by filter_comb'.format(self.rows[rid].content()))
                    del self.row_content_in_each_fields[rid]
                    ignore_bg_lines.append(row.order)
                    after_filter_row = True
                    break

        node_info = node_info[~node_info.row_order.isin(ignore_bg_lines)]

        if possible_key_row is not None:
            possible_key_row = possible_key_row - set(ignore_bg_lines)
        return node_info, possible_key_row

    def get_row_content_in_each_fields(self, node_info):
        """
        返回的字典记录了每行，在每列的文字信息，以及将每行在每列的node 组合成了一个nodeitemgroup
        """
        row_content_in_each_fields = defaultdict(dict)

        for (rid, fid), data in node_info.groupby(['rid', 'fid']):
            data = data.sort_values(by='xmin')
            row_content = '_'.join(data.text)
            element_group = NodeItemGroup(data.uid.map(lambda x: self.node_items[x]).to_list())
            row_order = data.row_order.values[0]
            for node in element_group.node_items:
                node.row_order = row_order
            header_type = data.header_type.values[0]
            row_content_in_each_fields[rid][fid] = {'header_type': header_type,
                                                    'content': row_content,
                                                    'row_order': row_order,
                                                    'element_group': element_group
                                                    }

        return row_content_in_each_fields

    def assign_keyrow(self, node_info: pd.DataFrame):
        """

        :param node_info: pd.DataFrame , 记录了每个节点的id ， 所属列的id ， 行的id
        :return:
        """
        success, possible_key_row = self.keyrow_group.assign_key_row(node_info, self.fields, self.rows,
                                                                     self.header_group)
        if success:
            return success, possible_key_row

        return False, set()

    @staticmethod
    def load_rule(func_name):
        if isinstance(func_name, str):
            function = getattr(element_common_rules, func_name, None)
            assert function is not None, 'must set right function name {}'.format(func_name)
            return function
        else:
            function = func_name
            return function

    def assign_row_to_block(self, possible_key_row, node_info):
        """
        目的，对数据进行分类
        可以利用的信息 ：
            node_info ： 记录了所有的node_item ，属于哪一行，哪一列，以及其基本属性
            possible_key_row: 记录了哪一行是关键行，一般认为关键行是一个block (一条记录称为一个block)
            self.row_content_in_each_fields: 记录了每行，在每一个fields 当中都拥有什么信息

        最后记录在block 当中的信息，应该类似于一个paragraph
        相当于是所有的在这个block 当中的行，给出content 和 bbox
        然后合并成一个node_item_group， 当然也会同时保持相关的其他信息


        难点：如何完成asssign:
            rule1 : 如果和key_row 完全不相交的，采取向上合并原则
            rule2 : 如果和key_row 有交集的（在y轴上有一定的比例相交），采取就近合并原则
            rule3 : 对于无法处理的情况，在后续考虑通过company_rules 来解决

        :return: node_info: 需要记录每个node_items所属的block id,
                 blocks 记录着每个block 包含了哪些内容
        """
        before_key_row, row_group, row_order_id_map = self.assign_row_to_key_row(possible_key_row)

        row_group = sorted(row_group.items(), key=lambda x: x[0])

        row_group = self.common_filter_total_line(row_group, row_order_id_map)

        blocks_in_row = []
        for row_id, row in row_group:
            auto_remove_tail = False
            if row_id == row_group[-1][0]:
                # 说明是最后一个group
                auto_remove_tail = True
            blocks = self.build_blocks(row_id, row, row_order_id_map, node_info, auto_remove_tail=auto_remove_tail)
            blocks_in_row.append(blocks)

        return blocks_in_row

    def common_filter_total_line(self, row_group, row_order_id_map):
        # 如果只有在最后一组出现了某个行是以total相关的正则表达式开头的，则认为这个total 指的是总计的total
        # 则这个total 之后的内容会过滤
        first_total_appear_id = -1
        first_total_appear_line = 0
        for group_id, group in row_group:
            find_total = False
            for group_idx, row in enumerate(group):
                row_content = self.rows[row_order_id_map[row]].content()

                for total_regex in TOTAL_STATS_REGEX:
                    # print('debug common filter total line', row_content , total_regex ,  re.search(total_regex,row_content))
                    if re.search(total_regex, row_content):
                        find_total = True
                        first_total_appear_line = group_idx
                        break

            if find_total:
                first_total_appear_id = group_id
                break
        # print('debug common filter total line', first_total_appear_id, row_group)
        if first_total_appear_id == row_group[-1][0]:
            # 说明最后一列存在total 的情况
            row_group[-1] = (
                row_group[-1][0],
                row_group[-1][1][:first_total_appear_line]
            )
        if row_group[-1][1] == []:
            row_group = row_group[:-1]
        return row_group

    def assign_row_to_key_row(self, possible_key_row, ):
        """
        :param possible_key_row: 按照key row 分组，将row 分配到不同的keyrow 当中
        :return:
        """
        _BEFORE_ROW = -1
        _AFTER_ROW = 1e4

        # 首先对数据进行排序
        # 注意，这个程序不能反复执行
        possible_key_row = list(possible_key_row)
        possible_key_row.sort()
        # 加入一前以后，便于后面设计算法
        possible_key_row.insert(0, _BEFORE_ROW)
        possible_key_row.append(_AFTER_ROW)

        # 建立row_order 对于rid 的字典
        row_order_id_map = {self.rows[rid].order: rid for rid in self.row_content_in_each_fields}
        # 按照从小到大排序
        row_order_id_map = OrderedDict(sorted(row_order_id_map.items(), key=lambda x: x[0]))

        matched_keyrow = []
        cur_key_row_idx = 0
        for row_order, rid in row_order_id_map.items():
            if row_order == possible_key_row[cur_key_row_idx + 1]:
                cur_key_row_idx += 1
                matched_keyrow.append(possible_key_row[cur_key_row_idx])
            else:
                if possible_key_row[cur_key_row_idx + 1] == _AFTER_ROW:
                    matched_keyrow.append(possible_key_row[cur_key_row_idx])
                else:
                    # 需要计算一下和下一个位置上的key_row 的iou
                    next_keyrow_id = row_order_id_map[possible_key_row[cur_key_row_idx + 1]]
                    if self.judge_intersection(rid, next_keyrow_id):
                        cur_key_row_idx += 1
                    matched_keyrow.append(possible_key_row[cur_key_row_idx])

        before_key_row = []
        row_group = defaultdict(list)
        for row_order, match_id in zip(row_order_id_map.keys(), matched_keyrow):
            if match_id == _BEFORE_ROW:
                before_key_row.append(row_order)
            else:
                row_group[match_id].append(row_order)

        return before_key_row, row_group, row_order_id_map

    def judge_intersection(self, row_id, keyrow_id):
        """
        检查这个行和关键行是否有相交

        :param row_id: 某行的数据的id
        :param keyrow_id: 某个关键行的id
        :return:
        """

        bbox1 = self.rows[row_id].bbox.rect
        bbox2 = self.rows[keyrow_id].bbox.rect

        # 判断y 方向上的iou
        ymin_b1, ymax_b1 = bbox1[1], bbox1[3]
        ymin_b2, ymax_b2 = bbox2[1], bbox2[3]

        iou = (min(ymax_b1, ymax_b2) - max(ymin_b1, ymin_b2)) / (max(ymax_b1, ymax_b2) - min(ymin_b1, ymin_b2))
        iou = max(iou, 0)
        if iou > 0.5:
            return True
        else:
            return False

    def build_blocks(self, row_id, rows, row_order_id_map, node_info, auto_remove_tail=False):
        """
        :param row_id: 关键行的行号
        :param rows:  list of row , 记录着这条记录涉及到的row order
        :param row_order_id_map: row_order 和 row 的关系
        :param node_info:
        :param auto_remove_tail : 对于最后一行设置这个参数为True ，会对最后一行，考虑一些特殊的过滤规则，去除掉表尾部的内容
        :return:
        """
        lines_in_field = defaultdict(list)

        useful_row = [True] * len(rows)
        if auto_remove_tail and len(rows) >= 2:
            # 需要自适应的去除一些不需要的信息
            # rule1  , 计算rows 之间的间隔，如果存在一个很大的间隔，对后面的内容不考虑
            # 拿到每个行的top
            row_bottom = [self.rows[row_order_id_map[rid]].bbox.bottom for rid in rows]
            row_height = [self.rows[row_order_id_map[rid]].bbox.height for rid in rows]
            row_height_diff = np.diff(row_bottom) > 5 * np.mean(row_height)
            after_useless = False
            for idx in range(1, len(rows)):
                if row_height_diff[idx - 1] == True:
                    after_useless = True
                if after_useless == True:
                    useful_row[idx] = False

        for row, is_useful in zip(rows, useful_row):
            if not is_useful:
                continue
            row_info = self.row_content_in_each_fields[row_order_id_map[row]]
            for fid, field_info in row_info.items():
                # header_name = self.fields[fid].header.name
                lines_in_field[fid].append(
                    {
                        'line_item': field_info['element_group'],
                        'line_content': field_info['content']
                    }
                )

        row_info = {}
        for fid, field_info in lines_in_field.items():
            line_content = [line['line_content'] for line in field_info]
            line_item = [line['line_item'] for line in field_info]

            header_name = self.fields[fid].header.name
            header_type = self.fields[fid].header.head_type

            update = False
            if header_type in [self.header_type[htype] for htype in
                               self.cfg.ELEMENT_HANDLER.get('block_update_config', [])]:
                logger.info('set update True for {}'.format(header_type))
                update = True

            row_info[fid] = Block(fid, row_id, header_name, header_type, line_content, line_item, update=update)

        return row_info
