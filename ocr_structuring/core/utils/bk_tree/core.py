import sys
from difflib import SequenceMatcher

import editdistance
from distance_metrics import lcs
from ocr_structuring.utils.logging import logger

sys.setrecursionlimit(1000000)


class Node(object):
    def __init__(self, word: str):
        self.word = word
        self.children = dict()

    def get_child(self, dist: int):
        return self.children[dist]

    def add_child(self, dist: int, new_word: str):
        assert (dist not in self.children.keys())
        self.children[dist] = Node(new_word)

    def get_dist_keys(self):
        return self.children.keys()

    def contain_key(self, dist: int):
        return dist in self.get_dist_keys()

    def cal_distance(self, other_word: str):
        return editdistance.eval(self.word, other_word)


class BKTree(object):
    def __init__(self, root: Node = None):
        self.root = root

    def insert_node(self, new_word: str):
        # logger.debug('insert word:{}'.format(new_word))
        if self.root is None:
            self.root = Node(new_word)
            return

        cur_node = self.root
        if cur_node.word == new_word:
            return

        dist = cur_node.cal_distance(new_word)
        while cur_node.contain_key(dist):
            cur_node = cur_node.children[dist]
            dist = cur_node.cal_distance(new_word)

        cur_node.add_child(dist, new_word)

    def search(self, word: str, search_dist=4, sort_by_ed=False):
        """
        :param word:
        :param search_dist: 返回小于 search_dist 的匹配项
        :param sort_by_ed: 是否根据编辑距离从小到大对搜索结果排序
        :return:
            [{'word': '', 'edit_distance': 3},...]
        """

        if self.root is None:
            return []

        candidate_words = []
        candidate_dict = {}
        self.recursive_search(self.root, candidate_words, candidate_dict, word, search_dist)

        if sort_by_ed:
            candidate_words = sorted(candidate_words, key=lambda item: item['edit_distance'])

        return candidate_words

    def search_one(self, text: str, search_dist=2, search_norm_dist=None, min_len=5):
        """
        返回编辑距离最小的那个候选字。如果两个候选字的编辑距离一样，会用 difflib 找最长公共子序列，返回子序列长度最大的
        :param text:
        :param search_dist: 返回小于 search_dist 的匹配项
        :param search_norm_dist: 如果不为 None，则根据 text 的长度计算 search_dist
        :param min_len: 如果 text 长度小于 min_len 则不进行搜索，并返回 None
        :return: str or None
        """
        if text is None:
            return text

        if len(text) < min_len:
            return None

        if search_norm_dist is not None:
            assert 0 < search_norm_dist < 1
            search_dist = int(search_norm_dist * len(text))

        candidate_words = self.search(text, search_dist, True)

        if len(candidate_words) == 0:
            return None

        max_LCS = 0
        out_idx = 0
        for i, it in enumerate(candidate_words):
            word = it['word']
            # s = SequenceMatcher(None, text, word)
            # lsc = s.find_longest_match(0, len(text), 0, len(word)).size
            llcs = lcs.llcs(text, word)
            if llcs > max_LCS:
                max_LCS = llcs
                out_idx = i

        return candidate_words[out_idx]['word']

    def recursive_search(self, node: Node, candidate_words: list, candidate_dict: dict, word: str, search_dist: int):
        cur_dist = node.cal_distance(word)
        min_dist = cur_dist - search_dist
        max_dist = cur_dist + search_dist
        if cur_dist <= search_dist:
            # TODO: 看起来这里的candidate_dict是在去重？
            if cur_dist not in candidate_dict.keys() or node.word not in candidate_dict[cur_dist]:
                if cur_dist not in candidate_dict.keys():
                    candidate_dict[cur_dist] = []
                candidate_dict[cur_dist].append(node.word)
                candidate_words.append({'word': node.word, 'edit_distance': cur_dist})

        for key in [key for key in node.get_dist_keys() if (min_dist <= key <= max_dist)]:
            self.recursive_search(node.children[key], candidate_words, candidate_dict, word, search_dist)
