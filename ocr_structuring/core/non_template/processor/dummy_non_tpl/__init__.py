from typing import List, Dict, Optional
import numpy as np

from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.non_template.base_non_template import BaseNonTemplate
from ocr_structuring.core.non_template.utils.bg_item import BgItem
from ocr_structuring.core.non_template.utils.target_item import TargetItem
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.debug_data import DebugData
from ocr_structuring.core.utils.node_item import NodeItem


class MoneyTargetItem(TargetItem):
    pass


class DummyProcessor(BaseNonTemplate):
    def __init__(self, debug_data: DebugData = None):
        super().__init__(debug_data)
        bg_item = BgItem("金额", BgItem.MATCH_MODE_COMMON)
        self.money_target_item = MoneyTargetItem("金额", [bg_item])

    def supported_class_names(self) -> List[str]:
        return ["dummy_non_tpl"]

    def process(
        self,
        node_items: Dict[str, NodeItem],
        img: Optional[np.ndarray],
        class_name: str,
    ) -> Dict[str, StructureItem]:
        """示例图片可以看 core/template/config/dummy_tpl.jpg """

        # set_node_items 会拷贝一份 node_items，每个 target item 维护自己的 node_items
        self.money_target_item.set_node_items(node_items)

        # 找到关键背景字
        key_node = self.money_target_item.find_key_node()
        if key_node is None:
            return {"money": StructureItem("money", "金额", "1", [1])}

        # 设定前景内容提取的返回，这里是设定在 key_node 的右侧区域
        boundary = BBox(
            [
                key_node.bbox.right,
                key_node.bbox.top,
                key_node.bbox.right + key_node.bbox.height * 5,
                key_node.bbox.top + key_node.bbox.height,
            ]
        )

        # 获得 boundary 区域内的候选结果
        node_item_group = self.money_target_item.search_value_by_boundary(
            None, boundary
        )

        if node_item_group is None:
            return {"money": StructureItem("money", "金额", "1", [1])}

        # 返回最终输出
        result_node = node_item_group.node_items[0]

        return {
            "money": StructureItem("money", "金额", result_node.text, result_node.scores)
        }
