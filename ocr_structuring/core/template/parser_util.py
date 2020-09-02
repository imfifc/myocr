from typing import Dict, List, Tuple

from ..template.tp_node_item import TpNodeItem


def get_regex_max_w(node_items: Dict[int, TpNodeItem], pos='above') -> Tuple[str, List]:
    """
    从 node_items 中获得正则权重最大的 match_regex_result，并返回位置靠上或靠下的
    :param node_items:
    :param pos: above/down
    :return
        text
        scores
    """
    max_regex_w = max(it.get_max_match_regex_w_str().w for it in node_items.values())

    res = []
    for it in node_items.values():
        r = it.get_max_match_regex_w_str()
        if r.w == max_regex_w:
            res.append((it.bbox.cy, r.text, r.scores))

    if pos == 'above':
        res.sort(key=lambda x: x[0])
    elif pos == 'down':
        res.sort(key=lambda x: x[0], reverse=True)
    else:
        raise NotImplementedError('pos not implemented. only support above/down')

    return res[0][1], res[0][2]
