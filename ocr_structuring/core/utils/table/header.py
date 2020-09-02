import sys

from ...utils.bbox import BBox
from ...utils.node_item import NodeItem


class HeaderCell:
    """表头单元格"""

    def __init__(self, name: str, gt_text: str, node_item: NodeItem = None, confirmed: bool = False):
        self.name = name
        self.gt_text = gt_text
        self.node_item = node_item
        self.confirmed = confirmed

    @property
    def bbox(self) -> BBox:
        return self.node_item and self.node_item.bbox

    def __str__(self):
        return '{}[{}][{}]'.format(self.gt_text, self.node_item and self.node_item.text, self.confirmed and '√' or '×')


class HeaderRow:
    """表头行，包含完整的表头，即使对应的node_item还没找到"""

    def __init__(self, names: [str], gt_texts: [str]):
        self.cells = [HeaderCell(names[i], header_text) for i, header_text in enumerate(gt_texts)]

    @property
    def bbox(self) -> BBox or None:
        if len(self.cells) == 0:
            return None
        left = sys.maxsize
        top = sys.maxsize
        right = -1
        bottom = -1
        for cell in self.cells:
            if cell.bbox is None:
                continue
            if cell.bbox.left < left:
                left = cell.bbox.left
            if cell.bbox.top < top:
                top = cell.bbox.top
            if cell.bbox.right > right:
                right = cell.bbox.right
            if cell.bbox.bottom > bottom:
                bottom = cell.bbox.bottom
        return BBox([left, top, right, bottom])

    @property
    def node_items(self) -> [NodeItem]:
        return [cell.node_item for cell in self.cells]

    def __str__(self):
        def get_actual_text(header: HeaderCell):
            if header is None or header.node_item is None:
                return None
            return header.node_item.text

        return ','.join(
            map(lambda x: '{}[{}]'.format(x.gt_text, get_actual_text(x)), self.cells))

