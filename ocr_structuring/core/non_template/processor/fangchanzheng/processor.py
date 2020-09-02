'''from typing import List, Dict, Optional
import numpy as np

from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.non_template.base_non_template import BaseNonTemplate
from ocr_structuring.core.non_template.utils.bg_item import BgItem
from ocr_structuring.core.non_template.utils.target_item import TargetItem
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.debug_data import DebugData
from ocr_structuring.core.utils.node_item import NodeItem


class FangChanZhengProcessor(BaseNonTemplate):
    def __init__(self, debug_data: DebugData = None):
        super().__init__(debug_data)
        self.target_nodes = self.init_target_nodes()
    
    # def init_target_nodes(self) -> Dict[str, TargetItem]:
    #     keys = [
    #     (
    #         target_names.invoiceNum,['发票号码', 'No', 'NO', 'N0'],InvoiceNumTargetItem, BgItem.MATCH_MODE_HORIZONTAL_SPLIT
    #     )]
    #     out = {}
    #     for it in keys:
    #         name, bg_texts, target_item_class, merge_mode = it
    #         # skip_search = True if name == target_names.totalTax else False
    #         skip_search = False

    #         bg_items = []
    #         for bg_text in bg_texts:
    #             if isinstance(bg_text, tuple):
    #                 ed_thresh = bg_text[1]
    #                 bg_text = bg_text[0]
    #             else:
    #                 ed_thresh = -1
    #             h_split_max_interval = 1
    #             if name == target_names.sellerAddressPhone or name == target_names.purchaserAddressPhone:
    #                 h_split_max_interval = 2
    #             bg_items.append(BgItem(bg_text, merge_mode, ed_thresh, h_split_max_interval=h_split_max_interval))

    #         out[name] = target_item_class(name,
    #                                       bg_items,
    #                                       skip_search_by_region=skip_search)
    #     return out
        


    def supported_class_names(self) -> List[str]:
        return ["non_tpl"]

    def process(
            self,
            node_items: Dict[str, NodeItem],
            img: Optional[np.ndarray],
            class_name: str,
    ) -> Dict[str, StructureItem]:
        return {}
       
'''