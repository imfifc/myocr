import numpy as np
from typing import Dict

from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.template.common_parser import CommonParser
from ocr_structuring.core.template.tp_fg_item import FGItem
from ocr_structuring.core.template.tp_node_item import TpNodeItem


class DummyTestParser(CommonParser):
    def tmpl_post_proc(
        self,
        structure_items: Dict[str, StructureItem],
        fg_items: Dict[str, FGItem],
        img: np.ndarray,
    ):
        """
        :param img: 经过roi、旋转、小角度处理后的图片（如果相关模块已启用）
        :param structure_items: dict. key: item_name value: StructureItem
        :return: 与 structure_items 的类型相同，可能会添加新的 item，或者修改原有 item 的值
        :param fg_items: dict. key: item_name.  value: FGItem
        """
        return structure_items

    def _post_func_name(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
    ):
        return "dummy", 1

    def _region_post_func(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
        structure_items: Dict[str, StructureItem],
        *args,
        **kwargs
    ):
        print(item_name)
        pass

    def _region_func_non_exist_region_func(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
        structure_items: Dict[str, StructureItem],
        *args,
        **kwargs
    ):
        print(item_name)
        pass
