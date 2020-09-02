import editdistance

from ...utils.node_item import NodeItem
from ...utils.table.header import HeaderCell


class HeaderMatchContext:
    def __init__(self, node_items: [NodeItem], current_item: NodeItem, current_header: HeaderCell):
        self.node_items = node_items
        self.current_node = current_item
        self.current_header = current_header


def header_cell_match(ctx: HeaderMatchContext) -> bool:
    return False


def exact_match() -> header_cell_match:
    """精确匹配，文本内容==gt_text"""

    def f(ctx: HeaderMatchContext) -> bool:
        return ctx.current_node.text == ctx.current_header.gt_text

    return f


def editdistance_match(max_distance) -> header_cell_match:
    """编辑距离匹配：如果文本内容和gt_text的最大编辑距离<=max_distance，则认为匹配上了"""

    def f(ctx: HeaderMatchContext) -> bool:
        return editdistance.eval(ctx.current_node.text, ctx.current_header.gt_text) <= max_distance

    return f


def custom_match(func) -> header_cell_match:
    """
    自定义比较器
    :param func:(node_item, header_cell) -> bool
    :return:
    """
    def f(ctx: HeaderMatchContext) -> bool:
        return func(ctx.current_node, ctx.current_header)

    return f
