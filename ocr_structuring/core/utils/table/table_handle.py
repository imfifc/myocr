import re
import sys
import uuid
import copy
import logging

import ocr_structuring.core.utils.bk_tree as bk_tree
import ocr_structuring.core.utils.bk_tree.data as bk_data
from ocr_structuring.core.models.structure_item import SummaryItemContent, ChargeItem, DetailItemContent, \
    SummaryChargeItem
from ocr_structuring.core.utils.extract_charges.func import is_chinese
from ocr_structuring.core.utils.extract_charges.label import TopLabel
from queue import PriorityQueue
from prettytable import PrettyTable
from ocr_structuring.core.utils.nlp.word_classify import gru_model
import ocr_structuring.core.utils.table.table_statistical as table_statistical
from ocr_structuring.core.utils.amount_in_words import cn_amount_util
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def _mean(labels, index):

    temp_label = [label[index] for label in labels if label[index] != sys.float_info.max]
    if len(temp_label) == 0:
        return 0
    return sum(temp_label) / len(temp_label)


class TableStructured(object):

    # detail_bk_tree
    drug_tree = bk_tree.medical_drug_tree
    equi_tree = bk_tree.medical_equi_tree
    exam_tree = bk_tree.medical_exam_tree
    service_tree = bk_tree.medical_service_tree

    # detail_tree 列表
    detail_trees = [drug_tree, exam_tree, equi_tree, service_tree]

    # summary_bk_tree
    summary_tree = bk_tree.summary_charge_item_name

    summary_charges = bk_data.summary_charges

    def __init__(self, passed_nodes, total_summary_money=None, reserve_int=False, filter_bracket=True, statistical_funcs=None, check_summary=True):

        # 原始数据
        self.passed_nodes = passed_nodes

        # 分列结果
        self.col_result = [[]]

        # 分列优先队列
        self.pq_table = [PriorityQueue()]

        # 分行结果
        self.rows = [[]]

        # 总体收费项结果
        self.summary_labels = []

        # 细分收费项结果
        self.detailed_labels = []

        # 细分收费项未矫正结果
        self.origin_detailed_labels = []

        # 识别出来的总金额
        self.total_summary_money = total_summary_money.content if total_summary_money else None

        # 是否保留整数金额
        self.reserve_int = reserve_int

        # 是否检查总体收费项
        self.check_summary = check_summary

        # 用于记录总体收费项金额是否被占用
        self.summary_charges = {}

        # 过滤
        self.detail_name_filter = r'(/[^\u4e00-\u9fa5]*[^/]*)'
        if filter_bracket:
            self.detail_name_filter += r'|(\(.*)'

        self.detail_name_char_filter = r'[^\u4e00-\u9fa5]'
        if not filter_bracket:
            self.detail_name_char_filter = r'[^\u4e00-\u9fa5()]'

        # 最后的统计函数
        if statistical_funcs:
            self.statistical_funcs = statistical_funcs
        else:
            self.statistical_funcs = []

        self.statistical_results = {}

    def structuring(self):
        self.get_cols()
        self.get_rows()
        self.get_entities()
        self.check_charge()
        self.make_summary_charge()

        # 打印结果
        table = PrettyTable(['名称', '单价', '总价'])
        for summary_label in self.summary_labels:
            table.add_row([summary_label.name, '', str(summary_label.charge.val)])

        for detailed_label in self.detailed_labels:
            table.add_row([detailed_label.name, detailed_label.unit_price.val, detailed_label.total_price.val])

        logger.debug(table)

        # 结构化完毕后调用最后的统计函数
        for statistical_func_name in self.statistical_funcs:
            func = getattr(table_statistical, statistical_func_name)
            have, result = func(self.summary_labels, self.detailed_labels, self.origin_detailed_labels)
            if have:
                self.statistical_results[statistical_func_name] = result

    def check_charge(self):
        # 计算平均距离

        if len(self.summary_labels) != 0:
            mean_space = _mean(self.summary_labels, 1)

            for i in range(len(self.summary_labels)):
                (summary_charge, charge_space) = self.summary_labels[i]
                if charge_space >= mean_space * 2:
                    summary_charge.charge.scores = [0]
                    summary_charge.charge.val = 0.0

                self.summary_labels[i] = summary_charge

        if len(self.detailed_labels) != 0:

            unit_mean_space = _mean(self.detailed_labels, 1)

            total_mean_space = _mean(self.detailed_labels, 2)

            for i in range(len(self.detailed_labels)):

                (detail_charge, unit_space, total_space) = self.detailed_labels[i]

                if unit_space >= unit_mean_space * 2:
                    detail_charge.unit_price.scores = [0]
                    detail_charge.unit_price.val = 0

                if total_space >= total_mean_space * 2:

                    detail_charge.total_price.scores = [0]
                    detail_charge.total_price.val = 0.0

                self.detailed_labels[i] = detail_charge

    def make_summary_charge(self):

        # 计算总体收费项总额
        total_charge = sum([float(summary_label.charge.val) for summary_label in self.summary_labels])

        if isinstance(self.total_summary_money, str):
            total_summary_money_check = check_label_money(self.total_summary_money, True)
            self.total_summary_money = float(self.total_summary_money) if total_summary_money_check else cn_amount_util.word2num(self.total_summary_money)

        zero_item = []

        if self.total_summary_money is None:
            return

        # 如果总体收费项相加不等receiptmoney
        if total_charge != self.total_summary_money:

            for summary_label in self.summary_labels:
                scores = sum(summary_label.charge.scores) / len(summary_label.charge.scores)
                if scores == 0:
                    zero_item.append(summary_label)

            if len(zero_item) == 1 and self.total_summary_money - total_charge > 0:
                zero_item[0].charge.val = round(self.total_summary_money - total_charge, 2)
                zero_item[0].charge.scores = [1]

    def get_entities(self):

        # 先定位名称
        for x, row in enumerate(self.rows):
            for y, label in enumerate(row):
                if not self.check_label_name(label.name):
                    continue
                if self.check_summary and self.check_summary_item(label, x, y):
                    continue
                self.check_detail_item(label, x, y)

    def get_rows(self, offset=0.5):
        """
        根据优先队列构造行
        :return:
        """

        # 存储行内元素react总和 用于计算平均值
        compare_react = []

        for pq in self.pq_table:
            row_id = 0
            while not pq.empty():
                item = pq.get()

                # 第一个元素
                if len(self.rows[row_id]) == 0:
                    self.rows[row_id].append(item)
                    compare_react.append(item.bbox.react())

                # 递归的插入
                else:
                    self._find_position(item, row_id, compare_react, offset)

        for row in self.rows:
            row.sort(key=lambda x: x.bbox.left)

    def get_cols(self, spilt_item=True, filters=None):

        """
        根据 passed_node 分列并构造优先队列
        """

        # 过滤
        if filters is None:
            filters = ['打印', '规格', '项目', '单价', '数量', '单位', '金额', '等级']

        # 分割
        sub_nodes = []
        origin_node_ids = []

        if spilt_item:
            for uid, node in self.passed_nodes.items():
                sub_nodes, origin_node_ids = create_node(uid, node, sub_nodes, origin_node_ids)

            for sub_node in sub_nodes:
                uid = uuid.uuid1().hex
                self.passed_nodes[uid] = sub_node

            for uid in origin_node_ids:
                self.passed_nodes.pop(uid)

        col_idx = 0
        compare_left = 0
        sort_result = sorted(self.passed_nodes.items(), key=lambda x: x[1].trans_bbox.left)
        # 根据left分列
        for idx in range(len(sort_result)):
            col = sort_result[idx]

            if len(col[1].text) == 1 and not col[1].text.isdigit():
                continue

            if check(filters, col[1].text):
                continue

            if col[1].text == '':
                continue

            label = TopLabel(col[1].text, col[1].trans_bbox, 1, col[1].scores)

            # 求数组中left均值用于比较
            col_result_len = len(self.col_result[col_idx])
            char_width = get_char_width(col[1])

            # 如果要换下一列
            if col_result_len > 0 and label.bbox.left - (compare_left / col_result_len) > 2 * char_width:

                # 当前列按照y排序
                self.col_result[col_idx].sort(key=lambda x: x.bbox.top)

                self._create_pq(col_idx)

                # 列标号+1
                col_idx += 1
                # 添加列list
                self.col_result.append([])
                # 将label放到下一列
                self.col_result[col_idx].append(label)
                # compare_left初始化(compare_left 记录当前列的总left，用于记录平均)
                compare_left = label.bbox.left
            else:
                compare_left += label.bbox.left
                self.col_result[col_idx].append(label)

        self.col_result[col_idx].sort(key=lambda x: x.bbox.top)
        self._create_pq(col_idx)

    def check_detail_item(self, label, x, y):

        # 先过滤和替换一些特殊符号
        modify = {'（': '(', '）': ')', '_': ''}

        label_name = label.name

        for k, v in modify.items():
            label_name = label_name.replace(k, v)

        # 利用神经网络判断是否为detail_charge_item
        check_result = gru_model.run(label_name)

        if not check_result:
            return

        temp_name = label_name.replace('中药饮片及药材/', '')

        regx = re.compile(self.detail_name_filter)
        temp_name = regx.sub('', temp_name)

        regx = re.compile(self.detail_name_char_filter)
        temp_name = regx.sub('', temp_name)

        bk_check_name = None

        for detail_tree in self.detail_trees:
            bk_check_name = detail_tree().search_one(label_name, search_norm_dist=0.4, min_len=len(temp_name) - 1)
            if bk_check_name:
                break
        temp_name = temp_name if len(temp_name) > 1 else label_name
        temp_name = bk_check_name if bk_check_name else temp_name

        if label_name.strip() != '':
            money, (cur_x, cur_y), money_item = self.find_money(x, y)
            unit = ChargeItem(val=money, scores=money_item.scores)
            unit_space = money_item.bbox.left - label.bbox.left
            unit_space = unit_space if unit_space > 0 else sys.float_info.max
            money, _, money_item = self.find_money(cur_x, cur_y)
            total = ChargeItem(val=money, scores=money_item.scores)
            total_space = money_item.bbox.left - label.bbox.left
            total_space = total_space if total_space > 0 else sys.float_info.max
            name = ChargeItem(val=temp_name, scores=label.scores)
            origin_name = ChargeItem(val=label_name, scores=label.scores)
            self.detailed_labels.append((DetailItemContent(name=name, unit_price=unit, total_price=total), unit_space, total_space))
            self.origin_detailed_labels.append(DetailItemContent(name=origin_name, unit_price=unit, total_price=total))

    def check_summary_item(self, label, x, y):
        # summary 的时候过滤掉英文和数字
        text = re.sub('[0-9A-Za-z_.]', '', label.name)
        bk_name = TableStructured.summary_tree().search_one(text, min_len=len(text) - 1, search_dist=len(text)//2)
        if bk_name:
            money, (x, y), money_item = self.find_money(x, y-1, split_money=True)
            charge = SummaryChargeItem(val=money, scores=money_item.scores, x=x, y=y)
            name = ChargeItem(val=bk_name, scores=label.scores)
            space = money_item.bbox.left-label.bbox.left
            space = space if space >= 0 else sys.float_info.max
            summary_item_content = SummaryItemContent(name=name, charge=charge)
            # 如果之前金额被占用了，则把占用该金额的项金额置空
            if self.summary_charges.get(charge):
                self.summary_charges[charge].charge = SummaryChargeItem(val=0, scores=[0], x=-1, y=-1)
            self.summary_charges[charge] = summary_item_content
            self.summary_labels.append((summary_item_content, space))
            return True

        return False

    def _find_position(self, item, row_id, compare_react, offset=0.5):
        """
        递归找寻当前item 在rows中的位置
        一共有三种情况，在当前行，在当前行的上位置或下位置
        :param compare_react: 记录行总react数据 顺序为 left, top, right, bottom
        :param row_id: 行号id
        :param item: 当前
        :return: 当前item所在row_id 因为下一个元素一定在当前元素的右下方
        """
        # 如果需要新建一行
        if row_id >= len(self.rows):
            self.rows.append([item])
            compare_react.append(item.bbox.react())
            return row_id

        row_mean_top = compare_react[row_id][1] / len(self.rows[row_id])
        row_mean_bottom = compare_react[row_id][3] / len(self.rows[row_id])
        top_offset = item.bbox.top - row_mean_top

        # 如果在当前行 或下一行
        if abs(top_offset) <= offset * (row_mean_bottom - row_mean_top):

            self.rows[row_id].append(item)
            compare_react[row_id] += item.bbox.react()

            return row_id

        # 如果在当前行的上一行
        elif top_offset < 0 and abs(top_offset) > (row_mean_bottom - row_mean_top) * offset:
            self.rows.insert(row_id, [item])
            compare_react.insert(row_id, item.bbox.react())

        else:
            row_id = self._find_position(item, row_id + 1, compare_react, offset)

        return row_id

    def find_money(self, x, y, split_money=False):
        """
        根据当前item找到金额
        :param split_money:
        :param x:
        :param y:
        :return:
        """
        filter_regx = r'[￥Y_，\,元]'
        count = 0
        while True:
            count += 1
            if len(self.rows[x]) > y+1:
                y += 1
            else:
                item = copy.deepcopy(self.rows[x][y])
                item.scores = [0]
                item.val = 0
                item.bbox.left = sys.float_info.max
                return 0, (x, y), item

            money = self.rows[x][y].name
            if split_money and count == 1:
                money = re.sub(r'[^\w_.]', '', money)
            money = re.sub(filter_regx, '', money)

            if check_label_money(money, self.reserve_int):
                # 如果金额与名字连在一起，则分割一下
                if split_money and count == 1:
                    split = copy.deepcopy(self.rows[x][y])
                    split.bbox.left = self.rows[x][y].bbox.right
                    split.bbox.right = 2 * self.rows[x][y].bbox.right - self.rows[x][y].bbox.left
                    return money, (x, y), split

                return money, (x, y), self.rows[x][y]

    def _create_pq(self, col_idx):
        # 将当前列按照y值放入优先队列中
        for i in range(len(self.col_result[col_idx])):
            if i + 1 > len(self.pq_table):
                self.pq_table.append(PriorityQueue())

            col_label = self.col_result[col_idx][i]
            self.pq_table[i].put(col_label)

    def check_label_name(self, txt):
        """
        检查是否为一个表格项
        :param txt:
        :return:
        """
        length = 0

        if txt in TableStructured.summary_charges():
            return True

        filters = ['付', '_付', '付_']
        re_filters = ['自付', '自村', '无自']
        re_temp = [f for f in re_filters if txt != '自付药' and re.search(f, txt)]
        temp = [f for f in filters if f == txt]

        if len(temp) > 0 or len(re_temp) > 0:
            return False

        for t in txt:
            if is_chinese(t):
                length += 1

        return length >= 3


def check(filters, txt):
    """
    是否满足过滤规则
    :param filters:
    :param txt:
    :return:
    """
    for f in filters:
        if re.search(f, txt):
            return True
    return False


def get_char_width(node):
    # 根据测试，不管是什么字符都占用1个单位的空间
    length = len(node.text)

    if length == 0:
        return 0

    return (node.trans_bbox.right - node.trans_bbox.left) / length


def create_node(uid, node, sub_nodes, origin_node_ids):
    """
    node 分割
    :param uid:
    :param node:
    :param sub_nodes:
    :param origin_node_ids:
    :return:
    """
    regex = '_{2,}|有|无?自?付_|-{2,}'
    result = re.split(regex, node.text)
    split_lengths = [len(char) for char in re.findall(regex, node.text)]
    char_width = get_char_width(node)

    left = node.trans_bbox.left

    # 说明需要分隔
    if len(result) > 1:
        origin_node_ids.append(uid)
        for i in range(len(result)):
            n = result[i]

            if n == '':
                continue

            # 根据测试，不管是什么字符都占用1个单位的空间
            length = len(n) * char_width

            sub_node = copy.deepcopy(node)

            sub_rect = [left, sub_node.trans_bbox.top, left + length, sub_node.trans_bbox.bottom]

            sub_node.trans_bbox.update(sub_rect)

            sub_node.text = n

            if i < len(result) - 1:
                left = sub_node.trans_bbox.right + split_lengths[i] * char_width

            sub_nodes.append(sub_node)

    return sub_nodes, origin_node_ids


def check_label_money(txt, reserve_int=False):
    """
    检查是否是金额
    :param txt:
    :param reserve_int: 是否保留整数金额
    :return:
    """
    if len(txt) == 0:
        return False

    txt = txt.replace('_', '')
    regex = '^([0-9,]{1,}[.][0-9]{1,4})$'
    if reserve_int:
        regex = '^([0-9,]{1,}([.][0-9]{1,4})?)$'
    if re.match(regex, txt):
        return True
    return False
