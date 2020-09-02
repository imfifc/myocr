from typing import Dict, List, Tuple, Callable
import numpy as np
import editdistance
from pampy import _ as __
from pampy import match

from ocr_structuring.core.utils import str_util
from ocr_structuring.core.utils.algorithm import max_sub_seq_order_dp
from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.core.utils.node_item_group import NodeItemGroup
from ocr_structuring.utils.logging import logger


class BgItem:
    MATCH_MODE_COMMON = 'common'  # 字符串完整匹配
    MATCH_MODE_HORIZONTAL_MERGE = 'h_merge'  # 字符串水平方向上单字合并
    MATCH_MODE_HORIZONTAL_SPLIT = 'h_split'  # 字符串水平方向上水平分割

    def __init__(self, text, mode, ed_thresh=-1, *,
                 h_split_pre_func: Callable = None,
                 h_split_max_interval: int = 1):
        """
        :param text: 待匹配的目标字符串
        :param mode: 匹配模式
        :param ed_thresh: 待匹配的编辑距离
        :param h_split_pre_func: h_split 中在调用 max_sub_seq_order_dp 时对 node_item 执行的预处理函数
        :param h_split_max_interval: max_sub_seq_order_dp 的返回索引间隔较大的话会忽略匹配，该值用于设置间隔的阈值
                                     最小值是 1，代表必须连续
        """
        self.text = text
        self.mode = mode
        self.h_split_pre_func = h_split_pre_func
        self.h_split_max_interval = h_split_max_interval

        # mode 为 MERGE_MODE_NORM 时计算匹配的编辑距离阈值
        # -1 代表完全匹配
        self.ed_thresh = ed_thresh

    def match(self, node_items: Dict[str, NodeItem]) -> List[NodeItem]:
        return match(
            self.mode,
            self.MATCH_MODE_COMMON, lambda _: self.norm_match(node_items),
            self.MATCH_MODE_HORIZONTAL_MERGE, lambda _: self.h_merge_match(node_items),
            self.MATCH_MODE_HORIZONTAL_SPLIT, lambda _: self.h_split_match(node_items,
                                                                           sub_seq_pre_func=self.h_split_pre_func,
                                                                           sub_seq_max_interval=self.h_split_max_interval),
            __, []
        )

    def norm_match(self, node_items: Dict[str, NodeItem]) -> Tuple[List[NodeItem], List[int]]:
        out = []
        ed_dists = []
        for it in node_items.values():
            matched, ed = self._text_match(it.cn_text, remove_symbols=True, remove_space=True, ed_thresh=self.ed_thresh)
            if matched:
                logger.info(f"bg_item [{self}] match {it} by [norm_match]")
                out.append(it)
                ed_dists.append(ed)
        return out, ed_dists

    def h_merge_match(self, node_items: Dict[str, NodeItem]) -> Tuple[List[NodeItem], List[int]]:
        norm_match_res = self.norm_match(node_items)
        if len(norm_match_res[0]) != 0:
            return norm_match_res

        candidate_node_items = {}
        candidate_chars_count = 0

        for node_item in node_items.values():
            if node_item.cn_text:
                for ic, c in enumerate(node_item.text):
                    if c in self.text:
                        s = node_item.split(ic, ic + 1)
                        candidate_node_items[s.uid] = s
                        candidate_chars_count += 1

        # 候选的节点的总长度小于背景的 content 长度，直接返回
        if candidate_chars_count < len(self.text):
            return [], []

        line_groups = NodeItemGroup.find_row_lines(candidate_node_items, y_thresh=0.3)

        out = []
        ed_dists = []
        for group in line_groups:
            if len(group.content()) < len(self.text):
                continue

            _g = group
            # 移除大于平均间隔字符
            if len(group.node_items) >= 3:
                avg_space = 0
                for i in range(len(group.node_items) - 1):
                    avg_space += (group.node_items[i + 1].bbox.cx - group.node_items[i].bbox.cx)
                avg_space /= len(group.node_items)
                __g = NodeItemGroup([group.node_items[0], group.node_items[1]])
                for i in range(2, len(group.node_items)):
                    if group.node_items[i].bbox.cx - group.node_items[i - 1].bbox.cx > 2 * avg_space:
                        continue
                    __g.append(group.node_items[i])
                if len(__g.node_items) != 0:
                    _g = __g

            if _g.content() == self.text:
                new_node = NodeItem(_g.gen_raw_node())
                out.append(new_node)
                ed_dists.append(editdistance.eval(new_node.text, self.text))
                logger.info(f"bg_item [{self}] match node_item {new_node} by [h_merge_match]")
        return out, ed_dists

    @staticmethod
    def align_node_idxes(node_idxes, clean_text, text):
        """
        """"""
        基本思想，clean_text 的元素个数一定是 少于 text 的
        这里采用贪婪算法，将clean_text 的字母按照从左到右的顺序，一个一个的去和text 的字母比较
        找到 node_idxes 对应到text 当中的idx
        
        
        如  clean_text: a c t u a l c p o
                        | | | | | | \ \ \
                                      \ \ \
            text:       a c t u a l ___ c p o
        """

        text = text.lower()
        clean_text = clean_text.lower()

        # 检查按照greedy 分配的方式，能否将text 的每个元素，找到在 text 当中的对应位置

        if clean_text == '' or text == '' or len(clean_text) >= len(text) or len(set(clean_text) - set(text)) != 0:
            # 特殊情况
            # 直接返回
            return node_idxes

        match_idxes = []
        cur_idx_in_text = 0
        for idx in range(len(clean_text)):
            cur_text = clean_text[idx]
            for idx_in_text in range(cur_idx_in_text, len(text)):
                if cur_text == text[idx_in_text]:
                    match_idxes.append(idx_in_text)
                    cur_idx_in_text = idx_in_text
                    break
        # 检查合理性
        # 即clean_text 是 text 的一个子串
        if len(match_idxes) == len(clean_text) and (np.array(match_idxes)[1:] - np.array(match_idxes[:-1]) > 0).all():
            new_idx = []
            for id in node_idxes:
                new_idx.append(match_idxes[id])
            return new_idx
        else:
            return node_idxes

    def h_split_match(
            self,
            node_items: Dict[str, NodeItem],
            *,
            sub_seq_max_interval: int = 2,
            sub_seq_pre_func: Callable = None,
    ) -> Tuple[List[NodeItem], List[int], List[NodeItem]]:
        """
        :param node_items:
        :param sub_seq_max_interval: 最长公共子序列的间距
        :param sub_seq_pre_func: 在调用 max_sub_seq_order_dp 时，对 it.text 进行预处理
        :return:
        """
        splited_ed_dist = []
        splited_key_node = []
        splited_rest_nodes = []
        for it in node_items.values():
            if sub_seq_pre_func is None:
                res, bg_idxes, node_idxes = max_sub_seq_order_dp(self.text, it.text)
            else:
                res, bg_idxes, node_idxes = max_sub_seq_order_dp(self.text, sub_seq_pre_func(it.text))

            ed_dist = abs(len(res) - len(self.text))
            if self.ed_thresh == -1:
                if res != self.text:
                    continue
            else:
                if ed_dist > self.ed_thresh:
                    continue

            # node 索引的间隔不能超过 1
            should_continue = False
            for i in range(len(node_idxes) - 1):
                if node_idxes[i + 1] - node_idxes[i] > sub_seq_max_interval:
                    should_continue = True
                    break
            if should_continue:
                continue

            if node_idxes[0] > 2:
                # split 出来的节点应该要位于字符串开头位置
                continue

            if sub_seq_pre_func is not None:
                node_idxes = self.align_node_idxes(node_idxes, sub_seq_pre_func(it.text), it.text)

            start_idx = node_idxes[0]
            end_idx = node_idxes[-1] + 1

            # sub_str_start_idxes = str_util.findall_sub_str_idx(sub_text=self.text, text=it.text)
            # if len(sub_str_start_idxes) != 1:
            #     continue
            # start_idx = sub_str_start_idxes[0]
            # # 假设所有要 split 的背景字比较靠前
            # if start_idx >= 3:
            #     continue
            # end_idx = sub_str_start_idxes[0] + len(self.text)

            if end_idx > start_idx:
                new_node = it.split(start_idx, end_idx)
                if new_node:
                    splited_key_node.append(new_node)
                    splited_ed_dist.append(ed_dist)

                rest_node = it.split(end_idx, -1)
                if rest_node:
                    splited_rest_nodes.append(rest_node)

        norm_match_res, norm_match_ed_dists = self.norm_match(node_items)
        splited_key_node.extend(norm_match_res)
        splited_ed_dist.extend(norm_match_ed_dists)

        if len(splited_key_node) != 0:
            logger.info(f"bg_item [{self}] match {' '.join(map(str, splited_key_node))} by [split_match]")

        for node in splited_rest_nodes:
            node.is_cut = True

        return splited_key_node, splited_ed_dist, splited_rest_nodes

    def _text_match(self, text, remove_symbols=False, remove_space=False, ed_thresh=-1) -> Tuple[bool, int]:
        """
        返回是否
           是否匹配
           编辑距离，如果不匹配，则返回 -1
        """
        exp_text = self.text
        if remove_symbols:
            exp_text = str_util.remove_symbols(self.text)
            text = str_util.remove_symbols(text)

        if remove_space:
            exp_text = str_util.remove_space(exp_text)
            text = str_util.remove_space(text)

        if text == '' or exp_text == '':
            return False, -1

        if exp_text == text:
            return True, 0

        if ed_thresh != -1:
            eddist = editdistance.eval(exp_text, text)
            ed_match = (eddist <= ed_thresh)
            return ed_match, eddist
        else:
            return False, -1

    def __str__(self):
        return f"{self.text} {self.mode}"
