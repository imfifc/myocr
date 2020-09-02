from typing import Optional, Tuple

from ...utils.table.body import BodyRow
from ...utils.table.footer import Footer
from ...utils.table.header import HeaderRow


class BodyRowFilterContext:
    def __init__(self, row: BodyRow, rows: [BodyRow], row_index: int, filtered_rows: [BodyRow], header_row: HeaderRow,
                 footer_row: Optional[Footer]) -> None:
        """

        :param row: 该row是多次过滤处理后的row，可能与原始的rows[row_index]不是同一个
        :param rows: 所有的rows
        :param row_index: 当前处理的row的index
        :param header_row:
        :param footer_row:
        """
        self.row = row
        self.rows = rows
        self.filtered_rows = filtered_rows
        self.row_index = row_index
        self.header_row = header_row
        self.footer_row = footer_row


def body_row_filter(ctx: BodyRowFilterContext) -> Optional[BodyRow]:
    pass


def filter_body_row(row_filters: [body_row_filter], rows: [BodyRow], filtered_rows: [BodyRow], row_index: int, header_row: HeaderRow,
                    footer_row: Optional[Footer]):
    result = rows[row_index]
    ctx = BodyRowFilterContext(result, rows, row_index, filtered_rows, header_row, footer_row)

    for row_filter in row_filters:
        result = row_filter(ctx)
        if not result:
            return None
        ctx.row = result
    return result


def between_header_and_footer_filter(ctx: BodyRowFilterContext) -> Optional[BodyRow]:
    """row的中心点一定在header_row和footer_row之间"""
    if ctx.row.bbox.is_above(ctx.header_row.bbox):
        return None

    if ctx.footer_row and ctx.footer_row.bbox and ctx.row.bbox.is_below(ctx.footer_row.bbox):
        return None

    return ctx.row


def build_above_space_filter(thresh: Tuple[float, float],
                             header_thresh: Tuple[float, float] = None) -> body_row_filter:
    """
    构造一个过滤器，该过滤器会过滤离上一行超过一定高度的行
    :param thresh: 表示中心点距离上一行的最小和最大距离，该值是一个浮点数，是相对于上一行高度的倍数。
    :param header_thresh: 如果是第一行，该参数会当做thresh使用。如果不传递该值或为None，则使用thresh的值
    :return:
    """

    def above_space_filter(ctx: BodyRowFilterContext) -> Optional[BodyRow]:
        if len(ctx.filtered_rows) > 0:
            above_row = ctx.filtered_rows[len(ctx.filtered_rows) - 1]
            min_k = thresh[0]
            max_k = thresh[1]
        else:
            above_row = ctx.header_row
            min_k = header_thresh[0] if header_thresh else thresh[0]
            max_k = header_thresh[1] if header_thresh else thresh[1]

        cy = ctx.row.bbox.center[1]
        y = ctx.row.bbox.top
        above_cy = above_row.bbox.center[1]
        above_y = above_row.bbox.top
        above_h = above_row.bbox.height
        if min_k * above_h <= cy - above_cy <= max_k * above_h or min_k * above_h <= y - above_y <= max_k * above_h:
            return ctx.row
        return None

    return above_space_filter


def build_max_empty_cell_filter(max_empty: int) -> body_row_filter:
    def max_empty_cell_filter(ctx: BodyRowFilterContext) -> Optional[BodyRow]:
        if len(list(filter(lambda x: not x or not x.node_item, ctx.row.cells))) > max_empty:
            return None
        return ctx.row
    return max_empty_cell_filter


def too_high_filter(ctx: BodyRowFilterContext) -> Optional[BodyRow]:
    # 如果row_bbox的高度比上一行的2倍还要大，则认为是乱七八糟行
    if ctx.row_index > 0 and ctx.row.bbox.height > ctx.rows[ctx.row_index - 1].bbox.height * 2:
        return None
    return ctx.row
