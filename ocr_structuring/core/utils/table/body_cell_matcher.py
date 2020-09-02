from typing import Tuple

from ...utils.table.footer import Footer
from ...utils.table.header import HeaderCell
from .body import BodyCell


class BodyCellMatchContext:
    def __init__(self, body_cell: BodyCell, above_cell: BodyCell,  header_cell: HeaderCell, footer: Footer):
        self.header_cell = header_cell
        self.body_cell = body_cell
        self.above_cell = above_cell
        self.footer = footer


def body_cell_match(ctx: BodyCellMatchContext) -> bool:
    return False


def vertical_same_line_match(thresh: float = 0.5) -> body_cell_match:
    """
    垂直方向共线
    :param thresh: 最大水平偏差为表头文字宽度的多少倍
    :return:
    """

    def f(ctx: BodyCellMatchContext) -> bool:
        bbox = ctx.body_cell.bbox
        header_bbox = ctx.header_cell.bbox
        return abs(bbox.center[0] - header_bbox.center[0]) <= header_bbox.width * thresh

    return f


def vertical_above_same_line_match(thresh: float = 0.5) -> body_cell_match:
    """
    与上面的cell在垂直方向共线
    :param thresh: 最大水平偏差为表头文字宽度的多少倍
    :return:
    """
    def f(ctx: BodyCellMatchContext) -> bool:
        bbox = ctx.body_cell.bbox
        above_bbox = ctx.above_cell.bbox if ctx.above_cell else ctx.header_cell.bbox
        return abs(bbox.center[0] - above_bbox.center[0]) <= above_bbox.width * thresh

    return f


def below_header_match(thresh: float = 0.5) -> body_cell_match:
    """
    在对应的header下方
    :param thresh:
    :return:
    """

    def f(ctx: BodyCellMatchContext) -> bool:
        bbox = ctx.body_cell.bbox
        header_bbox = ctx.header_cell.bbox
        return header_bbox.is_above(bbox, thresh)

    return f


def center_above_footer_match() -> body_cell_match:
    """
    中心点在footer的top之上
    # TODO: footer点最近的表头到footer点的距离与当前点到当前表头的距离
    :return:
    """
    def f(ctx: BodyCellMatchContext) -> bool:
        if not ctx.footer or not ctx.footer.bbox:
            return True
        bbox = ctx.body_cell.bbox
        footer_bbox = ctx.footer.bbox
        return bbox.center[1] < footer_bbox.top + bbox.height / 2

    return f


def size_match(width: Tuple[float, float], height: Tuple[float, float]) -> body_cell_match:
    """
    大小匹配
    :param width: body_cell的宽度是表头宽度的(最小， 最大)倍数
    :param height: body_cell的高度是表头宽度的(最小， 最大)倍数
    :return:
    """
    def f(ctx: BodyCellMatchContext) -> bool:
        bbox = ctx.body_cell.bbox
        header_bbox = ctx.header_cell.bbox
        return header_bbox.width * width[0] <= bbox.width <= header_bbox.width * width[1] \
               and header_bbox.height * height[0] <= bbox.height <= header_bbox.height * height[1]

    return f
