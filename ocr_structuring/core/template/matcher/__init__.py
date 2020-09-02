from typing import Dict

import numpy as np

from ocr_structuring import debugger
from ...template.tp_node_item import TpNodeItem
from ...utils.debug_data import DebugData
from .above_offset import (
    AboveOffset,
    ABOVE_OFFSET_METHOD_IOU,
    ABOVE_OFFSET_METHOD_ANCHOR,
)
from .bg_scale import BgScale

from ...utils.structuring_viz.viz_matcher_process import viz_bg_scale_and_above_offset


class TemplateMatcher:
    def __init__(self, conf):
        self.conf = conf
        self.above_offset_method = conf.get(
            "above_offset_method", ABOVE_OFFSET_METHOD_IOU
        )
        self.bg_scale = BgScale(conf)
        self.above_offset = AboveOffset(conf)

    @viz_bg_scale_and_above_offset
    def process(
        self,
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
        debug_data: DebugData = None,
    ):
        """
        :param node_items:
        :param img: BGR
        :return:
        """
        setattr(self, "debug_data", debug_data)
        img_height, img_width = img.shape[:2]
        self.bg_scale.eval(node_items, img_height, img_width, debug_data=debug_data)

        setattr(self.above_offset, "debug_data", debug_data)
        self.above_offset.eval(
            node_items, img_height, img_width, self.above_offset_method
        )

        def make_debug_raw_data():
            bg_raw_data = []
            above_raw_data = []
            bg_scale_raw_data = []
            above_offset_raw_data = []
            for node in node_items.values():
                if node.is_bg_item:
                    bg_raw_data.append([node.text, *node.bbox])

                if node.is_above_item:
                    above_raw_data.append([node.text, *node.bbox])

                _bbox = node.bg_scaled_bbox if node.bg_scaled_bbox else node.bbox
                bg_scale_raw_data.append([node.text, *_bbox])

                above_offset_raw_data.append([node.text, *node.trans_bbox])
            return bg_raw_data, above_raw_data, bg_scale_raw_data, above_offset_raw_data

        if debug_data:
            (
                bg_raw_data,
                above_raw_data,
                bg_scale_raw_data,
                above_offset_raw_data,
            ) = make_debug_raw_data()
            debug_data.add_rect_group(None, "matched bg item", bg_raw_data)
            debug_data.add_rect_group(None, "matched above item", above_raw_data)
            debug_data.set_bg_scale_result(bg_scale_raw_data)
            debug_data.set_above_offset_result(above_offset_raw_data)

        if debugger.enabled:
            (
                bg_raw_data,
                above_raw_data,
                bg_scale_raw_data,
                above_offset_raw_data,
            ) = make_debug_raw_data()
            # debugger v2
            debugger.variables.add_group(
                "matchedBgBBoxes", "匹配到的背景框", bg_raw_data, "基于模板的方法匹配到的背景框"
            )

            debugger.variables.add_group(
                "matchedAboveBBoxes", "匹配到的前景偏移框", above_raw_data, "基于模板的方法匹配到的前景偏移框"
            )

            debugger.variables.add_group2tpl(
                "bgScaleResultBBoxes", "背景缩放的结果", bg_scale_raw_data, "基于模板的方法背景缩放的结果"
            )

            debugger.variables.add_group2tpl(
                "aboveOffsetResultBBoxes",
                "前景偏移缩放的结果",
                above_offset_raw_data,
                "基于模板的方法前景偏移的结果",
            )

    def get_bg_nodes(
        self,
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
        debug_data: DebugData = None,
    ):
        """
        :param node_items:
        :param img: BGR
        :return:
        """
        setattr(self, "debug_data", debug_data)
        img_height, img_width = img.shape[:2]
        self.bg_scale.eval(node_items, img_height, img_width, debug_data=debug_data)

        setattr(self.above_offset, "debug_data", debug_data)
        self.above_offset.eval(
            node_items, img_height, img_width, self.above_offset_method
        )

        def make_debug_raw_data():
            bg_raw_data = []
            above_raw_data = []
            bg_scale_raw_data = []
            above_offset_raw_data = []
            for node in node_items.values():
                if node.is_bg_item:
                    bg_raw_data.append([node.text, *node.bbox])

                if node.is_above_item:
                    above_raw_data.append([node.text, *node.bbox])

                _bbox = node.bg_scaled_bbox if node.bg_scaled_bbox else node.bbox
                bg_scale_raw_data.append([node.text, *_bbox])

                above_offset_raw_data.append([node.text, *node.trans_bbox])
            return bg_raw_data, above_raw_data, bg_scale_raw_data, above_offset_raw_data

        (
            bg_raw_data,
            above_raw_data,
            bg_scale_raw_data,
            above_offset_raw_data,
        ) = make_debug_raw_data()
        return bg_raw_data
