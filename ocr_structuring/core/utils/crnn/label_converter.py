from __future__ import unicode_literals
import os
from ocr_structuring.utils.logging import logger


class LabelConverter:

    def __init__(self, chars_file, ctc_invalid_index=None):
        self.chars = ''.join(self.load_chars(chars_file))

        # char_set_length + ctc_blank
        self.num_classes = len(self.chars) + 1
        if ctc_invalid_index is None:
            self.ctc_invalid_index = len(self.chars)
        else:
            self.ctc_invalid_index = ctc_invalid_index

        self.encode_maps = {}
        self.decode_maps = {}

        self.create_encode_decode_maps(self.chars)

        logger.debug('Load chars file: %s num_classes: %d + 1(CTC Black)' % (chars_file, self.num_classes - 1))

    @staticmethod
    def load_chars(filepath):
        if not os.path.exists(filepath):
            raise AssertionError("Chars file not exists. %s" % filepath)
        ret = ''
        with open(filepath, mode='r', encoding='utf-8') as f:
            for line in f.readlines():
                if not line:
                    break
                ret += line[0]
        return ret

    def create_encode_decode_maps(self, chars):
        if self.ctc_invalid_index == len(chars):
            for i, char in enumerate(chars):
                self.encode_maps[char] = i
                self.decode_maps[i] = char
        else:
            # 对应 torch 的 ctc blank
            for i, char in enumerate(chars):
                self.encode_maps[char] = i + 1
                self.decode_maps[i + 1] = char

    def encode(self, label):
        """如果 label 中有字符集中不存在的字符，则忽略"""
        encoded_label = []
        for c in label:
            if c in self.chars:
                encoded_label.append(self.encode_maps[c])

        return encoded_label

    def encode_list(self, labels):
        encoded_labels = []
        for label in labels:
            encoded_labels.append(self.encode(label))
        return encoded_labels

    def decode(self, encoded_label):
        """
        :param encoded_label result of ctc_greedy_decoder
        :return decode label string
        """
        label = []
        for index, char_index in enumerate(encoded_label):
            if char_index != self.ctc_invalid_index:
                label.append(char_index)

        label = [self.decode_maps[c] for c in label]
        return ''.join(label)

    def decode_list(self, encoded_labels):
        decoded_labels = []
        for encoded_label in encoded_labels:
            decoded_labels.append(self.decode(encoded_label))
        return decoded_labels

    def filter_labels(self, labels):
        """
        把 labels 中不包含在 chars 中的字符都过滤掉
        :param labels: List[str]
        :return: List[str]
        """
        out = []
        for label in labels:
            tmp = ''
            for c in label:
                if c in self.chars:
                    tmp += c
            out.append(tmp)
        return out
