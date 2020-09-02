from typing import List
import numpy as np
from .utils.node_item import NodeItem
from .non_template.main import NoneTemplateStructuring
from .multi_img.main import MultiImgStructuring
from .template.main import TemplateStructuring
from .template.tp_node_item import TpNodeItem
from .utils.debug_data import DebugData
from ..debugger import variables


class Structuring:
    def __init__(self, should_init_tp_structure: bool = True, class_name=None):
        self.non_template = NoneTemplateStructuring()

        if should_init_tp_structure:
            self.template = TemplateStructuring(class_name)
        else:
            self.template = None

        self.multi_img = MultiImgStructuring(self.template, self.non_template)

    def process(self, raw_data: List[List], img: np.ndarray, class_name: str, ltrb=True,
                debug_data: DebugData = None):
        """
        :param raw_data: [text, x1, y1, x2, y2, x3, y3, x4, y4, angle, label, *scores]
        :param img: BGR
        :param class_name:
        :return:
        """
        if class_name in self.non_template.supported_class_names():
            if debug_data:
                debug_data.is_template = False

            node_item_class = NodeItem
            process_func = self.non_template.process
        elif self.template and class_name in TemplateStructuring.supported_class_names():
            if debug_data:
                debug_data.is_template = True

            node_item_class = TpNodeItem
            process_func = self.template.process
        else:
            raise NotImplementedError(f'class_name [{class_name}] is not supported')

        node_items = {}
        for it in raw_data:
            node = node_item_class(it, ltrb)
            node_items[node.uid] = node

        variables.add_group('raw data', 'raw data', [item.raw_node for item in node_items.values()])

        return process_func(node_items, img, class_name, debug_data=debug_data)

    def process_multi(self,
                      raw_datas: List[List[List]],
                      images: List[np.ndarray],
                      class_name: str):
        if class_name not in self.multi_img.supported_class_names():
            raise NotImplementedError(f'class_name [{class_name}] is not supported')

        node_items_list = []
        for raw_data in raw_datas:
            node_items = {}
            for it in raw_data:
                node = NodeItem(it, ltrb=False)
                node_items[node.uid] = node
            node_items_list.append(node_items)

        return self.multi_img.process(node_items_list, images, class_name)

    def supported_class_names(self) -> List[str]:
        return TemplateStructuring.supported_class_names() + self.non_template.supported_class_names()
