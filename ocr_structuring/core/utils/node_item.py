import difflib

import cv2
import numpy as np
import copy
import math
import uuid
from typing import List
from wcwidth import wcswidth

import ocr_structuring.core.utils.str_util as str_util
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.rbox import RBox
from ocr_structuring.core.utils.score_string import ScoreString


class NodeItem:
    def __init__(self, raw_node, ltrb=True):
        """
        :param raw_data:
                ltrb==False [text, x1, y1, x2, y2, x3, y3, x4, y4, angle, label, probability]
                ltrb==True [text, left, top, right, bottom, label, probability]
        """
        if ltrb:
            # 使用 cv2.boundingRect 获得 BBox 会导致 right, bottom + 1，所以这里要减去 1
            raw_node = [
                raw_node[0],
                raw_node[1],
                raw_node[2],
                raw_node[3],
                raw_node[2],
                raw_node[3],
                raw_node[4],
                raw_node[1],
                raw_node[4],
                0,
                *raw_node[5:],
            ]

        self.raw_node = raw_node
        self.uid = uuid.uuid1().hex
        self.text: str = raw_node[0]
        self.ltrb = ltrb

        x, y, w, h = cv2.boundingRect(np.array(raw_node[1:9]).reshape(4, 2).astype(np.int))

        if ltrb:
            self.bbox = BBox([x, y, x + w - 1, y + h - 1])
        else:
            self.bbox = BBox([x, y, x + w, y + h])

        self.rbox = RBox(raw_node[1:10])
        self.text_label = raw_node[10]
        self.scores = raw_node[11:]

        self._ss = ScoreString(self.text, self.scores)

        self.is_cut=False

    @property
    def is_empty(self):
        return not bool(self.text)

    @property
    def cn_text(self) -> str:
        """
        仅包含中文字符的 text
        """
        return str_util.get_clean_cn_text(self.text)

    @property
    def en_text(self) -> str:
        return str_util.get_clean_eng(self.text)

    @property
    def ss(self):
        return self._ss

    @ss.setter
    def ss(self, new: ScoreString):
        self._ss = new
        self.text = new.data
        self.scores = new.scores

    @property
    def probability(self) -> float:
        if len(self.scores) == 0:
            return 0

        return sum(self.scores) / len(self.scores)

    def clear(self):
        self.text = ""
        self.scores = []

    def gen_ltrb_raw_node(self) -> List:
        return copy.deepcopy(
            [
                self.text,
                self.bbox.left,
                self.bbox.top,
                self.bbox.right,
                self.bbox.bottom,
                self.text_label,
                *self.scores,
            ]
        )

    def split(self, start: int, end: int) -> "NodeItem" or None:
        """
        返回的字符串包含 start 的字符，不包含 end 的字符
        根据中文、英文、数字、符号的字符宽度切分，返回新的 NodeItem。
        该方法可同时兼顾中文、英文、符号的宽度
        原理：先计算纯文本的字符长度，然后根据bbox的宽度计算单元字符宽度，通过子串的文本长度 * 单元宽度得到最终宽度
        """
        if end > len(self.text) or end == -1:
            end = len(self.text)

        if end <= start:
            return None

        if start < 0:
            return None

        if not self.text:
            return None

        if start == 0 and end == len(self.text):
            return copy.deepcopy(self)

        pure_text_len = wcswidth(self.text)
        total_width = self._attr_bbox().width
        unit_char_width = total_width / pure_text_len

        sub_text = self.text[start:end]
        sub_text_len = wcswidth(sub_text)
        sub_text_width = sub_text_len * unit_char_width

        left_text = self.text[0:start]
        if len(left_text) == 0:
            left_text_len = 0
        else:
            left_text_len = wcswidth(left_text)
        left_text_width = left_text_len * unit_char_width

        left = self._attr_bbox().left + left_text_width
        right = left + sub_text_width
        return self.__class__(
            [
                sub_text,
                math.ceil(left),
                math.ceil(self._attr_bbox().top),
                math.ceil(right),
                math.ceil(self._attr_bbox().bottom),
                self.text_label,
                *self.scores[start:end],
            ],
            ltrb=True,
        )

    def _attr_bbox(self):
        """
        设置split用何bbox
        :return:
        """
        return self.bbox

    def _is_same(self, other: "NodeItem") -> bool:
        """
        - text 相同
        - bbox 相同
        """
        if other is None:
            return False

        if self.text != other.text:
            return False

        if self.bbox != other.bbox:
            return False

        return True

    def __eq__(self, other: "NodeItem"):
        return self._is_same(other)

    def __hash__(self):
        return (
            hash(self.text)
            + hash(self.bbox.left)
            + hash(self.bbox.top)
            + hash(self.bbox.right)
            + hash(self.bbox.bottom)
        )

    def __ne__(self, other: "NodeItem"):
        return not self._is_same(other)

    def __str__(self):
        return "%s [%d %d %d %d]" % (
            self.text,
            self.bbox.left,
            self.bbox.top,
            self.bbox.right,
            self.bbox.bottom,
        )
