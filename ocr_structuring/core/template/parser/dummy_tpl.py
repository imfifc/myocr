from typing import Dict, Tuple, List

from numpy import ndarray

from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.template.common_parser import CommonParser
from ocr_structuring.core.template.tp_fg_item import FGItem
from ocr_structuring.core.template.tp_node_item import TpNodeItem


class DummyTpl(CommonParser):
    def tmpl_post_proc(
        self,
        structure_items: Dict[str, StructureItem],
        fg_items: Dict[str, FGItem],
        img: ndarray,
    ) -> Dict[str, StructureItem]:
        """

        Args:
            structure_items: dict. key: item_name value: StructureItem
            fg_items: dict. key: item_name.  value: FGItem
            img: 经过 roi、旋转、小角度处理后的图片（如果相关模块已启用）

        Returns:
            与 structure_items 的类型相同
        """
        return structure_items

    def _pre_func_dummy(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: ndarray,
    ):
        """
        预处理函数，在 filter_area 和 filter_content 之后调用，主要目的是修改 node_items 中的 text，执行重识别操作等

        Args:
            item_name: 当前正在处理的字段的名称
            passed_nodes: 经过 filter_area 和 filter_content 过滤的 node
            node_items: 所有的 node_items
            img: BGR ndarray

        """
        pass

    def _post_func_dummy(
        self,
        item_name: str,
        passed_nodes: Dict[str, TpNodeItem],
        node_items: Dict[str, TpNodeItem],
        img: ndarray,
    ) -> Tuple[str, List[float]]:
        """
        后处理函数，用于返回某个结构化字段的最终结果
        Args:
            item_name: 当前正在处理的字段的名称
            passed_nodes: 经过 filter_area 和 filter_content 过滤的 node
            node_items: 所有的 node_items
            img: BGR ndarray

        Returns:
            text: 字段结构化结果
            scores: 每个字符的置信度，应该尽量确保长度和 text 的长度一致
        """
        return self._post_func_max_w_regex(item_name, passed_nodes, node_items, img)
