# encoding=utf-8

import difflib
import math
import re
from collections import defaultdict
from typing import List, Dict, Set, Tuple
from ...utils.bbox import BBox
from ...template.tp_node_item import TpNodeItem
from ocr_structuring.utils.logging import logger
from .tp_conf_above_item import TpConfAboveItem
from ...utils.debug_data import DebugData
from ...utils.structuring_viz.viz_matcher_process import viz_above_item_offset_iou

ABOVE_OFFSET_METHOD_IOU = 'iou'
ABOVE_OFFSET_METHOD_ANCHOR = 'anchor'


class AboveOffset:
    def __init__(self, conf):
        self.above_items = {}
        is_tp_conf = conf['is_tp_conf']
        for item_conf in conf.get('above_items', []):
            above_node = TpConfAboveItem(item_conf, is_tp_conf)
            self.above_items[above_node.uid] = above_node

    @viz_above_item_offset_iou
    def eval(self, node_items: Dict[str, TpNodeItem],
             img_height: int,
             img_width: int,
             offset_method: str = ABOVE_OFFSET_METHOD_IOU):
        """
        修改 node_item 中的 trans_box 坐标
        :param node_items:
        :param offset_method:
            - anchor
            - iou
        :return:
        """
        if len(self.above_items) == 0:
            return

        ban_offset_uids = self.sign_ban_offset(node_items, self.above_items)

        if offset_method == ABOVE_OFFSET_METHOD_ANCHOR:
            new_offset = self.above_offset_by_anchor(node_items)
            logger.debug('Do above_offset by ANCHOR')
        elif offset_method == ABOVE_OFFSET_METHOD_IOU:
            content_similarity = self.cal_content_similarity(node_items)
            new_offset = self.iou_block_search(content_similarity, node_items, ban_offset_uids)
            logger.debug('Do above_offset by IOU')
        else:
            raise NotImplementedError(f'above_offset offset_method [{offset_method}] is not implemented')

        logger.debug(f'above_offset value: {new_offset}')

        for uid, node_item in node_items.items():
            if uid in ban_offset_uids:
                continue

            bb = node_item.trans_bbox.transform((-new_offset[0], -new_offset[1]))
            node_item.above_offset_bbox = bb

    def above_offset_by_anchor(self, node_items: Dict[str, TpNodeItem]):
        match_pairs = []
        for above_item in self.above_items.values():
            if above_item.is_ban_offset:
                continue

            matched_node_item = above_item.match_node(node_items)
            if matched_node_item is None:
                continue

            logger.debug(f'above item {matched_node_item}')
            matched_node_item.is_above_item = True
            match_pairs.append((above_item.bbox, matched_node_item.trans_bbox))

        if len(match_pairs) == 0:
            return 0, 0

        max_width, max_height = 0, 0
        for _, node_bbox in match_pairs:
            if node_bbox.width > max_width:
                max_width = node_bbox.width
            if node_bbox.height > max_height:
                max_height = node_bbox.height

        offset = self.search_offset(match_pairs, int(max_height), int(max_width))

        return offset

    def search_offset(self, match_pairs: List[Tuple[BBox, BBox]], height, width) -> Tuple[int, int]:
        """
        搜索使得匹配到的 above item 中心点距离最近的 offset 值
        这里不能以 iou 为度量指标，因为 above item 的匹配对长度会是不一样的
        :param match_pairs: (above_bbox, node_bbox)
        :param height: 高度方向搜索范围 (-height, height)
        :param width: 宽度方向搜索范围 (-width, width)
        :return: (offset_x, offset_y)
        """
        offset = (0, 0)
        if len(match_pairs) == 0:
            return offset

        search_step = 1
        min_mean_dis = float('inf')
        for offset_x in range(-width, width + 1, search_step):
            for offset_y in range(-height, height + 1, search_step):
                dis_sum = 0
                for above_bbox, node_bbox in match_pairs:
                    node_left_cx = node_bbox.left + offset_x
                    node_left_cy = (node_bbox.top + node_bbox.bottom) / 2 + offset_y
                    above_left_cx, above_left_cy = above_bbox.left, (above_bbox.top + above_bbox.bottom) / 2
                    dis_sum += math.sqrt((node_left_cx - above_left_cx) ** 2 + (node_left_cy - above_left_cy) ** 2)
                mean_dis = dis_sum / len(match_pairs)

                if min_mean_dis > mean_dis:
                    min_mean_dis = mean_dis
                    offset = (offset_x, offset_y)

        return offset

    def sign_ban_offset(self, node_items: Dict[str, TpNodeItem], above_items: Dict[str, TpConfAboveItem]) -> Set[str]:
        """
        返回位于 ban_offset 区域内不需要进行前景偏移的元素 uid
        """
        res = []
        for node_item in node_items.values():
            if node_item.is_bg_item:
                res.append(node_item.uid)
                continue

            for above_item in above_items.values():
                if not above_item.is_ban_offset:
                    continue

                # 进行这步时已经做过了背景缩放所以要用 node_item.trans_bbox
                # ioo 相交大于阈值认为这个区域不可以偏移
                ioo = node_item.trans_bbox.cal_ioo(above_item.bbox)
                if ioo > above_item.ioo_thresh:
                    res.append(node_item.uid)

        return set(res)

    def cal_content_similarity(self, node_items: Dict[str, TpNodeItem]) -> Dict[str, Dict[str, float]]:
        """
        计算above element中的每一个元素和label的每一个元素的匹配程度conent_similarity[i][j]
        :return:
            Dict[above_item.uid, Dict[node_item.uid, similarity]]
            第一层 key 为 above_item.uid
            第二层 key 值为 node_item.uid
        """
        content_similarity = defaultdict(dict)
        for above_item in self.above_items.values():
            contents = above_item.contents

            if not isinstance(contents, list):
                contents = [contents]

            for content in contents:
                if isinstance(content, dict):
                    content = content.get('text', None)
                    if content is None:
                        logger.warning(f"{above_item.item_name}'s content is a dict, but not set 'text' key")
                        continue

                for node_item in node_items.values():
                    seq = difflib.SequenceMatcher(None, content, node_item.text)
                    similarity = seq.ratio()

                    if above_item.regex:
                        re_search_res = re.search(above_item.regex, node_item.text)
                        if re_search_res is not None:
                            similarity = max(similarity, 1.0)

                    content_similarity[above_item.uid][node_item.uid] = similarity

        return content_similarity

    def iou_block_search(self,
                         content_similarity: Dict[str, Dict[str, float]],
                         node_items: Dict[str, TpNodeItem],
                         ban_offset_uids: Set):
        w, h = 0, 0
        for above_item in self.above_items.values():
            w = max(w, above_item.bbox.right)
            h = max(h, above_item.bbox.bottom)

        for node_item in node_items.values():
            w = max(w, node_item.trans_bbox.right)
            h = max(h, node_item.trans_bbox.bottom)
        # w，h 为所有的框的上限位置，为搜索的上届，做二分法搜索
        now_offset_center = [0, 0]
        max_search_dis = max(w, h) / 6.0
        split_size = 10

        record_of_all_best = None
        while max_search_dis > 1:
            block_size = max_search_dis / split_size
            left_up_point = [v - (max_search_dis / 2.0) for v in now_offset_center]
            new_center = [0, 0]
            result_offset_center = [v for v in now_offset_center]
            best_similarity_value = 0

            for i in range(split_size):
                for j in range(split_size):
                    new_center[0] = left_up_point[0] + i * block_size
                    new_center[1] = left_up_point[1] + j * block_size
                    similarity_value, hit_num, hit_can_not_miss = self.cal_match_similarity_value(content_similarity,
                                                                                                  node_items,
                                                                                                  new_center,
                                                                                                  ban_offset_uids)
                    offset = [v for v in new_center]
                    if not record_of_all_best:
                        record_of_all_best = (hit_can_not_miss, hit_num, similarity_value, offset)
                    else:
                        # 现在里面已经有值了
                        current = (hit_can_not_miss, hit_num, similarity_value, offset)
                        if self.get_score_of_each_offest(current) > self.get_score_of_each_offest(record_of_all_best):
                            record_of_all_best = current

                    # 原先的处理逻辑
                    # if similarity_value > best_similarity_value:
                    #     best_similarity_value = similarity_value
                    #     result_offset_center = [v for v in new_center]

            #            now_offset_center = [v for v in result_offset_center]
            max_search_dis = block_size * 2

        # if self.exp_data:
        #     self.exp_data.set_above_matched_idxes(best_label_node_idx_4_debug)
        logger.debug('above offset with hit_can_not_miss :{} , with hit {}'.format(
            record_of_all_best[0],
            record_of_all_best[1]
        ))

        return record_of_all_best[3]
        # return now_offset_center

    def get_score_of_each_offest(self, record):
        # 对于每个位移，记录的信息为(hit_can_not_miss_num , hit_num , similarity)
        # 目前的判断准则为， 首先希望使得can not miss 的数量尽量多
        # 然后使得 hit 的个数尽量多
        # 然后在前两个一致的情形下使得similarity尽量高
        return record[0] * 10000 + record[1] * 100 + record[2]

    def cal_match_similarity_value(self,
                                   content_similarity: Dict[str, Dict[str, float]],
                                   node_items: Dict[str, TpNodeItem],
                                   offset: List[int],
                                   ban_offset_uids: Set,
                                   record_best_match_node=False
                                   ):
        """

        :param content_similarity: 已经计算出的相似度
        :param node_items: 传入的node_items 节点
        :param offset: 本次实验所使用的位移
        :param ban_offset_uids: 一系列的uid，用于记录哪些框是不能被移动的
        :param record_best_match_node: 是否返回每个above_item最匹配的node_item的uid
        :return:
        """
        best_match_map = defaultdict(dict)
        best_match_above_region = defaultdict(dict)
        sum_value = 0
        hit_num = 0  # 在当前位移下，iou不为零的的above_item个数
        hit_can_not_miss = 0
        for above_item in self.above_items.values():
            if above_item.is_ban_offset:
                continue
            max_value = 0
            above_bbox = above_item.bbox
            for node_item in node_items.values():
                if node_item.uid in ban_offset_uids:
                    continue
                similarity = content_similarity[above_item.uid][node_item.uid]
                if similarity > 0.7:
                    node_bbox = node_item.trans_bbox.transform((-offset[0], -offset[1]))
                    iou = node_bbox.cal_iou(above_bbox)  # 这里的逻辑是，把一个和他有字符上相似的框位置进行偏移，并期望偏移后的iou也很大
                    max_value = max(max_value, iou * similarity)
                    use_alternative = -1
                    if above_item.bbox_alternative:
                        # 说明存在其他区域
                        for idx, alternative_box in enumerate(above_item.bbox_alternative):
                            # 进行其他区域的尝试
                            iou = node_bbox.cal_iou(alternative_box)
                            if max(max_value, iou * similarity) > max_value:
                                use_alternative = idx
                            max_value = max(max_value, iou * similarity)

                    if record_best_match_node and max_value == iou * similarity and max_value != 0:
                        # max_value == iou * similarity , 代表对应的node item 的偏移后坐标和 这个above item更加匹配
                        best_match_map[above_item.uid][node_item.uid] = iou * similarity
                        best_match_above_region[above_item.uid][node_item.uid] = use_alternative

            if max_value != 0:
                # 说明这个前景参与了计算
                if above_item.can_not_miss:
                    # 统计在该位移下面，hit can not miss 的个数
                    hit_can_not_miss += 1
                hit_num += 1
            sum_value += max_value

        if record_best_match_node:
            return sum_value, best_match_map, best_match_above_region
        return sum_value, hit_num, hit_can_not_miss
