from ...utils.bbox import BBox
from ...utils.node_item import NodeItem


class Footer:
    def __init__(self, node_items: [NodeItem]):
        self.node_items: [NodeItem] = node_items

    @property
    def bbox(self) -> BBox or None:
        if len(self.node_items) == 0:
            return None
        return BBox.merge_all(*[node_item.bbox for node_item in self.node_items])


