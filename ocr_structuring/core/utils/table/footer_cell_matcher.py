import re
from typing import Dict

import editdistance
from ...utils.node_item import NodeItem
from ...utils.table.header import HeaderRow


class FooterCell:
    def __init__(self, node_item: NodeItem, confirmed: bool = False):
        self.node_item = node_item
        self.confirmed = confirmed


class FooterCellMatchContext:
    def __init__(self, node_item: NodeItem, header_row: HeaderRow):
        self.node_item = node_item
        self.header_row = header_row


def footer_cell_match(ctx: FooterCellMatchContext) -> bool:
    pass


def match_group(*matchers: [footer_cell_match]) -> footer_cell_match:
    def f(ctx: FooterCellMatchContext) -> footer_cell_match:
        for matcher in matchers:
            if not matcher(ctx):
                return False
        return True

    return f


def keywords_editdistance_match(keywords: Dict[str, int]) -> footer_cell_match:
    """
    有个关键字，有一个匹配上就算成功
    :param keywords: 关键字：最大编辑距离
    :return:
    """

    def f(ctx: FooterCellMatchContext) -> bool:
        for keyword, max_distance in keywords.items():
            if editdistance.eval(ctx.node_item.text, keyword) <= max_distance:
                return True
        return False

    return f


def contains_match(s: str) -> footer_cell_match:
    """
    包含匹配
    :param s:
    :return:
    """

    def f(ctx: FooterCellMatchContext) -> bool:
        return s in ctx.node_item.text

    return f


def contains_any_match(*strs) -> footer_cell_match:
    """
    包含其中任意一个，即算匹配
    :param strs:
    :return:
    """
    def f(ctx: FooterCellMatchContext) -> bool:
        for s in strs:
            if contains_match(s)(ctx):
                return True
        return False
    return f

def regex_match(pattern: str) -> footer_cell_match:
    def f(ctx: FooterCellMatchContext) -> bool:
        return re.match(pattern, ctx.node_item.text) is not None

    return f
