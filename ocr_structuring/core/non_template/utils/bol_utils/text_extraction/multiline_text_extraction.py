import re
import uuid

from ocr_structuring.core.non_template.utils.target_item import BgItem
from ocr_structuring.core.utils.node_item import NodeItem


def extract_text_from_multiline_text(text, start_key_words=[], end_key_words=[], start_exps=[], end_exps=[],
                                     start_filter_exps=[], filter_exps=[]):
    node_items = {}
    rows = text.split('\n')
    for idx, row in enumerate(rows):
        node = NodeItem(raw_node=[row, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        node.text_label = idx
        node_items[uuid.uuid1().hex] = node

    # -------------------------------------------
    # 如果设置了 filter_exps ，则优先利用filter_exps 筛选一遍rows
    # -------------------------------------------
    if filter_exps:
        filtered_rows = []
        for row in rows:
            for filter_exp in filter_exps:
                # print('debug filter exps',filter_exp , row , re.search(filter_exp,row))
                if re.search(filter_exp, row, re.IGNORECASE):
                    filtered_rows.append(row)
                    break
        rows = filtered_rows

    start_row = 0
    find_start_row = False
    end_row = len(rows)
    find_end_row = False

    # --------------------------------------------
    # 先根据关键字找起始行
    # --------------------------------------------
    row_num = []
    if len(start_key_words) > 0:
        row_num = find_row_by_key_word(start_key_words, node_items)
        if len(row_num) > 0:
            find_start_row = True
            row_num = sorted(row_num, key=lambda x: x)
            start_row = row_num[0]

    # --------------------------------------------
    # 若未找到则根据正则找起始行
    # --------------------------------------------

    row_num = []
    if len(start_exps) > 0 is not None and not find_start_row:
        for start_exp in start_exps:
            for idx, row in enumerate(rows):
                if re.search(start_exp, row):
                    row_num.append(idx)
                    break
    if len(row_num) > 0:
        find_start_row = True
        row_num = sorted(row_num, key=lambda x: x)
        start_row = row_num[0]

    # --------------------------------------------
    # 先根据关键字找结束行
    # --------------------------------------------

    if len(end_key_words) > 0:
        row_num = find_row_by_key_word(end_key_words, node_items)
        if len(row_num) > 0:
            find_end_row = True
            row_num = sorted(row_num, key=lambda x: x)
            end_row = row_num[0]

    # --------------------------------------------
    # 若未找到则根据正则找结束行
    # --------------------------------------------

    row_num = []
    if len(end_exps) > 0 is not None and not find_end_row:
        for end_exp in end_exps:
            for idx, row in enumerate(rows):
                if re.search(end_exp, row):
                    row_num.append(idx)
                    break
    if len(row_num) > 0:
        find_end_row = True
        row_num = sorted(row_num, key=lambda x: x)
        end_row = row_num[0]

    # --------------------------------------------
    # 根据start_filter_regex,过滤起始行，找到不满足该regex的第一行作为起始行
    # --------------------------------------------
    new_start_row = -1
    for row in range(start_row, end_row):
        filtered = False
        for exp in start_filter_exps:
            # print('debug',row , rows[row],exp,re.search(exp,rows[row],re.IGNORECASE))
            if re.search(exp, rows[row], re.IGNORECASE):
                filtered = True
                break
        if filtered:
            new_start_row = row + 1
        else:
            break
    start_row = new_start_row if new_start_row != -1 else start_row
    # --------------------------------------------
    # 根据起始行结束行，提取text
    # --------------------------------------------
    extract_rows = rows[start_row:end_row]
    return "\n".join(extract_rows), start_row, end_row


def extract_texts_from_paragraph(paragraph, start_key_words=[], end_exps_tuple=[]):
    rows = [it.text for it in paragraph.node_items]
    # 根据正则找最后一行
    find_end_exps = False
    target_row_tuples = []
    for idx, row in enumerate(rows):
        for exp_tuple in end_exps_tuple:
            exps = exp_tuple[0]
            score = exp_tuple[1]
            find_exp = False
            for end_exp in exps:
                if re.search(end_exp, row, re.IGNORECASE):
                    target_row_tuples.append((idx, score))
                    find_exp = True
                    break
            if find_exp:
                break
    row_end_idxs = []
    result = []

    for target_tuple in target_row_tuples:
        end_row_idx = target_tuple[0]
        score = target_tuple[1]

        # 查找结尾行是否包含起始关键字，包含则只保留最后一行，删除第一行
        start_rows = find_row_by_key_word(start_key_words,
                                          list_to_dict(paragraph.node_items[end_row_idx:end_row_idx + 1]))

        start_row_idx = end_row_idx - 1  # 取两行
        if start_row_idx < 0 or (start_row_idx in row_end_idxs) or len(start_rows) > 0:  # 取一行
            start_row_idx = end_row_idx

        row_end_idxs.append(end_row_idx)

        text = '\n'.join(rows[start_row_idx:end_row_idx + 1])
        nodes = paragraph.node_items[start_row_idx:end_row_idx + 1]
        obj = {"start": start_row_idx, "end": end_row_idx + 1, "score": score, "text": text, "nodes": nodes}
        result.append(obj)
    return result


def find_row_by_key_word(bg_texts, node_items):
    # 根据bg_texts生成bg_items
    bg_items = []
    for bg_text in bg_texts:
        if isinstance(bg_text, tuple):
            ed_thresh = bg_text[1]
            bg_text = bg_text[0]
        else:
            ed_thresh = -1

        max_interval = 1 if len(bg_text) <= 3 else 2
        bi = BgItem(bg_text, BgItem.MATCH_MODE_HORIZONTAL_SPLIT, ed_thresh,
                    h_split_pre_func=clean,
                    h_split_max_interval=max_interval)
        bg_items.append(bi)

    # 根据bg_items找到matched_nodes
    matched_nodes = []
    matched_ed_dist = []
    rest_nodes = []

    for bg_item in bg_items:
        if bg_item.mode == BgItem.MATCH_MODE_HORIZONTAL_SPLIT:
            _matched_nodes, _matched_ed_dist, _rest_nodes = bg_item.match(node_items)
            matched_nodes.extend(_matched_nodes)

            for rest_node in _rest_nodes:
                rest_nodes.append(rest_node)

        else:
            _matched_nodes, _matched_ed_dist = bg_item.match(node_items)
            matched_nodes.extend(_matched_nodes)

        matched_ed_dist.extend(_matched_ed_dist)

    row_num = []
    for node in matched_nodes:
        row_num.append(node.text_label)
    return row_num


def clean(text):
    return text.lower()


def list_to_dict(list_data):
    dict_result = {}
    for idx, data in enumerate(list_data):
        dict_result[idx] = data
    return dict_result


def extract_text_from_node_items(node_items, thresh=None):
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
    split = '\n'
    multi_line_texts = split.join(row_texts)
    return multi_line_texts, rows
