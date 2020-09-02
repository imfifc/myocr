from abc import abstractmethod
from typing import Dict, List

import numpy as np

from ..models.structure_item import StructureItem
from ..utils import str_util
from ..utils.node_item import NodeItem
from ..utils.debug_data import DebugData


class BaseNonTemplate:
    subclasses = {}

    # need python 3.6: https://stackoverflow.com/questions/5189232/how-to-auto-register-a-class-when-its-defined
    def __init_subclass__(cls, **kwargs):
        """
        注册所有子类
        """
        super().__init_subclass__(**kwargs)

        parser_name = str_util.camel_to_underline(cls.__name__)
        cls.subclasses[parser_name] = cls

    def __init__(self, debug_data: DebugData = None):
        self.debug_data = debug_data

    @abstractmethod
    def process(self, node_items: Dict[str, NodeItem], img: np.ndarray, class_name: str) -> Dict[str, StructureItem]:
        pass

    @abstractmethod
    def supported_class_names(self) -> List[str]:
        pass

    def supported_codes(self) -> Dict[int, Dict[int, str]]:
        """
        如果想要使用一二级分类，需要在这个函数中返回 class_code 和对应的 class_name
        :return:
        """
        pass
