import re
from typing import Dict

from ...template.tp_node_item import TpNodeItem
from .tp_conf_base_item import TpConfBaseItem


class TpConfAboveItem(TpConfBaseItem):
    def __init__(self, item_conf, is_tp_conf: bool = False):
        super().__init__(item_conf, is_tp_conf)
        self.is_ban_offset = True if item_conf.get("ban_offset", "") == "1" else False
        self.regex = item_conf.get("regex", "")
        self.can_not_miss = item_conf.get("can_not_miss", "")
        self.ioo_thresh = item_conf.get("ioo_thresh", 0.1)

    def match_node(self, node_items: Dict[str, TpNodeItem]) -> TpNodeItem or None:
        """
        在 node_items 中寻找与当前 above_item 匹配的 node
        """
        matched_node_uids = set()
        for node_item in node_items.values():
            if self.check_content_similar(
                node_item.text, remove_space=True, remove_symbols=True
            ):
                matched_node_uids.add(node_item.uid)
                continue

            if self.regex:
                m = re.search(self.regex, node_item.text)
                if m:
                    matched_node_uids.add(node_item.uid)

        matched_node_uids = list(matched_node_uids)
        # TODO 根据某些条件筛选
        if len(matched_node_uids) == 1:
            return node_items[matched_node_uids[0]]
