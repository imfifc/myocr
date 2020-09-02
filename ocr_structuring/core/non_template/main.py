import pkgutil
import numpy as np
from importlib import import_module
from typing import Dict, List
from ocr_structuring.core.non_template.loader import PROCESSOR_DIR
from ..utils.node_item import NodeItem
from ..non_template.base_non_template import BaseNonTemplate
from ..utils.debug_data import DebugData


class NoneTemplateStructuring:
    def __init__(self, debug_data: DebugData = None):
        # 动态加载.
        # non_template/processor 中的 modules 必须在其 __init__.py 文件中 import 自己的 BaseNonTemplate 子类，
        # 否则无法进行注册
        for (_, name, _) in pkgutil.iter_modules([PROCESSOR_DIR]):
            import_module('ocr_structuring.core.non_template.processor.' + name)
        self.processors = {}

        all_class_names = {}
        for processor_name, processor_class in BaseNonTemplate.subclasses.items():
            processor = processor_class(debug_data)
            self.processors[processor_name] = processor

            for class_name in processor.supported_class_names():
                if class_name in all_class_names:
                    raise ValueError(f'{class_name} already exists in processor {all_class_names[class_name]}')
                all_class_names[class_name] = processor_name

    def process(self, node_items: Dict[str, NodeItem], img: np.ndarray, class_name: str, debug_data: DebugData = None,
                request=None):
        if class_name not in self.supported_class_names():
            raise NotImplementedError(f'class_name {class_name} is not implemented in non template structuring')

        for processor in self.processors.values():
            if class_name in processor.supported_class_names():
                processor.debug_data = debug_data
                if request is None:
                    return processor.process(node_items, img, class_name)
                else:
                    return processor.process(node_items, img, class_name, request=request)

    def supported_class_names(self) -> List[str]:
        names = []
        for processor in self.processors.values():
            names.extend(processor.supported_class_names())
        return sorted(names)
