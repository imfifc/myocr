from typing import Dict, List
from ...template.tp_node_item import TpNodeItem
from ...utils import str_util
from ocr_structuring.utils.logging import logger
from ...utils.node_item_group import NodeItemGroup
from .tp_conf_base_item import TpConfBaseItem

BG_MATCH_MODE_COMMON = "common"
BG_MATCH_MODE_HORIZONTAL_SPLIT = "h_split"
BG_MATCH_MODE_HORIZONTAL_MERGE = "h_merge"
BG_MATCH_MODE_VERTICAL_MERGE = "v_merge"


class TpConfBgItem(TpConfBaseItem):
    def __init__(self, item_conf, is_tp_conf: bool = False):
        super().__init__(item_conf, is_tp_conf)
        self.content = self.contents[0]
        self.mode = item_conf.get("mode", BG_MATCH_MODE_COMMON)
        self.match_func = {
            BG_MATCH_MODE_COMMON: self._norm_match,
            BG_MATCH_MODE_HORIZONTAL_MERGE: self._horizontal_merge_match,
            BG_MATCH_MODE_HORIZONTAL_SPLIT: self._horizontal_split_match,
        }
        assert self.mode in self.match_func.keys(), "current mode is {}".format(
            self.mode
        )

    def _norm_match(self, node_items: Dict[str, TpNodeItem]) -> List[TpNodeItem]:
        out = []
        for node_item in node_items.values():
            if self.check_content_similar(
                node_item.text, remove_space=True, remove_symbols=True
            ):
                out.append(node_item)

        return out

    def _horizontal_split_match(
        self, node_items: Dict[str, TpNodeItem]
    ) -> List[TpNodeItem]:
        norm_match_res = self._norm_match(node_items)
        if len(norm_match_res) != 0:
            return norm_match_res

        # 如果是有编辑距离的设置，则只使用 text 的内容进行 split
        if type(self.content) != str:
            bg_content = self.content["text"]
        else:
            bg_content = self.content

        out = []
        for it in node_items.values():
            sub_str_start_idxes = str_util.findall_sub_str_idx(
                sub_text=bg_content, text=it.text
            )

            if len(sub_str_start_idxes) != 1:
                continue

            start_idx = sub_str_start_idxes[0]
            end_idx = sub_str_start_idxes[0] + len(bg_content)

            if end_idx > start_idx:
                new_node = it.split(start_idx, end_idx)
                if new_node:
                    out.append(TpNodeItem(new_node.gen_ltrb_raw_node()))

        return out

    def _horizontal_merge_match(
        self, node_items: Dict[str, TpNodeItem]
    ) -> List[TpNodeItem]:
        norm_match_res = self._norm_match(node_items)
        if len(norm_match_res) != 0:
            return norm_match_res

        # 如果是有编辑距离的设置，则只使用 text 的内容进行 merge
        if not isinstance(self.content, str):
            bg_content = self.content["text"]
        else:
            bg_content = self.content

        candidate_node_items = {}
        candidate_chars_count = 0

        for node_item in node_items.values():
            if node_item.cn_text in bg_content:
                candidate_node_items[node_item.uid] = node_item
                candidate_chars_count += len(node_item.cn_text)

        # 候选的节点的总长度小于背景的 content 长度，直接返回
        if candidate_chars_count < len(bg_content):
            return []

        line_groups = NodeItemGroup.find_row_lines(candidate_node_items)

        grouped_segs: List[List[NodeItemGroup]] = []
        for group in line_groups:
            segs = group.find_x_segs()
            grouped_segs.append(segs)

        out = []
        for segs in grouped_segs:
            for seg in segs:
                if seg.content() == bg_content:
                    new_node = TpNodeItem(seg.gen_raw_node())
                    out.append(new_node)
                    logger.debug(f"Merge mode bg item match success: {new_node}")

        return out

    def match_node(self, node_items: Dict[str, TpNodeItem]) -> List[TpNodeItem]:
        matched_node_items = self.match_func[self.mode](node_items)
        return matched_node_items

    def __str__(self):
        return f"{self.content} {self.bbox}"
