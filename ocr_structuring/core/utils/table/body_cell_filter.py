import re
from typing import Optional, Tuple
from ...utils import str_util
from .footer import Footer
from .header import HeaderRow
from ...utils.node_item import NodeItem


class BodyCellFilterContext:
    """TODO: 传参逻辑与row一致"""

    def __init__(self, node_item: NodeItem, col_index: int, header_row: HeaderRow, footer_row: Footer) -> None:
        self.node_item = node_item
        self.col_index = col_index
        self.header_row = header_row
        self.footer_row = footer_row


def body_cell_filter(ctx: BodyCellFilterContext) -> Optional[NodeItem]:
    pass


def header_below_filter(ctx: BodyCellFilterContext) -> Optional[NodeItem]:
    if ctx.node_item.bbox.is_below(ctx.header_row.cells[ctx.col_index].bbox):
        return ctx.node_item
    return None


def build_regex_exclude_filter(pattern: str) -> body_cell_filter:
    def func(ctx: BodyCellFilterContext) -> Optional[NodeItem]:
        if re.match(pattern, ctx.node_item.text):
            return None
        return ctx.node_item

    return func


def build_remove_symbols_filter(symbols: str) -> body_cell_filter:
    """去除常规的特殊字符和空格"""

    def remove_symbols_filter(ctx: BodyCellFilterContext) -> Optional[NodeItem]:
        # TODO: 不应在filter中修改原始数据
        ctx.node_item.text = str_util.remove_chars(ctx.node_item.text, symbols)
        return ctx.node_item

    return remove_symbols_filter


def build_remove_spec_symbols_filter(excludes: str = '') -> body_cell_filter:
    def f(ctx: BodyCellFilterContext) -> Optional[NodeItem]:
        symbols = str_util.SYMBOL_AND_SPACE_CHARS.copy()
        for c in excludes:
            if c in symbols:
                symbols.remove(c)
        chars = ''.join(symbols)
        # TODO: 不应在filter中修改原始数据
        ctx.node_item.text = str_util.remove_chars(ctx.node_item.text, chars)
        return ctx.node_item

    return f


def build_too_big_box_filter(thresh: Tuple[float, float]):
    """
    构造一个判断是否为大框的过滤器
    :param thresh: (header宽度的倍数， header高度的倍数)
    :return:
    """

    def f(ctx: BodyCellFilterContext) -> Optional[NodeItem]:
        header_cell = ctx.header_row.cells[ctx.col_index]
        # 长宽都大于表头的2倍的，属于大框，去除掉
        if ctx.node_item.bbox.width > header_cell.bbox.width * thresh[
            0] and ctx.node_item.bbox.height > header_cell.bbox.height * thresh[1]:
            return None
        return ctx.node_item

    return f
