import pkgutil
import numpy as np
from importlib import import_module
from typing import Dict, List
from ocr_structuring.core.multi_img.loader import PROCESSOR_DIR
from ..models.multi_img_result import MultiImgResult
from ..models.structure_result import StructureResult
from ..utils.node_item import NodeItem
from .base_multi_img import BaseMultiImg
from ..utils.debug_data import DebugData


class MultiImgStructuring:
    def __init__(self, template, non_template):
        # 动态加载.
        # processor 中的 modules 必须在其 __init__.py 文件中 import 自己的子类，
        # 否则无法进行注册
        for (_, name, _) in pkgutil.iter_modules([PROCESSOR_DIR]):
            import_module("ocr_structuring.core.multi_img.processor." + name)
        self.processors = {}

        all_class_names = {}
        for processor_name, processor_class in BaseMultiImg.subclasses.items():
            processor = processor_class(template, non_template)
            self.processors[processor_name] = processor

            for class_name in processor.supported_class_names():
                if class_name in all_class_names:
                    raise ValueError(
                        f"{class_name} already exists in processor {all_class_names[class_name]}"
                    )
                all_class_names[class_name] = processor_name

    def process(
            self,
            node_items_list: List[Dict[str, NodeItem]],
            images: List[np.ndarray],
            class_name: str,
    ) -> StructureResult:
        if class_name not in self.supported_class_names():
            raise NotImplementedError(
                f"class_name {class_name} is not implemented in multi img structuring"
            )

        for processor in self.processors.values():
            if class_name in processor.supported_class_names():
                return processor.process(node_items_list, images, class_name)

    def supported_class_names(self) -> List[str]:
        names = []
        for processor in self.processors.values():
            names.extend(processor.supported_class_names())
        return sorted(names)
