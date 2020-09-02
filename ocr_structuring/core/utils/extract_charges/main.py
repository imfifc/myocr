import json

from .table import find_table_entries
from .rect_data import RectData


def run(filename):
    with open(filename, mode='r', encoding='utf-8') as f:
        labels = json.load(f)

    label_node_list = []
    for label in labels['raw_data']:
        content = label[0]
        rect = [label[1], label[2], label[3], label[4]]
        text_type = label[5]

        d = RectData(rect, content, text_type)
        label_node_list.append(d)

    summary_charges, detail_charges, failures = find_table_entries(label_node_list)
    print("summary charges")
    print(summary_charges)
    print("detail_charges")
    print(detail_charges)
    print("failures")
    print(failures)


if __name__ == '__main__':
    run(filename='./test/0000301353__charges_area_1.txt')
