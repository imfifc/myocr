import os
import re
from typing import Optional, Tuple

from ocr_structuring.core.utils.str_util import keep_amountinwords_char

NUMBERS = '壹贰叁肆伍陆柒捌玖'
UNITS = '拾佰仟万亿元角分'
CN_INT = {'零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9}


class AmountUtils:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'amount_format.txt')
        self.prefix_patterns = self._load_amount_format(path)

    def word2num(self, text: str) -> Optional[str]:
        text = self.auto_correct_content(text)

        ret = self._split(text)
        if ret is None:
            return

        prefix_text, suffix_text = ret

        prefix_pattern_text = self._get_pattern(prefix_text)
        prefix_pattern_value = self.prefix_patterns.get(prefix_pattern_text, None)
        if prefix_pattern_value is None:
            return

        number_list = [CN_INT[c] for c in prefix_text if c in NUMBERS]
        if prefix_pattern_text == '拾圆':
            number_list.insert(0, 1)
            number_list.insert(1, 0)
        elif prefix_pattern_text == '拾*圆':
            number_list.insert(0, 1)

        offset_pos = 0
        prefix_pattern_value = list(prefix_pattern_value)
        for i in range(len(prefix_pattern_value)):
            bit = prefix_pattern_value[i]
            if bit == '1':
                prefix_pattern_value[i] = str(number_list[offset_pos])
                offset_pos += 1
        prefix_result_text = ''.join(prefix_pattern_value)

        suffix_result_text = ''
        n = len(suffix_text)
        if n >= 4 and suffix_text[0] == '零' and (suffix_text[1] in NUMBERS) and (
                (suffix_text[3] in NUMBERS) or (suffix_text[3] == '零')):
            suffix_result_text = str(CN_INT[suffix_text[1]]) + str(CN_INT[suffix_text[3]])
        elif n >= 2 and suffix_text[0] == '零' and (suffix_text[1] in NUMBERS):
            suffix_result_text = '0' + str(CN_INT[suffix_text[1]])
        elif n == 2 and suffix_text[1] == '分':
            suffix_result_text = '0' + str(CN_INT[suffix_text[0]])
        else:
            if n >= 1:
                c = suffix_text[0]
                if (c in NUMBERS) or c == '零':
                    suffix_result_text += str(CN_INT[c])
            if n >= 3:
                c = suffix_text[2]
                if c in NUMBERS:
                    suffix_result_text += str(CN_INT[c])

        if suffix_result_text == '':
            res = prefix_result_text
        else:
            res = '.'.join([prefix_result_text, suffix_result_text])
        return res

    def auto_correct_content(self, content: str) -> str:
        if content.startswith('零万'):
            # 现在的识别模型会把前面的 合计(大写) 错误的识别成零或者零万
            content = content[2:]
        # 如果发生了问题，做一些修补和自动推断，然后再次尝试
        dan_wei_2_num = {'万': 7, '仟': 6, '佰': 5, '拾': 4, '圆': 3, '分': 2, '角': 1}
        word_map = {'杆': '仟', '座': '叁', '啤': '肆', '抬': '拾', '捡': '拾'}
        num_2_danwei = {v: k for k, v in dan_wei_2_num.items()}

        content = [word_map.get(c, c) for c in content]

        for idx, loc in enumerate(content):
            if idx == 1 or idx > len(content) - 3:
                continue
            if content[idx - 1] in CN_INT and content[idx + 1] in CN_INT:
                if loc not in dan_wei_2_num:
                    i = content[idx - 2]
                    if i not in dan_wei_2_num:
                        continue
                    convert = num_2_danwei[dan_wei_2_num[i] - 1]
                    content[idx] = convert

        text = ''.join(content)
        # 合计大写的写字容易识别成万，这里移除
        if text.startswith('万'):
            text = text[1:]

        # 上海的医疗发票中可能打印了「捌佰玖拾元零零角壹分」
        if '零零' in text:
            text = text.replace('零零', '零')

        # 矫正 圆 的识别，
        text = re.sub('[元园固回]', '圆', text)

        # 识别模型容易把「整」前面的「圆」识别成「捌」
        if '圆' not in text and text.endswith('整') and len(text) > 3:
            idx = text.find('整')
            if text[idx - 1] == '捌':
                text = text[:idx - 1] + '圆' + text[idx:]

        text = keep_amountinwords_char(text)

        if text.startswith('零') and len(text) > 3:
            text = text[1:]

        return text

    def _load_amount_format(self, file_path):
        result = {}
        with open(file_path, mode='r', encoding='utf-8') as f:
            for line in f.readlines():
                k, v = line.strip().split(' ')
                result[k] = v
        return result

    def _get_pattern(self, text: str) -> str:
        pattern_str = re.sub(f'[{NUMBERS}]', '*', text)
        pattern_str = pattern_str.replace('元', '圆')
        pattern_str = pattern_str.replace('园', '圆')
        pattern_str = pattern_str.rstrip('整')
        return pattern_str

    def _split(self, text: str) -> Optional[Tuple[str, str]]:
        """
        以 圆 为单位整数部分和小数部分分割开来返回
        :param text:
        :return: (整数部分字符, 小数部分字符)
        """
        label_text = text.rstrip('整')

        yuan_pos_idx = label_text.find('圆')
        if yuan_pos_idx == -1:
            return

        numbers = '零壹贰叁肆伍陆柒捌玖'
        prefix_text = label_text[0:yuan_pos_idx]
        suffix_text = label_text[yuan_pos_idx + 1:]

        suffix_len = len(suffix_text)
        if suffix_len >= 4 and suffix_text[0] == '零' and (
                (suffix_text[1] in numbers) and ((suffix_text[3] in numbers) or (suffix_text[3] == '零'))):
            return prefix_text + '圆', suffix_text

        if suffix_len >= 2 and suffix_text[0] == '零' and (suffix_text[1] in numbers):
            return prefix_text + '圆', suffix_text

        if suffix_len >= 2 and (suffix_text[0] not in numbers) and (suffix_text[1] == '角'):
            return

        if suffix_len >= 4 and (suffix_text[2] not in numbers) and (suffix_text[3] == '分'):
            return

        if len(label_text) >= 3 and label_text[-2:] == '整分':
            return prefix_text + '圆', ''

        return prefix_text + '圆', suffix_text

    @staticmethod
    def num2word(num, last_char='正') -> str:
        """
        FIXME: 代码来源于网络，待优化、测试
        .转换数字为大写货币格式( format_word.__len__() - 3 + 2位小数 )
        change_number 支持 float, int, long, string
        """
        try:
            format_word = ["分", "角", "元",
                           "拾", "佰", "仟", "万",
                           "拾", "佰", "仟", "亿",
                           "拾", "佰", "仟", "万",
                           "拾", "佰", "仟", "兆"]

            format_num = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
            if type(num) == str:
                # - 如果是字符串,先尝试转换成float或int.
                if '.' in num:
                    num = float(num)
                else:
                    num = int(num)

            if type(num) == float:
                real_numbers = []
                for i in range(len(format_word) - 3, -3, -1):
                    if num >= 10 ** i or i < 1:
                        real_numbers.append(int(round(num / (10 ** i), 2) % 10))

            elif isinstance(num, int):
                real_numbers = []
                for i in range(len(format_word), -3, -1):
                    if num >= 10 ** i or i < 1:
                        real_numbers.append(int(round(num / (10 ** i), 2) % 10))

            else:
                '%s   can\'t change' % num

            zflag = 0  # 标记连续0次数，以删除万字，或适时插入零字
            start = len(real_numbers) - 3
            change_words = []
            for i in range(start, -3, -1):  # 使i对应实际位数，负数为角分
                if 0 < real_numbers[start - i] or len(change_words) == 0:
                    if zflag:
                        change_words.append(format_num[0])
                        zflag = 0
                    change_words.append(format_num[real_numbers[start - i]])
                    change_words.append(format_word[i + 2])

                elif 0 == i or (0 == i % 4 and zflag < 3):  # 控制 万/元
                    change_words.append(format_word[i + 2])
                    zflag = 0
                else:
                    zflag += 1

            if change_words[-1] not in (format_word[0], format_word[1]):
                change_words.append(last_char)

            return ''.join(change_words)
        except Exception as e:
            return ''


cn_amount_util = AmountUtils()
