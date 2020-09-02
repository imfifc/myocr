from typing import List
from collections import namedtuple
import numpy as np
from .models import FilterRegex, FilterArea
from ..utils.node_item import NodeItem

RegexMatchResult = namedtuple('RegexMatchResult', 'w text scores')


class TpNodeItem(NodeItem):

    def __init__(self, raw_node, ltrb=True):
        super().__init__(raw_node, ltrb)
        # 代表当前节点是通过哪些区域和正则过滤保留下来的，用于计算最终的权重
        self.filter_areas: List[FilterArea] = []
        self.filter_regexes: List[FilterRegex] = []

        self.is_filtered_by_area = False
        self.is_filtered_by_regex = False
        self.is_filtered_by_content = False

        self.regex_match_results: List[RegexMatchResult] = []

        # 经过背景缩放的 bbox，这个值可能是通过投影变换计算出来的，也可能是通过 best match 计算出来的
        self.bg_scaled_bbox = None
        self.above_offset_bbox = None

        self.is_bg_item = False
        self.is_above_item = False

        # 这个变量用于记录这个node是否有被重识别过，在某些后处理过程中会被用到
        self.is_re_recognized = False
    @property
    def is_filtered(self):
        return self.is_filtered_by_area or \
               self.is_filtered_by_regex or \
               self.is_filtered_by_content

    def _attr_bbox(self):
        """
        设置split用何bbox
        :return:
        """
        return self.trans_bbox

    @property
    def trans_bbox(self):
        """
        :return: 经过背景缩放和投影变换后最终的坐标
        """
        if self.above_offset_bbox is not None:
            return self.above_offset_bbox

        if self.bg_scaled_bbox is not None:
            return self.bg_scaled_bbox

        return self.bbox

    def get_scores(self):
        if self.text is None:
            return []

        # 在 _pre_func 阶段可能已经赋值
        if len(self.scores) != 0:
            return self.scores

        return [1] * len(self.text)

    # TODO test LRU
    def get_final_w(self):
        """
        accumulating w(>=0) through layers
        """
        if self.is_filtered:
            return 0

        area_w = max([x.w for x in self.filter_areas]) if self.filter_areas else 1
        regex_w = max([x.w for x in self.filter_regexes]) if self.filter_regexes else 1
        return area_w * regex_w

        final_w = 1
        filter_layers = [[y.w for y in x] for x in [self.filter_areas, self.filter_regexes]]
        for filter_layer in filter_layers:
            if not filter_layer:
                continue
            tmp_w = 0
            for w in filter_layer:
                tmp_w += final_w * w
            final_w = tmp_w
        return final_w

    def add_regex_match_res(self, w, s, scores):
        self.regex_match_results.append(RegexMatchResult(w, s, scores))

    def get_max_match_regex_w_str(self) -> RegexMatchResult:
        """
        获得权重最高的正则匹配项，如果权重相同，再返回 crnn 置信度最高的结果
        """
        max_regex_w = 0
        # 做这个的前提是，字段进行了正则匹配，并且有正则匹配的结果，如果没有，直接返回字段
        if not self.filter_regexes:
            return RegexMatchResult(max_regex_w, self.text, self.scores)

        out_str = ''
        max_scores = []
        if len(self.regex_match_results) == 0:
            return RegexMatchResult(max_regex_w, out_str, max_scores)

        max_regex_w = max(self.regex_match_results, key=lambda it: it.w).w

        max_prob = 0
        for w, content, scores in self.regex_match_results:
            if w != max_regex_w:
                continue
            prob = np.mean(scores)
            if prob > max_prob:
                max_prob = prob
                max_scores = scores
                out_str = content

        return RegexMatchResult(max_regex_w, out_str, max_scores)

    def __repr__(self):
        return super().__str__()
