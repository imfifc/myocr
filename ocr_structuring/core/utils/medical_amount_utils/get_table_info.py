import re
from typing import Dict

from ocr_structuring.core.models.structure_item import StructureItem
from .structure_amount_table import *
from ...utils.crnn import crnn_util


def get_infer_region(table_config, image):
    """

    :param table_config:  config 信息
    :param image:  原始图片
    :return:  返回这个区域在原始图片中的对应区域
    """
    bg_config = table_config.get('template_bg_config', None)
    if not bg_config:
        return None
    else:
        bg_loc = bg_config['loc']
        bg_width = bg_config['width']
        bg_height = bg_config['height']

        x_ratio = bg_width / image.shape[1]
        y_ratio = bg_width / image.shape[0]

        org_loc = [None] * 4
        org_loc[0], org_loc[2] = bg_loc[0] / x_ratio, bg_loc[2] / x_ratio
        org_loc[1], org_loc[3] = bg_loc[1] / x_ratio, bg_loc[3] / x_ratio
        return org_loc


def get_left_table_info(node_items, image, table_config):
    # org_loc = get_infer_region(table_config , image)
    # if org_loc:
    # 如果能找到org_loc ,尝试进行重识别：
    bg_config = table_config.get('template_bg_config', None)

    num_of_rows = len(table_config['left'])

    # 获得模板上，对应的区域，并根据image， 和模板的关系，把这个区域对应回到image中， 并对
    # 在这个区域中的node进行重识别

    left_col = LeftColumn(num_of_rows)
    # 这里有一个问题，就是医疗发票中，有字段 "自付一"，"自付二"，但是自付二容易识别为自付一
    # 这里的解决办法是，将搜索过程改变，同时，在 leftColumn中加入检查机制，将坐标信息明显不对的点去除

    for row_num, rule in enumerate(table_config['left']):
        for rl in rule:
            find = False
            possible_match_node = []
            for row in node_items.values():
                if re.search(rl, row.text):
                    left_node = Node(row, row_num)
                    possible_match_node.append(left_node)
            if possible_match_node:
                match_node = max(possible_match_node, key=lambda x: x.cy)
                left_col._insert_row(left_node)
                find = True
            if find:
                break
    left_col._clean_invalid_row()
    return num_of_rows, left_col


def get_table_info(node_items, table_config, image, thres=0.2, thres_x=4):
    re_recog = table_config.get('re_recog', False)
    num_of_rows, left_col = get_left_table_info(node_items, image, table_config)

    if left_col._get_not_none_row_num() <= 1:
        result = {name: res for name, res in zip(table_config['name'], [None] * num_of_rows)}
        return result

    table_area = list(left_col._get_table_location(thres=thres, thres_x=thres_x))
    # 这里会对area进行一些pad
    # table_height = table_area[3] - table_area[1]
    # # 再稍微扩大一点点
    # pad_height = 0.05 * table_height / 2
    # table_area[1] -= pad_height
    # table_area[3] += pad_height
    right_node = []
    for node in node_items.values():
        if node.trans_bbox.is_center_in(table_area):
            right_node.append(node)

    # 构建右侧列
    right_col = RightColumn(num_of_rows)
    if table_config['right']:
        # 如果配了右侧，就搜索一下右侧的行
        for row_num, rule in enumerate(table_config['right']):
            for rl in rule:
                find = False
                for node in right_node:
                    if re.search(rl, node.text):
                        node = Node(node, row_num)
                        right_col._insert_row(node)
                        find = True
                if find:
                    break
        if right_col._get_not_none_row_num() == 0:
            filter_node = right_col._clean_node_by_rule(right_node)
        else:
            filter_node = right_col._clean_node(right_node)
        matcher = Matcher(num_of_rows, left_col, filter_node, right_col, image, re_recog=re_recog)
        match_res = matcher.matcher()
        result = {name: res for name, res in zip(table_config['name'], match_res)}
    else:
        # 不使用右侧信息
        filter_node = right_col._clean_node_by_rule(right_node)
        if not filter_node:
            match_res = [None] * num_of_rows
        else:
            matcher = Matcher(num_of_rows, left_col, filter_node, right_col, image, re_recog=re_recog)
            match_res = matcher.matcher()
        result = {name: res for name, res in zip(table_config['name'], match_res)}
    return result


def is_three_column(node_items: Dict[str, TpNodeItem]) -> bool:
    three_column_key_words = ['退休', '残军', '单位补', '门诊大额']
    key_words_count = defaultdict(int)
    for it in node_items.values():
        for word in three_column_key_words:
            if word in it.text:
                key_words_count[word] += 1

    return len(key_words_count) >= 1


def delete_extract_items_in_two_column(structure_items: Dict[str, StructureItem]):
    """
    北京门诊下方打印的列会有两列或者三列的情况，模板的配置里是三列的字段配置
    这个函数判断先判断是两列还是三列，如果是两列，则应该删除仅属于三列格式的结构化结果
    :param node_items:
    :return:
    """
    three_column_unique_items = [
        'men_zhen_da_e_zhi_fu',
        'tui_xiu_bu_chong_zhi_fu',
        'can_jun_bu_zhu_zhi_fu',
        'dan_wei_bu_chong_xian_zhi_fu',
        'personal_account_balance'
    ]

    for item_name in three_column_unique_items:
        if item_name in structure_items:
            del structure_items[item_name]


def set_personal_account_pay_money_in_two_column(structure_items: Dict[str, StructureItem]):
    """
    北京门诊、门诊特殊，只有两列的模板中，中间一列没有打印，所以个人账户支付一定为 0.00
    起始从现有的数据看，三列的图片 personal_account_pay_money 也是 0.00，但是业务规则还不确定
    """
    personal_account_pay_money = structure_items.get('personal_account_pay_money')
    if personal_account_pay_money is None:
        return
    personal_account_pay_money.content = '0.00'
    personal_account_pay_money.scores = [1]
