import re
from itertools import product
from typing import Dict

import pandas as pd

from ocr_structuring.core.utils.node_item import NodeItem
# ----------------------------------
# matched rule
# -----------------------------------
from ocr_structuring.utils.logging import logger


def common_matched_rule(node1, node2, node_in_row1: pd.Series, node_in_row2: pd.Series,
                        node_items: Dict[str, NodeItem], rows, fields: Dict):
    """
    遵循一定的原则，判断对应的两行是否是匹配的


    """
    row1_fid_set = set(node_in_row1.fid)
    row2_fid_set = set(node_in_row2.fid)

    # 原则,两行存在两个以上的位置是"对应的":即存在两个位置的 文本类型是对应的，且bbox 是对应的
    matched_fields_count = 0
    for fid in row1_fid_set | row2_fid_set:
        nodes_in_fields_1 = node_in_row1[node_in_row1.fid == fid]
        nodes_in_fields_2 = node_in_row2[node_in_row2.fid == fid]

        # 在每个fields 中，至少存在一个match 的组合
        matched_text = []
        has_matched = False
        for comb in product(nodes_in_fields_1.iterrows(), nodes_in_fields_2.iterrows()):
            node_in_f1 = node_items[comb[0][1].uid]
            node_in_f2 = node_items[comb[1][1].uid]

            min_height = (node_in_f1.bbox.height + node_in_f2.bbox.height) / 2

            align_ratio = min(abs(node_in_f1.bbox.cx - node_in_f2.bbox.cx),
                              abs(node_in_f1.bbox.left - node_in_f2.bbox.left),
                              abs(node_in_f1.bbox.right - node_in_f2.bbox.right)
                              ) / min_height
            if align_ratio < 0.1:
                has_matched = True
                matched_text = [node_in_f1.text, node_in_f2.text]
                break
        if has_matched:
            logger.info('row {} , {} matched in  {}'.format(node1.text, node2.text, matched_text))
            matched_fields_count += 1

    logger.info(
        'matched_fields_count is {} for node {} and node {} , thres is {}'.format(matched_fields_count, node1.text,
                                                                                  node2.text,
                                                                                  max(2, node1.num_fid_in_row - 1)))
    if matched_fields_count >= max(2, node1.num_fid_in_row - 1):
        return True

    return False


# ----------------------------------
# re rule 1 :
# LINE | CARTON_NO
#   1  |  02-03
#   2  |  04
# -----------------------------------


# rule1
def re_func_for_cno1(x: str):
    """

    :param x: 判断 x 是否满足 02-03 的情况
    :return:
    """
    x = re.sub('[^0-9\-]', '', x)
    if not x:
        return False
    if re.match('[0-9]{,3}\-[0-9]]{,3}', x) or re.match('[0-9]+', x):
        return True
    return False


def increasing_func_for_cno1(x: str, y: str):
    x = re.sub('[^0-9\-]', '', x)
    y = re.sub('[^0-9\-]', '', y)

    if not x or not y:
        return False
    x_last = x.split('-')[-1]
    y_first = y.split('-')[0]

    if not x_last or not y_first:
        return False
    if int(y_first) - int(x_last) == 1:
        return True
    return False


# ----------------------------------
# re rule 2 :
# LINE | CARTON_NO
#   1  |  2/3
#   2  |  3/3
# -----------------------------------

def re_func_for_cno2(x: str):
    # 判断 x 是否满足 02/03 - 03/03
    x = re.sub('[^0-9/\-]', '', x)
    if not x:
        return False
    if re.match('[0-9]{,3}/[0-9]{,3}', x):
        return True
    if re.match('([0-9]{,3}/[0-9]{,3})-([0-9]{,3}/[0-9]{,3})', x):
        return True
    return False


def increasing_func_for_cno2(x: str, y: str):
    x = re.sub('[^0-9/\-]', '', x)
    y = re.sub('[^0-9/\-]', '', y)

    if not x or not y:
        return False

    x_last = x.split('-')[-1]
    y_first = y.split('-')[0]

    x_split = x_last.split('/')
    y_split = y_first.split('/')

    x_split = [text for text in x_split if text != '']
    y_split = [text for text in y_split if text != '']

    if not len(x_split) == 2 or not len(y_split) == 2:
        return False

    if int(y_split[1]) != int(x_split[1]):
        return False

    if int(y_split[0]) - int(x_split[0]) == 1:
        return True
    return False


# ----------------------------------
# re rule 3 :
# LINE | CARTON_NO
#   1  |  2/3
#   2  |  3/3
# -----------------------------------

def re_func_for_cno3(x: str):
    # 判断 x 是否满足 1-9
    x = re.sub('[^0-9\-]', '', x)
    if not x:
        return False
    if re.match('[0-9]{1,4}\-[0-9]{1,4}', x):
        return True
    return False


def increasing_func_for_cno3(x: str, y: str):
    x = re.sub('[^0-9/\-]', '', x)
    y = re.sub('[^0-9/\-]', '', y)

    if not x or not y:
        return False

    x_last = x.split('-')[-1]
    y_first = y.split('-')[0]
    if int(y_first) - int(x_last) == 1:
        return True
    return False


# ----------------------------------
# re rule 4 :
# LINE |  PO_NO
#   1  |  9999999901
#   2  |  9999999902
# -----------------------------------

def re_func_for_po1(x: str):
    x = re.sub('[^0-9]', '', x)
    if len(x) == 10:
        return True
    else:
        return False


def increasing_func_for_po1(x: str, y: str):
    x = re.sub('[^0-9]', '', x)
    y = re.sub('[^0-9]', '', y)
    if int(y) - int(x) == 1:
        return True
    else:
        return False


# ----------------------------------
# re rule 5 :
# LINE | LINE_NO
#   1  | 3.1
#   2  | 4.1
# -----------------------------------
def re_func_for_line_no1(x: str):
    x = re.sub('[^0-9\.]', '', x)
    if not x:
        return False
    if re.match('[0-9]{1,}\.[0-9]{1,}', x):
        return True
    else:
        return False


def increasing_func_for_line_no1(x, y):
    x_split = x.split('.')
    y_split = y.split('.')

    if x_split[-1] == y_split[-1] and (int(y_split[0]) - int(x_split[0])) == 1:
        return True
    else:
        return False
