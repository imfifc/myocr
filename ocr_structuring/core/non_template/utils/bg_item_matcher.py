import re
from typing import Optional, Dict, Tuple

import editdistance
from pampy import match as pammath

from ocr_structuring.core.utils.node_item import NodeItem


class BgItemMatchContext:
    def __init__(self, node_items: Dict[str, NodeItem], current_item: NodeItem, bg_text: str):
        self.node_items = node_items
        self.current_node = current_item
        self.bg_text = bg_text


def bg_item_match(ctx: BgItemMatchContext) -> Optional[NodeItem]:
    return None


class ItemMatchCfg:
    def __init__(self, name: str, text: str, matcher: bg_item_match) -> None:
        self.name = name
        self.text = text
        self.matcher = matcher


def match_items(node_items: Dict[str, NodeItem], cfgs: [ItemMatchCfg]) -> Dict[str, NodeItem]:
    """
    给定一些配置，返回匹配到的bg_items
    TODO: 返回多个满足条件的
    :param cfgs:
    :param node_items: 所有的node_items
    :param cfg: List套tuple(( item_name, text, bg_item_matcher),)
    :return:
    """
    result_nodes: Dict[str, NodeItem] = {}
    for cfg in cfgs:
        for _, node_item in node_items.items():
            ctx = BgItemMatchContext(node_items, node_item, cfg.text)
            matched_node = cfg.matcher(ctx)
            if matched_node is not None:
                result_nodes[cfg.name] = matched_node
    return result_nodes


# TODO: 使用上面的方法替换
def match_bg_items(node_items: Dict[str, NodeItem], cfg: [Tuple[str, str, bg_item_match]]) -> Dict[str, NodeItem]:
    """
    给定一些配置，返回匹配到的bg_items
    TODO: 返回多个满足条件的
    :param node_items: 所有的node_items
    :param cfg: List套tuple(( item_name, text, bg_item_matcher),)
    :return:
    """
    result_nodes: Dict[str, NodeItem] = {}
    for bg_item_cfg in cfg:
        bg_item_name, text, matcher = bg_item_cfg[0], bg_item_cfg[1], bg_item_cfg[2]
        for _, node_item in node_items.items():
            ctx = BgItemMatchContext(node_items, node_item, text)
            matched_node = matcher(ctx)
            if matched_node is not None:
                result_nodes[bg_item_name] = matched_node
    return result_nodes


def logic_and(*matchers: bg_item_match) -> bg_item_match:
    """
    使用"与"逻辑组合多个matchers，当所有的matchers都匹配时才算匹配成功
    :param matchers:
    :return:
    """

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        result = None
        for matcher in matchers:
            result = matcher(ctx)
            if result is None:
                return None
        return result

    return f


def logic_or(*matchers: bg_item_match) -> bg_item_match:
    """
    使用"或"逻辑组合多个matchers，当任意一个匹配成功时即算匹配成功
    :param matchers:
    :return:
    """
    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        for matcher in matchers:
            result = matcher(ctx)
            if result is not None:
                return result

    return f


def exact_match() -> bg_item_match:
    """精确匹配，文本内容==gt_text"""

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        if ctx.current_node.text == ctx.bg_text:
            return ctx.current_node

    return f


def editdistance_match(max_distance) -> bg_item_match:
    """编辑距离匹配：如果文本内容和gt_text的最大编辑距离<=max_distance，则认为匹配上了"""

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        if editdistance.eval(ctx.current_node.text, ctx.bg_text) <= max_distance:
            return ctx.current_node

    return f


def any_eq_match(*texts: str) -> bg_item_match:
    """和任意一个相等，则认为匹配上了"""

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        for text in texts:
            if text == ctx.current_node.text:
                return ctx.current_node
        return None

    return f


def regex_match(pattern: str) -> bg_item_match:
    """正则匹配"""

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        if re.match(pattern, ctx.current_node.text):
            return ctx.current_node
        return None

    return f


def custom_match(func) -> bg_item_match:
    """
    自定义比较器
    :param func:(node_item, header_cell) -> bool
    :return:
    """

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        return func(ctx.current_node, ctx.bg_text)

    return f


def merge_match(direction, distance_thresh, post_matcher) -> bg_item_match:
    """
    合并匹配器
    :param direction: one of ('TOP'、'BOTTOM'、'LEFT'、'RIGHT')
    :param distance_thresh: 合并时位置距离阈值，是相对于主框高度的倍数
    :param post_matcher: 合并后的后置匹配器
    :return:
    """

    def is_match_direction(main_node: NodeItem, other_node: NodeItem):
        # TODO: 考虑两个框有一点重叠的情况
        return pammath(
            direction,
            'TOP', lambda _: 0 <= main_node.bbox.top - main_node.bbox.bottom <= main_node.bbox.height * distance_thresh,
            'BOTTOM',
            lambda _: 0 <= other_node.bbox.top - main_node.bbox.bottom <= main_node.bbox.height * distance_thresh,
            'LEFT',
            lambda _: 0 <= main_node.bbox.left - other_node.bbox.right <= main_node.bbox.height * distance_thresh,
            'RIGHT',
            lambda _: 0 <= other_node.bbox.left - main_node.bbox.right <= main_node.bbox.height * distance_thresh,
        )

    def merge_nodes(main_node: NodeItem, other_node: NodeItem) -> NodeItem:
        def build_result(node1: NodeItem, node2: NodeItem) -> (str, [float]):
            return node1.text + node2.text, node1.scores + node2.scores

        text, scores = pammath(direction,
                               'TOP',
                               lambda _: build_result(other_node, main_node),
                               'BOTTOM',
                               lambda _: build_result(main_node, other_node),
                               'LEFT',
                               lambda _: build_result(other_node, main_node),
                               'RIGHT',
                               lambda _: build_result(main_node, other_node),
                               )
        bbox = main_node.bbox.merge(other_node.bbox)
        return NodeItem([text, *bbox, main_node.text_label, ])

    def f(ctx: BgItemMatchContext) -> Optional[NodeItem]:
        for _, node_item in ctx.node_items.items():
            if node_item == ctx.current_node:
                continue
            if is_match_direction(ctx.current_node, node_item):
                # merge
                merged_node = merge_nodes(ctx.current_node, node_item)
                old_current_node = ctx.current_node
                ctx.current_node = merged_node
                if post_matcher(ctx):
                    return ctx.current_node
                ctx.current_node = old_current_node
        return None

    return f
