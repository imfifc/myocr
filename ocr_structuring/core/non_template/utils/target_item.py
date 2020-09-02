import re
import copy
from enum import Enum, auto

from typing import List, Dict, Optional, Callable

import editdistance

from ocr_structuring.core.utils.debug_data import DebugData
from .bg_item import BgItem
from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.node_item_group import NodeItemGroup
from ocr_structuring.core.utils import str_util
from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.utils.logging import logger


class TargetRegion(Enum):
    """代表前景内容相对于背景字的相对位置"""
    LEFT_TOP = auto()
    MID_TOP = auto()
    RIGHT_TOP = auto()
    RIGHT_MID = auto()
    RIGHT_BOTTOM = auto()
    MID_BOTTOM = auto()
    LEFT_BOTTOM = auto()
    LEFT_MID = auto()


class RegionAnchor(Enum):
    CENTER = auto()
    LEFT_CENTER = auto()


class TargetItem:
    """
    表示非模板结构化中一个 key-value 形式的目标字段
    """

    def __init__(self, name: str, bg_items: List[BgItem], skip_search_by_region=False):
        self.name = name
        self.bg_items = bg_items
        self.skip_search_by_region = skip_search_by_region

        self.node_items = {}
        # 包含所有 node_items 的区域
        self.node_items_area: BBox = None
        self.key_node: NodeItem = None
        self.matched_bg_item: BgItem = None

        self.regions = [TargetRegion.RIGHT_MID]
        self.region_anchor = RegionAnchor.LEFT_CENTER

        self.key_node_x_pading: float = 0
        self.key_node_y_pading: float = 0

    def pre_find_key_node(self, node_items: Dict[str, NodeItem]) -> Dict[str, NodeItem]:
        """
        在 find_key_node 之前调用，如果要修改 node_items 的内容，使用 copy.deepcopy() 拷贝一份
        使用场景：有些背景字包含多余的字符，对匹配造成影响
        :param node_items:
        :return:
        """
        return node_items

    def filter_key_node(self, node_items: Dict[str, NodeItem]) -> Dict[str, NodeItem]:
        """
        在 find_key_node 之前调用过滤 node
        :param node_items:
        :return:
        """
        return node_items

    def post_bg_h_split(self, rest_nodes: List[NodeItem]) -> List[NodeItem]:
        """
        用于过滤 bg split 模式下出来的内容，如果不希望出来的内容放到 node_items 中，则不应该返回
        """
        return rest_nodes

    def find_key_node(self, debug_data: DebugData = None):
        """
        找到背景关键字
        """
        node_items = self.pre_find_key_node(self.node_items)
        node_items = self.filter_key_node(node_items)

        matched_nodes = []
        matched_ed_dist = []
        rest_nodes = []
        for bg_item in self.bg_items:
            if bg_item.mode == BgItem.MATCH_MODE_HORIZONTAL_SPLIT:
                _matched_nodes, _matched_ed_dist, _rest_nodes = bg_item.match(node_items)
                matched_nodes.extend(_matched_nodes)

                _rest_nodes = self.post_bg_h_split(_rest_nodes)

                for rest_node in _rest_nodes:
                    rest_nodes.append(rest_node)

            else:
                _matched_nodes, _matched_ed_dist = bg_item.match(node_items)

                matched_nodes.extend(_matched_nodes)

            matched_ed_dist.extend(_matched_ed_dist)

        rest_nodes = set(rest_nodes)
        for rest_node in set(rest_nodes):
            self.node_items[rest_node.uid] = rest_node

        if debug_data:
            debug_raw_data = []
            for node in rest_nodes:
                debug_raw_data.append([node.text, *node.bbox])
            debug_data.add_rect_group(self.name, 'h split rest nodes', debug_raw_data)

            debug_raw_data = []
            for node in matched_nodes:
                debug_raw_data.append([node.text, *node.bbox])
            debug_data.add_rect_group(self.name,
                                      'all matched key nodes',
                                      debug_raw_data)

        self.key_node = self.decide_key_node(matched_nodes, matched_ed_dist)

        return self.key_node

    def find_key_nodes(self, debug_data: DebugData = None):
        """
        找到所有背景关键字
        """
        node_items = self.pre_find_key_node(self.node_items)
        node_items = self.filter_key_node(node_items)

        matched_nodes = []
        matched_ed_dist = []
        rest_nodes = []
        for bg_item in self.bg_items:
            if bg_item.mode == BgItem.MATCH_MODE_HORIZONTAL_SPLIT:
                _matched_nodes, _matched_ed_dist, _rest_nodes = bg_item.match(node_items)
                matched_nodes.extend(_matched_nodes)

                _rest_nodes = self.post_bg_h_split(_rest_nodes)

                for rest_node in _rest_nodes:
                    rest_nodes.append(rest_node)

            else:
                _matched_nodes, _matched_ed_dist = bg_item.match(node_items)

                matched_nodes.extend(_matched_nodes)

            matched_ed_dist.extend(_matched_ed_dist)

        rest_nodes = set(rest_nodes)
        for rest_node in set(rest_nodes):
            self.node_items[rest_node.uid] = rest_node

        if debug_data:
            debug_raw_data = []
            for node in rest_nodes:
                debug_raw_data.append([node.text, *node.bbox])
            debug_data.add_rect_group(self.name, 'h split rest nodes', debug_raw_data)

            debug_raw_data = []
            for node in matched_nodes:
                debug_raw_data.append([node.text, *node.bbox])
            debug_data.add_rect_group(self.name,
                                      'all matched key nodes',
                                      debug_raw_data)

        return matched_nodes

    def decide_key_node(self, key_nodes: List[NodeItem], ed_dists: List[int]) -> Optional[NodeItem]:
        """
        在 find_key_node 中调用，这个函数应该根据不同字段的需求，最终给出一个 key_node 或者 None
        默认返回编辑距离最小的匹配结果
        :param key_nodes: 匹配到的多个背景字
        :param ed_dists: 每个匹配结果和背景字的编辑距离
        """
        if len(key_nodes) == 0:
            return None

        if len(key_nodes) != len(ed_dists):
            return None

        sorted_key_nodes = sorted(zip(key_nodes, ed_dists), key=lambda x: x[1])
        return sorted_key_nodes[0][0]

    def get_boundary(self) -> Optional[BBox]:
        """
        仅在找到 key_node 时被调用，用于在 search_value_by_region 中确定内容的边界
        """
        pass

    def get_filter_regex(self) -> Optional[str]:
        """
        返回正则表达式，用于在 search_value_by_region 中过滤 node_items，如果返回 None，则不进行正则过滤
        """
        pass

    def filter_node(self, node_item: NodeItem) -> bool:
        """
        用于在 search_value_by_region 中过滤 node_items，如果 True 则过滤掉
        """
        return False

    def search_value_by_region(self,
                               regions: List[TargetRegion],
                               key_nodes: List[NodeItem],
                               key_node_x_pading: float = 0,
                               key_node_y_pading: float = 0,
                               boundary: BBox = None,
                               regex: str = None,
                               region_anchor: RegionAnchor = RegionAnchor.LEFT_CENTER) -> Optional[NodeItemGroup]:
        """
        这个函数设计的不好，regions 的概念没必要，用 search_value_by_boundary

        在关键字周围寻找内容的值，把 key_node 周围的区域划成 9 宫格
        :param regions:  key 对应的值可能存在的位置，以中心点来判断
        :param key_nodes:
        :param key_node_y_pading: 构建 region 时 key_node 区域内 x 方向 padding 的比例，高度的比例
        :param key_node_x_pading: 构建 region 时 key_node 区域内 y 方向 padding 的比例，高度的比例
        :param boundary: 构建 region 时的最大边界，如果为 None，则不限制
        :param regex: 用于过滤 node_items
        :param region_anchor: 判断区域包含条件时以 node_item 的中心点/左侧中心点
                    center: 中心点
                    left_center: 左边中心点


                        ----boundary.top-----
                       |  lt |    mt    | rt |
                       |---------------------|
         boundary.left |  lm | key_node | rm | boundary.right
                       |---------------------|
                       |  lb |    mb    | rb |
                        ---boundary.bottom---
        """
        if self.key_node is None:
            return

        if boundary is None:
            boundary = BBox([0, 0, 1e10, 1e10])

        bbox = copy.deepcopy(self.key_node.bbox)
        bbox.left += key_node_x_pading * bbox.width
        bbox.right -= key_node_x_pading * bbox.width
        bbox.top += key_node_y_pading * bbox.height
        bbox.bottom -= key_node_y_pading * bbox.height

        all_regions = {
            TargetRegion.LEFT_TOP: BBox([boundary.left, boundary.top, bbox.left, bbox.top]),
            TargetRegion.MID_TOP: BBox([bbox.left, boundary.top, bbox.right, bbox.top]),
            TargetRegion.RIGHT_TOP: BBox([bbox.right, boundary.top, boundary.right, bbox.top]),
            TargetRegion.RIGHT_MID: BBox([bbox.right, bbox.top, boundary.right, bbox.bottom]),
            TargetRegion.RIGHT_BOTTOM: BBox([bbox.right, bbox.bottom, boundary.right, boundary.bottom]),
            TargetRegion.MID_BOTTOM: BBox([bbox.left, bbox.bottom, bbox.right, boundary.bottom]),
            TargetRegion.LEFT_BOTTOM: BBox([boundary.left, bbox.bottom, bbox.left, boundary.bottom]),
            TargetRegion.LEFT_MID: BBox([boundary.left, bbox.top, bbox.left, bbox.bottom])
        }

        out = []
        region_bboxs = []
        for region in regions:
            if isinstance(region, list) or isinstance(region, tuple):
                _region = region[0]
                region_anchor = region[1]
            else:
                _region = region
            region_bboxs.append(all_regions[_region])
        for node_item in self.node_items.values():
            if regex and not re.search(regex, node_item.text):
                continue

            if self.filter_node(node_item):
                continue

            if self.key_node.bbox.contain(node_item.bbox):
                continue

            if region_anchor == RegionAnchor.CENTER:
                point = (node_item.bbox.cx, node_item.bbox.cy)
            elif region_anchor == RegionAnchor.LEFT_CENTER:
                point = (node_item.bbox.left, node_item.bbox.cy)
            for region_bbox in region_bboxs:
                if region_bbox.contain_point(point):
                    out.append(node_item)
                    break

        if not out:
            return

        node_item_group = NodeItemGroup(out)
        node_item_group.sort(key=lambda x: x.bbox.cy)

        return node_item_group

    def search_value_by_boundary(self,
                                 key_nodes: List[NodeItem],
                                 boundary: BBox,
                                 region_anchor: RegionAnchor = RegionAnchor.LEFT_CENTER) -> Optional[NodeItemGroup]:
        """
        在关键字周围寻找内容的值
        :param key_nodes:
        :param boundary: 构建 region 时的最大边界，如果为 None，则不限制
        :param region_anchor: 判断区域包含条件时以 node_item 的中心点/左侧中心点
                    center: 中心点
                    left_center: 左边中心点
        """
        if self.key_node is None:
            return

        out = []
        for node_item in self.node_items.values():
            if self.filter_node(node_item):
                continue

            if self.key_node.bbox.contain(node_item.bbox):
                continue

            if region_anchor == RegionAnchor.CENTER:
                point = (node_item.bbox.cx, node_item.bbox.cy)
            elif region_anchor == RegionAnchor.LEFT_CENTER:
                point = (node_item.bbox.left, node_item.bbox.cy)

            if boundary.contain_point(point):
                out.append(node_item)

        if not out:
            return

        node_item_group = NodeItemGroup(out)
        node_item_group.sort(key=lambda x: x.bbox.cy)

        return node_item_group

    def search_value_without_key_node(self) -> Optional[StructureItem]:
        """
        在 key_node 不存在的情况下找结果
        """
        pass

    def output(self, node_item_group: NodeItemGroup, **kwargs) -> Optional[StructureItem]:
        """
        根据 search_value_by_region 或者 search_value_around_key_node 返回的结果输出结构化结果
        :param **kwargs:
        """
        if not node_item_group:
            return

        show_name = self.key_node.cn_text if self.key_node else ''

        join_char = kwargs.get('join_char', '')

        return StructureItem(self.name, show_name, node_item_group.content(join_char=join_char),
                             node_item_group.scores())

    def post_output(self, result: Dict[str, StructureItem]):
        """
        在所有 TargetItem 都掉用完 output 之后调用
        :param result:
        :return:
        """
        pass

    def set_node_items(self, node_items: Dict[str, NodeItem]):
        self.node_items = copy.deepcopy(node_items)
        self.node_items_area = NodeItemGroup(self.node_items).bbox
