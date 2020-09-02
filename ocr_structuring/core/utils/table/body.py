from ...utils.bbox import BBox
from ...utils.node_item import NodeItem


class BodyCell:
    """表体单元格"""

    def __init__(self, node_item: NodeItem or None):
        self.node_item = node_item

    @property
    def bbox(self):
        return self.node_item.bbox

    @property
    def text(self):
        return self.node_item.text

    @property
    def scores(self):
        return self.node_item.scores

    def __str__(self):
        return '{}[{}]'.format(self.node_item.text, self.node_item.bbox)

    def __repr__(self):
        return self.__str__()


class BodyRow:

    def __init__(self, cells: [BodyCell]) -> None:
        self.cells = cells

    @property
    def bbox(self) -> BBox or None:
        bboxes = []
        # TODO: cell不应为None
        for cell in self.cells:
            if not cell:
                continue
            bbox = cell.bbox
            if bbox:
                bboxes.append(bbox)
        if len(bboxes) == 0:
            return None
        return BBox.merge_all(*bboxes)

    def __str__(self):
        return [cell and cell.node_item and cell.node_item.text for cell in self.cells].__str__()

    def __repr__(self):
        return self.__str__()
