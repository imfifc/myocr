from typing import List
from ocr_structuring.core.models.structure_item import SummaryItemContent, DetailItemContent, ChargeItem
from ocr_structuring.core.utils.node_item import NodeItem
from .func import group_into_rows, group_into_tables, classify, \
    divide_into_labels, adjust_label_classifier, merge_labels
from .label import Label
from ocr_structuring.utils.logging import logger

# 在 windows 上如果要直接运行 main.py，请用下面这行 import。
# tensorflow 在 windows 上只支持 python3，目前这个库是 python2 的
# from rect_data import SummaryItemContent, DetailItemContent, ChargeItem


def create_charge_item(content):
    s = content
    if isinstance(content, float) or isinstance(content, int):
        s = str(content)
    scores = [1 for _ in s]
    return ChargeItem(content, scores)


def find_table_entries(rect_data_list: List[NodeItem]) -> (List[SummaryItemContent], List[DetailItemContent]):
    """
    :param rect_data_list: List[NodeItem]
    :return: (List[SummaryItemContent], List[DetailItemContent])
    """
    labels = []


    for label in rect_data_list:
        label = Label(label.text, label.trans_bbox, 1, label.scores)
        adjust_label_classifier(label)
        labels.append(label)

    comma_separated_labels = []
    for label in labels:
        sub_labels, ok = divide_into_labels(label=label, c=',')
        if ok:
            merged_labels = merge_labels(labels=sub_labels)
            comma_separated_labels.extend(merged_labels)
        else:
            comma_separated_labels.append(label)

    space_separated_labels = []
    for label in comma_separated_labels:
        sub_labels, ok = divide_into_labels(label=label, c='_')
        if ok:
            space_separated_labels.extend(sub_labels)
        else:
            space_separated_labels.append(label)
    colon_separated_labels = []
    for label in space_separated_labels:
        sub_labels, ok = divide_into_labels(label=label, c=':')
        if ok:
            merged_labels = merge_labels(labels=sub_labels)
            colon_separated_labels.extend(merged_labels)
        else:
            colon_separated_labels.append(label)

    # 按照y排序
    colon_separated_labels.sort(key=lambda x: x.bbox.center_y())
    # 按照高度分组, 参数代表分离度
    rows = group_into_rows(labels=colon_separated_labels, fraction=0.5)
    # 按照左对齐分块, 参数代表像素点偏移绝对值
    tables = group_into_tables(rows=rows, offset=5)

    summary_labels = []
    detailed_labels = []
    failed_labels = []

    for table in tables:
        for row in table:
            for label in row:
                classify(label)
            row.stat()
            if len(row.names) == 0:
                continue
            # 名字取最靠左边的，最符合阅读习惯
            name_index = row.names[0]
            name = ChargeItem(val=row.labels[name_index].label.name, scores=row.labels[name_index].label.scores)
            # 在名字左边的数字去掉
            amounts = [row.labels[x] for x in row.amounts if x > name_index]
            quantities = [row.labels[x] for x in row.quantities if x > name_index]
            if len(amounts) == 0 == len(quantities):
                continue
            # 只要有小数，就忽略整数
            if len(amounts) == 1:
                l1 = amounts[-1]
                charge = ChargeItem(val=l1.label.name, scores=l1.label.scores)
                summary_labels.append(SummaryItemContent(name=name, charge=charge))
                continue
            if len(amounts) > 1:
                amounts.sort(key=lambda x: x.content)
                l1 = amounts[-1]
                l2 = amounts[-2]
                unit = ChargeItem(val=l2.label.name, scores=l2.label.scores)
                total = ChargeItem(val=l1.label.name, scores=l1.label.scores)
                detailed_labels.append(DetailItemContent(name=name,
                                                         unit_price=unit,
                                                         total_price=total))
                continue
            if len(quantities) == 1:
                l1 = quantities[-1]
                charge = ChargeItem(val=l1.label.name, scores=l1.label.scores)
                summary_labels.append(SummaryItemContent(name=name, charge=charge))
                continue
            if len(quantities) > 1:
                quantities.sort(key=lambda x: x.content)
                l1 = quantities[-1]
                l2 = quantities[-2]
                unit = ChargeItem(val=l2.label.name, scores=l2.label.scores)
                total = ChargeItem(val=l1.label.name, scores=l1.label.scores)
                detailed_labels.append(DetailItemContent(name=name,
                                                         unit_price=unit,
                                                         total_price=total))
                continue
            failed_labels.append(row)
    return summary_labels, detailed_labels, failed_labels
