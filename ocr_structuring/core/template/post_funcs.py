from numpy import ndarray
from typing import Dict

from .tp_node_item import TpNodeItem


def max_w_regex(item_name: str,
                passed_nodes: Dict[str, TpNodeItem],
                node_items: Dict[str, TpNodeItem],
                img: ndarray):
    # 按照最终的权重从大到小排序
    passed_nodes = sorted(passed_nodes.values(), key=lambda x: x.get_final_w(), reverse=True)

    # 找到最终权重最大、相同的节点
    # 在权重相同的节点当中，找出和模板过滤区域 iou 最大的结果
    idx = 0
    largest_iou = float('-inf')
    largest_w = passed_nodes[idx].get_final_w()
    for i in range(0, len(passed_nodes)):
        node = passed_nodes[i]
        if node.get_final_w() != largest_w:
            break

        if len(node.filter_areas) != 1:
            continue

        # TODO 目前只支持一个 filter_area 的判断
        iou = node.trans_bbox.cal_iou(node.filter_areas[0].area)
        if iou > largest_iou:
            largest_iou = iou
            idx = i

    best_rect_data = passed_nodes[idx]

    # 在这里计算最优的passed_nodes的变换后的左上角的值相对于fg_item的filter_area的左上角的值的偏移
    # ideal_loc = self.fg_items[item_name].filter_areas[0].area.rect
    # real_loc = best_rect_data.trans_bbox.rect
    # offset = real_loc[0] - ideal_loc[0], real_loc[1] - ideal_loc[1]
    # self.fg_items[item_name].offset_value = offset

    r = best_rect_data.get_max_match_regex_w_str()
    return r.text, r.scores
