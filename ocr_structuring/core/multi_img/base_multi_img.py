from abc import abstractmethod
from typing import Dict, List

import numpy as np

from ..models.structure_item import StructureItem
from ..utils import str_util
from ..utils.node_item import NodeItem
from ..utils.debug_data import DebugData


class BaseMultiImg:
    subclasses = {}

    # need python 3.6: https://stackoverflow.com/questions/5189232/how-to-auto-register-a-class-when-its-defined
    def __init_subclass__(cls, **kwargs):
        """
        注册所有子类
        """
        super().__init_subclass__(**kwargs)

        parser_name = str_util.camel_to_underline(cls.__name__)
        cls.subclasses[parser_name] = cls

    def __init__(self, template=None, non_template=None):
        self.template = template
        self.non_template = non_template
        pass

    @abstractmethod
    def process(
            self,
            node_items_list: List[Dict[str, NodeItem]],
            images: List[np.ndarray],
            class_name: str,
    ):
        pass

    @abstractmethod
    def supported_class_names(self) -> List[str]:
        pass
