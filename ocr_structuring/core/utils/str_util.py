# encoding=utf-8
import difflib
import re
import unicodedata
from typing import Dict, Callable, Tuple, List, Optional

CAPITAL_ENG = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
LOWER_ENG = set('abcdefghijklmnopqrstuvwxyz')
ENG_CHARS = CAPITAL_ENG | LOWER_ENG
NUM_CHARS = set('0123456789')
MONEY_CHARS = NUM_CHARS | set('.')
ENG_NUM_CHARS = ENG_CHARS | NUM_CHARS
SYMBOL_CHARS = set('!@#$%^&*()_+~-=<>?:：;；'".,{}\\|`“、。，！￥·/")
SYMBOL_EXCEPT_PARENTHESES = set('!@#$%^&*_+~-=<>?:：;；'".,{}\\|`“、。，！￥")
SPACE_CHAR = ' '
PYTORCH_CRNN_SPACE_CHAR = '_'

SYMBOL_AND_SPACE_CHARS = SYMBOL_CHARS | set(
    SPACE_CHAR) | set(PYTORCH_CRNN_SPACE_CHAR)

ENG_2_NUM_MAP = {
    'A': '4', 'a': '0',
    'B': '8', 'b': '6',
    'C': '0', 'c': '0',
    'D': '0', 'd': '5',
    'E': '3', 'e': '0',
    'F': '9', 'f': '1',
    'G': '6', 'g': '9',
    'Y': '7', 'y': '7',
    'O': '0', 'o': '0',
    'S': '5', 's': '5',
    'T': '7', 't': '4',
    'Z': '2', 'z': '2',
}

CHN_YEAR2_NUM_MAP = {
    '一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6',
    '七': '7', '八': '8', '九': '9', '〇': '0', '0': '0', '—': '1'
}

CHN_MONTH2_NUM_MAP = {
    '一': '01', '二': '02', '三': '03', '四': '04', '五': '05', '六': '06',
    '七': '07', '八': '08', '九': '09', '十': '10', '十一': '11', '十二': '12'
}

CHN_DAY2_NUM_MAP = {
    '一': '01', '二': '02', '三': '03', '四': '04', '五': '05', '六': '06',
    '七': '07', '八': '08', '九': '09', '十': '10', '十一': '11', '十二': '12',
    '十三': '13', '十四': '14', '十五': '15', '十六': '16', '十七': '17', '十八': '18', '十九': '10', '二十': '20',
    '二十一': '21', '二十二': '22', '二十三': '23', '二十四': '24', '二十五': '25', '二十六': '26', '二十七': '27', '二十八': '28', '二十九': '29',
    '三十': '30', '三十一': '31', '三十二': '22', '三十三': '23', '三十四': '24', '三十五': '25', '三十六': '26', '三十七': '27',
    '三十八': '28', '三十九': '29'
}

MONEY_BIG_CHARS = '零壹贰叁肆伍陆柒捌玖拾佰仟万圆正整角分'
AMOUNTINWORDS_CHARS = '零壹贰叁肆伍陆柒捌玖拾佰仟万亿圆元角分整'
CHINESE_NUM = '零壹贰叁肆伍陆柒捌玖拾佰仟万'


def remove_last_dot(text):
    """
    2055. 这种金额的预测结果会被正则表达式过滤掉，该函数会把最后一个 dot 移除
    """
    if text is None:
        return text
    if len(text) != 0 and text[-1] == '.':
        text = text[:-1]
    return text


def remove_first_char(text, char='.'):
    """
    .2055 这种金额的预测结果会被正则表达式过滤掉，该函数会把最后一个 dot 移除
    """
    if text is None:
        return text

    if len(text) != 0 and text[0] == char:
        text = text[1:]
    return text


def remove_number_if_body_isnot_num(text):
    """
    有的字段，主体可能是纯数字，也可能是纯中文，但是识别出出来数字
    处理思路为：计算数字和其他的比例，如果数字的比例不足，就全部删除
    """
    if not text:
        return text
    num_chars = len(text)
    num_number = 0
    for char in text:
        if char in NUM_CHARS:
            num_number += 1
    if num_number / num_chars * 1.0 < 0.5:
        return filter_not_num(text)
    else:
        return filter_num(text)


def remove_extra_dot(text):
    """
    别模型可能会将「逗号」识别成小数点，例如 20.500.25 的真值是 20,500.25
    该函数会把除最后一个小数点意外的小数点移除

    - 2.500.25 -> 2500.25
    - .11 -> .11
    - 11. -> 11.
    """
    if text is None:
        return text

    tmp = text.split('.')
    if len(tmp) > 2:
        text = ''.join(tmp[:-1]) + '.' + tmp[-1]
    return text


def filter_not_num(text):
    """
    保留非数字
    """
    return ''.join(filter(lambda x: x not in NUM_CHARS, text))


def filter_num(text):
    """
    仅保留 text 中的数字字符
    """
    return ''.join(filter(lambda x: x in NUM_CHARS, text))


def filter_num_eng(text):
    """
    仅保留 text 中的数字和字母
    """
    return ''.join(filter(lambda x: x in ENG_NUM_CHARS, text))


def remove_space(text):
    """
    移除字符串中的空格
    """
    if text is None:
        return text

    # pytorch crnn 项目中把空格字符转换成了下划线
    text = text.replace(PYTORCH_CRNN_SPACE_CHAR, '')
    text = text.replace(SPACE_CHAR, '')
    return text


def remove_chars(text: str or None, chars: str) -> str or None:
    if text is None:
        return text
    return ''.join(filter(lambda x: x not in chars, text))


def match_re(text: str, regex) -> bool:
    # 判断文本是否符合一个re表达式
    return len(re.findall(regex, text)) != 0


def replace_shuminghao(text):
    text = text.replace('《', '（')
    text = text.replace('》', '）')
    return text


def replace_special_word(text, replace_words: List, target_words: List):
    for r, t in zip(replace_words, target_words):
        text = text.replace(r, t)
    return text


def replace_space(text, char):
    """
    把空格换成其他字符
    """
    if text is None:
        return text

    if char is None:
        return text

    # pytorch crnn 项目中把空格字符转换成了下划线
    text = text.replace(PYTORCH_CRNN_SPACE_CHAR, char)
    text = text.replace(SPACE_CHAR, char)
    return text


def remove_symbols_and_space(text):
    """
    移除字符串中的所有符号和空格
    """
    if text is None:
        return text

    return ''.join(filter(lambda x: x not in SYMBOL_AND_SPACE_CHARS, text))


def remove_symbols_except_parentheses(text):
    if text is None:
        return text
    return ''.join(filter(lambda x: x not in SYMBOL_EXCEPT_PARENTHESES, text))


def remove_redundant_patthern(text, pattern_list):
    if text is None:
        return text
    for pattern in pattern_list:
        text = re.sub(pattern, '', text)
    return text


def replace_chinese_parentheses_to_eng(text):
    if text is None:
        return text
    if '（' or '）' in text:
        text = text.replace('（', '(')
        text = text.replace('）', ')')
    return text


def clean_eng_num_text_to_num(text):
    """
    对医疗机构类型，有时候为纯数字，但是检测模型会检测出英文，则将英文替换为可能的数字
    """
    if not text:
        return text
    replace_map = {"B": 8, "O": "0", "o": "0", "K": "X", "I": '1', 'D': '0', 'G': '6', 'Y': 7, 'U': 0}

    for need_replace in replace_map:
        if need_replace in text:
            text = text.replace(need_replace, str(replace_map[need_replace]))
    return text


def remove_symbols(text, contain: List = None):
    """
    移除字符串中的所有符号 , 但是contain中的留下
    """
    if text is None:
        return text
    if contain:
        return ''.join(filter(lambda x: x not in SYMBOL_CHARS or x in contain, text))
    else:
        return ''.join(filter(lambda x: x not in SYMBOL_CHARS, text))


def replace_eng_with_num(text):
    """
    把相似的英文字字符替换为数字
    """
    if text is None:
        return text

    tmp = ''
    for c in text:
        tmp += ENG_2_NUM_MAP.get(c, c)
    text = tmp
    return text


def only_keep_money_char(text):
    return ''.join(filter(lambda x: x in MONEY_CHARS, text))


def only_keep_continue_money_char(text, return_first=True):
    # 现在默认只返回第一个,return_first 返回false的话，会返回最长的那个一
    text_ = list(map(lambda x: x if x in MONEY_CHARS else '_', text))
    text_ = ''.join(text_)
    if not text_:
        return ''
    text_ = list(filter(lambda x: x != '', text_.split('_')))
    if return_first:
        if len(text_) > 0:
            return text_[0]
        else:
            return ''
    else:
        if text_:
            return max(text_, key=lambda x: len(x))
        else:
            return ''


def only_keep_start_money_char(text):
    # 返回一个字符串开头的数字部分，比如 12你好 ，返回12
    text_ = list(map(lambda x: x if x in MONEY_CHARS else '_', text))
    text_ = ''.join(text_)
    if text_.startswith('_'):
        return ''
    else:
        text_ = text_.split('_')
        return text_[0]


def to_money(text) -> str:
    if not text:
        return ''

    text = only_keep_money_char(text)
    text = remove_last_dot(text)
    text = remove_extra_dot(text)

    if not text:
        return ''

    return text


def keep_num_char(text):
    if not text:
        return text
    return ''.join(list(filter(lambda x: x in NUM_CHARS, text)))


def keep_eng_num_char(text):
    if not text:
        return text
    return ''.join(list(filter(lambda x: x in NUM_CHARS or x in ENG_CHARS, text)))


def keep_amountinwords_char(text):
    if not text:
        return text

    return ''.join(filter(lambda x: x in AMOUNTINWORDS_CHARS, text))


def contain_chinese_num(text) -> bool:
    if not text:
        return False

    for c in text:
        if c in CHINESE_NUM:
            return True

    return False


def only_keep_chn(txt: str):
    if txt is None:
        return None

    return re.sub('[^一-龥]', '', txt)

def only_keep_chn_withsymbol(text):
    if text is None:
        return None
    return re.sub('[^一-龥、，“”；《》]', '', txt)

def remove_chn_chars(txt: str):
    if txt is None:
        return None

    return re.sub('[一-龥]', '', txt)


def get_clean_cn_text(text: str):
    """
    只保留中文字符
    """
    if text is None:
        return None

    return re.sub('[^一-龥]', '', text)


def is_cn(text: str) -> bool:
    return len(re.sub('[^一-龥]', '', text)) == 0


def contain_cn(text: str) -> bool:
    return len(re.sub('[一-龥]', '', text)) != len(text)


def get_clean_eng(text: str, lower=False, replace_space=True):
    """
    :param text:
    :param lower: 输出是否要转成小写
    :param replace_space: if true, 把空格替换成下划线 `_`
    """
    space_char = '_' if replace_space else ' '
    text = re.sub('[^0-9A-Za-z]', space_char, text)
    text = re.sub('%s+' % space_char, space_char, text)
    if lower:
        text = text.lower()
    text = text.strip('_')
    return text


def count_num_in_text(text):
    count = 0
    for char in text:
        if char in NUM_CHARS:
            count += 1
    return count


def is_all_num_eng(text):
    if text is None:
        return False
    for c in text:
        if c not in NUM_CHARS and c not in ENG_CHARS:
            return False
    return True


def is_all_num(text):
    """
    判断 text 中是否全是数字
    """
    if text is None:
        return False

    for c in text:
        if c not in NUM_CHARS:
            return False
    return True


def strip_space(text):
    """
    移除字符串首尾的空格
    """
    if text is None:
        return text

    res = text.strip('_')
    res = res.strip(' ')

    return res


def underline_to_camel(underline_format_str):
    """
    下划线命名格式驼峰命名格式
    """
    camel_format_str = ''
    if isinstance(underline_format_str, str):
        for _s_ in underline_format_str.split('_'):
            camel_format_str += _s_.capitalize()
    return camel_format_str


def camel_to_underline(word: str) -> str:
    """
    Make an underscored, lowercase form from the expression in the string.

    Example::
        >>> camel_to_underline("DeviceType")
        "device_type"
    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")
    return word.lower()


def findall_sub_str_idx(sub_text, text):
    """
    返回所有 sub_text 的起止位置的索引
    :param sub_text:
    :param text:
    :return: List[int], 每个子串开始位置的索引
    """
    if text is None or sub_text is None:
        return []

    iters = re.finditer(re.escape(sub_text), text)

    start_idxes = []
    for m in iters:
        start_idxes.append(m.start(0))

    return start_idxes


def cal_char_mean_width(width, text):
    """
    :param width:
    :param text:
    :return:
    """
    if not text:
        return 0

    chn_unit = 1
    eng_unit = 0.65  # 经验值

    count = 0
    for c in text:
        if c in (ENG_NUM_CHARS | SYMBOL_CHARS):
            count += eng_unit
        else:
            count += chn_unit

    return int(width / count)


def contain_only_special(text, char) -> bool:
    if text == '':
        return False
    only_contain = True
    for ch in text:
        if ch != char:
            only_contain = False
    return only_contain


def contain_continue_nums(text, num_count=10) -> bool:
    """
    判断一个字符串中是否包含固定多个连续的数字
    :param text:
    :param num_count: 连续数字的个数
    :return:
    """
    if not text and num_count == 0:
        return True

    if not text:
        return False

    count = 0
    max_count = 0
    for c in text:
        if str.isdigit(c):
            count += 1
            max_count = max(max_count, count)
        else:
            count = 0

    if max_count >= num_count:
        return True

    return False


def count_max_continue_nums(text) -> int:
    if not text:
        return 0

    iters = re.finditer('\d+', text)

    max_len = 0
    for i in iters:
        max_len = max(max_len, i.span()[1] - i.span()[0])

    return max_len


def filter_data_format_standard(filter_str):
    str_ = filter_str.replace(',', '')
    str_ = str_.replace(':', '')
    str_ = str_.replace(u'学年', u'年')
    str_ = str_.replace('--', '-')
    str_ = str_.replace('_', '')
    str_ = str_.replace(u'】', '')
    year_index = str_.find(u'年')
    month_index = str_.rfind(u'月')
    day_index = str_.find(u'日')
    # print('year index, month index, day index',year_index,month_index,day_index)
    if year_index == -1 or month_index == -1:
        return str_
    try:
        year = int(str_[year_index - 4:year_index])
        month = str_[year_index + 1:month_index]
        # print('month is......',month,year_index,month_index)
        if len(month) == 2 and int(month[0]) > 2:
            month = month[1]
        month = int(month)
        if day_index != -1:
            if (day_index - month_index == 2) or (day_index - month_index == 3):
                day = int(str_[month_index + 1:day_index])
                if day > 31:
                    day = day % 10
                res = '{}-{:02}-{:02}'.format(year, month, day)
                return res
            else:
                day = ''
                str2 = str_[month_index + 1:month_index + 3]
                if str2.isdigit() is True:
                    day = int(str2)
                else:
                    day = int(str_[month_index + 1])
                if day > 31:
                    day = day % 10
                res = '{}-{:02}-{:02}'.format(year, month, day)
                return res
        else:
            # print('--------------')
            day = ''
            str2 = str_[month_index + 1:month_index + 3]
            # print('str2,,,,,,',str2)
            if str2.isdigit() is True:
                day = int(str2)
            else:
                day = int(str_[month_index + 1])
            if day > 31:
                day = day % 10
            res = '{}-{:02}-{:02}'.format(year, month, day)
            return res
    except Exception:
        pass
    return str_


def filter_yingyezhizhao_qixian(qixian_str):
    time_split = qixian_str.split(u'至')
    times_filtered = []
    for time_item in time_split:
        time_filtered = filter_data_format_standard(time_item)
        times_filtered.append(time_filtered)
    str_ = ','.join(times_filtered)
    return str_


def filter_date_format1(str):  # 用在本科学位证书中过滤日期用。输入示例:卢国_安_,_男,_1990年1_月_7_日生。在
    regex = '^\S*([\d+]{4,}\S+日)[生。在]'
    m = re.search(regex, str)
    if m:
        str_matched = m.group(1)
        # print(m.group(0),m.group(1))
        str_filtered = str_matched.replace('_', '')
        str_filtered = str_filtered.replace('.', '')
        str_filtered = str_filtered.replace('g', '')
        # 1989年22月28日矫正 1991.年01月08g日
        index_year = str_filtered.find('年')
        index_month = str_filtered.find('月')
        month_str = str_filtered[index_year + 1:index_month]
        try:
            # 如果未能加载GroundTruth，认为其没有对应的GroundTruth
            if len(month_str) == 2 and int(month_str[0]) > 1:
                str_filtered = str_filtered[0:index_year +
                                              1] + str_filtered[index_month - 1:]
            return str_filtered
        except Exception:
            pass

    return str


def filter_degree_format(str):  # 用在本科学位证书中过滤专业：输入示例：毕业,_经审核符合《中华人民共和国学位条例》的规定,授予管理学
    regex = '^(\S+授予)?([\S]{2,})$'
    str = str.replace('王学', '工学')
    m = re.search(regex, str)
    print(regex, str)
    if m:
        str_matched = m.group(2)
        str_filtered = str_matched.replace('_', '')
        return str_filtered
    return str


def filter_degree_issue_date(str):  # 用在本科学位证书中过滤签发时间，输入示例：三_0一三年年六月三七日日
    str = str.replace('_', '')
    # print('str of issue date', str)
    continous_check_words = ['年年', '月月', '日日']
    str = str.replace('Q', '0')
    for words in continous_check_words:
        str = str.replace(words, words[0])
    if str.startswith('三'):
        str_list = [str[i] for i in range(len(str))]
        str_list[0] = '二'
        str = ''.join(str_list)
    return str


def filter_degree_school(str):  # 用在本科学位证书中纠正学校
    str = str.replace('丙蒙古', '内蒙古')
    return str


def filter_jidongche_jiashuiheji(str):
    str = str.replace('_', '')
    return str


def filter_jidongche_xiaoxie_price(str):
    str = str.replace('_', '')
    place_pos = [i.start() for i in re.finditer('\.', str)]
    place_count = len(place_pos)
    str_filtered = str
    # print(str, place_pos)
    if place_count == 2:
        # print(str, place_pos)
        str_filtered = str[0:place_pos[0]] + ',' + str[place_pos[0] + 1:]
    regex = '(￥?[\d+,\.]{3,})'
    m = re.search(regex, str_filtered)
    if m:
        str_filtered = m.group(1)
    return str_filtered
    #     price_mark_index = str_filtered.find('￥')
    #     if price_mark_index != -1:
    #         str_filtered = str_filtered[price_mark_index:]
    #     return str_filtered
    # price_mark_index = str.find('￥')
    # if price_mark_index != -1:
    #     str = str[price_mark_index:]
    # return str


def filter_jidongche_kaipiaoriqi(str):  # 用在机动车销售发票中过滤开票日期字符串，'开票日期_2012-03-02'
    regex = '^\S*([\d+]{4,}\S+)$'
    m = re.search(regex, str)
    if m:
        str_matched = m.group(1)
        str_filtered = str_matched.replace('_', '')
        return str_filtered
    return str


def correct_date_str(str):
    place_pos = [i.start() for i in re.finditer('\-', str)]
    content = ''
    if len(place_pos) == 2:
        year = str[0:place_pos[0]]
        month = str[place_pos[0] + 1:place_pos[1]]
        day = str[place_pos[1] + 1:]
        # print('year,  month, day', year, month, day)
        if len(year) > 1 and year[0] == '2' and (year[1] == '6' or year[1] == '8'):
            # print('-----------------**********---------------')
            content = year[0] + '0'
            content += year[2:]
        else:
            content += year
        content += '-'
        if len(month) == 2 and (month[0] == '8' or month[0] == 'β'):
            content += '0'
            content += month[1]
        elif len(month) == 1:
            content += '0'
            content += month
        else:
            content += month
        content += '-'
        if len(day) == 2 and (day[1] == '{'):
            content += day[0]
            content += '1'
        else:
            content += day
        # print('content is ---------',content)
        return content
    return str


def filter_jidongche_valid_term(str):
    zhi_index = str.find('至')
    print('str.......', str, zhi_index)
    if zhi_index != -1:
        left = str[0:zhi_index]
        right = str[zhi_index + 1:]
        content = ''
        content += correct_date_str(left)
        content += '至'
        content += correct_date_str(right)
        return content
    return str


# 机动车驾驶证中起作用，针对机动车驾驶证中出现的'C1卫'等情况
def filter_driving_licence_zhunjiachexing_field(str):
    if str.endswith('卫'):
        str = str[:-1] + 'E'
    if str[0] == '2':
        str = 'A' + str[1:]
    return str


def convert_chinese_time2digital_time(time_str):
    year_index = time_str.find(u'年')
    month_index = time_str.find(u'月')
    day_index = time_str.find(u'日')
    year_str = time_str[0:year_index]
    if year_index > 4:
        year_str = year_str[-4:]
    month_str = time_str[year_index + 1:month_index]
    day_str = time_str[month_index + 1:day_index]
    year_ = []
    for year_item in year_str:
        if year_item in CHN_YEAR2_NUM_MAP.keys():
            digit_item = CHN_YEAR2_NUM_MAP[year_item]
            year_.append(digit_item)
    year_transfered = ''.join(year_)
    if month_str in CHN_MONTH2_NUM_MAP.keys():
        month_transfered = CHN_MONTH2_NUM_MAP[month_str]
    else:
        month_transfered = '01'
    if day_str in CHN_DAY2_NUM_MAP.keys():
        day_transfered = CHN_DAY2_NUM_MAP[day_str]
    else:
        day_transfered = '01'
    res = '{}-{}-{}'.format(year_transfered, month_transfered, day_transfered)
    return res


def filter_yingyezhizhao_zhuceziben(ziben_str):
    start_index = 0
    end_index = len(ziben_str)
    for i in range(0, len(ziben_str)):
        if ziben_str[i] not in MONEY_BIG_CHARS:
            continue
        else:
            start_index = i
            break

    for i in range(1, len(ziben_str)):
        if ziben_str[len(ziben_str) - i] not in MONEY_BIG_CHARS:
            continue
        else:
            end_index = len(ziben_str) - i
            break

    ziben_filtered = ziben_str[start_index:end_index + 1]
    print('start_index,end_index,ziben_filtered',
          start_index, end_index, ziben_filtered)
    return ziben_filtered


def is_valid_idcard_id_no(id_no: str) -> bool:
    """
    规则
    """
    if id_no is None:
        return False

    if len(id_no) != 18:
        return False

    pos_weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    valid_checkbits = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    pos_sum = 0
    for i in range(17):
        c = id_no[i]
        if not str.isdigit(c):
            return False

        pos_sum += (int(c) * pos_weight[i])

    pos_sum %= 11
    checkbit = valid_checkbits[pos_sum]

    if checkbit == id_no[-1]:
        return True

    return False


def remove_none_num(text: str or None) -> str or None:
    """去除字符串中的非数字部分，返回纯数字字符串"""
    if text is None:
        return None
    return ''.join([c for c in text if str.isdigit(c)])


def count_num_eng(text: str) -> int:
    if text is None:
        return 0
    count = 0
    for c in text:
        if str.isdigit(c) or c in ENG_CHARS:
            count += 1
    return count


def count_num(text: str) -> int:
    if text is None:
        return 0

    count = 0
    for c in text:
        if str.isdigit(c):
            count += 1

    return count


def count_special(text, special):
    """
    统计每个字符串中某个字符的个数
    :param text:
    :param special:
    :return:
    """
    assert len(special) == 1, 'special words must be an char'
    count = 0
    for char in text:
        if char == special:
            count += 1
    return count


def count_alpha(text: str) -> int:
    """
    统计字符串中英文字符的数量
    :param text:
    :return:
    """
    count = 0
    for c in text:
        if c.isalpha():
            count += 1
    return count


def count_max_continous_num(text: str) -> int:
    """

    :param text: 带有数字的字符串
    :return: 返回，最长的连续的数字的个数
    """
    max_count = 0
    cur_count = 0
    for idx in range(len(text)):
        if text[idx].isdigit():
            cur_count += 1
        else:
            if cur_count >= max_count:
                max_count = cur_count
            cur_count = 0
    if cur_count > max_count:
        max_count = cur_count
    return max_count


def count_upper_eng(text: str) -> int:
    if not text:
        return 0
    return len(re.sub('[^A-Z]', '', text))


def str_sbc_2_dbc(ustring):
    """
    全角字符转半角字符
    参见：https://www.jianshu.com/p/a5d96457c4a4
    :param ustring:
    :return:
    """
    rstring = ''
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 0x3000:  # 空格全角
            inside_code = 0x0020  # 空格半角
        elif 0xFF01 <= inside_code <= 0xFF5E:  # 其余字符的全角
            inside_code -= 0xFEE0  # 转半角
        rstring += chr(inside_code)

    return rstring


def is_none_or_empty(s: str or None) -> bool:
    """判断字符串是否为None或空串"""
    if s is None:
        return True
    return len(s) == 0


def is_none_or_white_space(s: str or None) -> bool:
    """判断字符串是否为空或纯空格串"""
    if s is None:
        return True
    return len(s.strip(' ')) == 0


def batch_replace(text: str or None, pairs: Dict[str, str]) -> str or None:
    """
    批量替换文本中的内容。
    输入为"天让只能"，pairs = { '天让': '天壤', '只能': '智能' }， 则输出为"天壤智能"
    :param text: 原始字符串
    :param pairs: { 旧文本: 新文本 }
    :return:
    """
    if text is None:
        return None
    next_text = text
    for old_text, new_text in pairs.items():
        next_text = next_text.replace(old_text, new_text)
    return next_text


def replace_when(text: str or None, pairs: Dict[str, str]) -> str or None:
    """
    批量替换文本，当输入text 和 pair.key 完全相等时， 替换为pair.value。
    如输入为"天壤只能"，pairs = {'天壤只能':'天壤智能'}， 则输出为"天壤智能"。
    当输入为"天壤只能"，pairs = {'天壤只': '天壤智'}，则不进行替换，输出为"天壤只能"
    :param text: 原始字符串
    :param pairs: { 旧文本: 新文本 }
    :return:
    """
    if text is None:
        return None
    next_text = text
    for old_text, new_text in pairs.items():
        if next_text == old_text:
            next_text = new_text
    return next_text


def find_sub(text: str, find_len: int, key: Callable, reverse=False, start_index=0) -> Tuple[int, int] or None:
    """
    查找满足条件的子串
    :param text: 被查找文本
    :param find_len: 查找的文本长度
    :param key: 过滤条件函数，参数为子串
    :param start_index: 起始位置
    :return: 返回查找到的第一个满足条件的字符串的位置或None，如示例返回'02'的位置(5,7)
    """
    if reverse:
        start = len(text) - find_len
        stop = start_index - 1
        step = -1
    else:
        start = start_index
        stop = len(text) - find_len + 1
        step = 1
    for i in range(start, stop, step):
        if key(text[i:i + find_len]):
            return i, i + find_len
    return None


def normalize(text: str) -> str:
    """
    把中文的符号转成英文符号
    """
    if not text:
        return ''

    # unicode有个normalize的过程，按照unicode标准，有C、D、KC、KD四种，KC会将大部分的中文标点符号转化为对应的英文，还会将全角字符转化为相应的半角字符
    res = unicodedata.normalize('NFKC', text)
    return res


def digitalizing(text: str, mapper=lambda x, index, collected: '0') -> str:
    """
    字符串数字化，把字符串中的非数字部分转换成数字，
    :param text:
    :param mapper: (当前需要转换的非数字字符:str, 当前索引号:int, 当前已经收集到的字符列表[str])->str。
        如原始字符串为'123.A0',当前正在处理字符A，则参数为('A', 4, ['1','2','3','.'])
    :return:
    """
    if str.isnumeric(text):
        return text
    collected = []
    for i in range(len(text)):
        c = text[i]
        if c == '.' or str.isnumeric(c):
            collected.append(c)
        else:
            collected.append(mapper(c, i, collected))
    return ''.join(collected)


def add_dot(text: str, business_min: float, business_max: float) -> Optional[str]:
    """
    补全小数点。该方法不做字符识别错误的纠正，如text=1230000a, min=123, max=999,则返回123.0000a
    :param text: 待补全小数点的文本
    :param business_max: 业务上的最大值
    :param business_min: 业务上的最小值
    :return: 补全后的字符串或None（如果怎么加都不满足业务大小限制）
    """

    def mapper(c: str, idx: int, collected: [str]) -> str:
        min_str = str(business_min)
        if idx < len(min_str):
            return min_str[idx]
        return '0'

    all_num_text = digitalizing(text, mapper)
    for i in range(1, len(all_num_text) + 1):
        if business_min <= float(all_num_text[:i]) <= business_max:
            return f'{text[:i]}.{text[i:]}'
    return None


def to_int(text: str, default_value=None) -> Optional[int]:
    """转成整数，如果失败返回默认值"""
    try:
        return int(text)
    except:
        return default_value


def to_float(text: str, default_value=None) -> Optional[float]:
    """是否可转成浮点型，如'123'、'123.456'"""
    try:
        return float(text)
    except:
        return default_value


def digital_to_chinese(digital, use_yuan='元'):
    assert use_yuan in ['元', '圆']
    if not digital:
        return
    str_digital = str(digital)
    chinese = {'1': '壹', '2': '贰', '3': '叁', '4': '肆', '5': '伍', '6': '陆', '7': '柒', '8': '捌', '9': '玖', '0': '零'}
    chinese2 = ['拾', '佰', '仟', '万', '厘', '分', '角']
    jiao = ''
    bs = str_digital.split('.')
    yuan = bs[0]
    if len(bs) > 1:
        jiao = bs[1]
    r_yuan = [i for i in reversed(yuan)]
    count = 0
    for i in range(len(yuan)):
        if i == 0:
            r_yuan[i] += use_yuan
            continue
        r_yuan[i] += chinese2[count]
        count += 1
        if count == 4:
            count = 0
            chinese2[3] = '亿'

    s_jiao = [i for i in jiao][:3]  # 去掉小于厘之后的
    j_count = -1
    for i in range(len(s_jiao)):
        s_jiao[i] += chinese2[j_count]
        j_count -= 1
    last = [i for i in reversed(r_yuan)] + s_jiao
    last_str = ''.join(last)
    for i in range(len(last_str)):
        digital = last_str[i]
        if digital in chinese:
            last_str = last_str.replace(digital, chinese[digital])

    return last_str


def get_check_bit(num17):
    """
    获取身份证最后一位，即校验码
    :param num17: 身份证前17位字符串
    :return: 身份证最后一位
    """
    Wi = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_code = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
    zip_wi_num17 = zip(list(num17), Wi)
    S = sum(int(i) * j for i, j in zip_wi_num17)
    Y = S % 11
    return check_code[Y]


def extract_valid_id_no(text):
    """

    :param text 行驶证字符串
    :return: 如果可能提取出身份证，那么就提取出
    """
    if len(text) < 18:
        if len(text) == 17:
            if text[6:8] in ['19', '20', '21'] and float(text[10:11]) <= 12 and float(text[12:13]) <= 31:
                last_pos = get_check_bit(text)
                return text + last_pos
            if text[5:7] in ['19', '20', '21'] and float(text[9:10]) <= 12 and float(text[11:12]) <= 31:
                for start_pos in range(10):
                    if get_check_bit(str(start_pos) + text[:-1]) == text[-1]:
                        return str(start_pos) + text
            return text

    else:
        for i in range(len(text) - 18 + 1):
            prob_license = text[i: i + 18]
            last = get_check_bit(prob_license[:17])
            if last == prob_license[17]:
                return prob_license
    return text


def format_crnn_amount_res(text):
    """

    :param text: crnn 重识别的结果，可能会带有 . , _ ,需要进行清理
    :return:  text: numeric format data
    """
    if not text:
        return text
    split_res = re.split(',|\.|_', text)
    split_res = [num for num in split_res if num]
    if len(split_res) == 3:
        text = split_res[0] + split_res[1] + '.' + split_res[2]
    if len(split_res) == 2:
        text = split_res[0] + '.' + split_res[1]
    return text


def date_format_scores(year_text, month_text, day_text):
    def _trim(scores):
        if scores > 1:
            scores = 1
        return scores

    scores = [0, 0, 0]
    if year_text:
        year_score = _trim(len(year_text) / 4)
        scores[0] = year_score
    if month_text:
        month_score = _trim(len(month_text) / 2)
        scores[1] = month_score
    if day_text:
        day_score = _trim(len(day_text) / 2)
        scores[2] = day_score
    return scores


def money_char_clean(text: str):
    if not text:
        return text
    text = only_keep_money_char(text)
    text = remove_last_dot(text)
    text = remove_extra_dot(text)
    only_zero = contain_only_special(text, '0')
    if only_zero:
        text = '0.00'
    return text


def is_float(text: str) -> bool:
    try:
        float(text)
        return True
    except:
        return False


def convert_financial_number(text):
    """

    :param text: 类似于  129,812,599.18 的数字
    :return: 129812599.18 形式的数字
    """
    # if re.match('^（[0-9,\.]*）$',text):
    #     re.sub('（|）','',text)
    #     text = '-' + text
    text_ = text.replace('，', ',')
    text_ = re.sub('[^\-0-9，,\.]', '', text_)
    if not text_:
        return text
    text = text_.strip()
    if re.match('^[0-9]{1,}$', text):
        return text

    # 首先，完成多个点的清理工作
    dot_loc = []
    for idx, char in enumerate(text):
        if char == '.':
            dot_loc.append(idx)
    if len(dot_loc) >= 2:
        text = ''.join([char for idx, char in enumerate(text) if idx not in dot_loc[:-1]])

    if re.match('^(-)?([0-9]*,)+[0-9]{1,}\.[0-9]*$', text):
        return re.sub(',', '', text)
    if re.match('^(-)?[0-9,]*$', text):
        return re.sub(',', '', text)
    return text


def sequence_match(long_str: str, query_str: str, threshold=0.8) -> bool:
    """
    在 long_str 中找与 query_str 相似的子序列
    threshold 代表判断子序列与 query_str 是否相似的阈值，如果 len(子序列)/len(query_str) >= threshold，则返回 True
    Args:
        long_str:
        query_str:
        threshold:

    Returns:

    """
    s = difflib.SequenceMatcher(None, long_str, query_str)
    out = []

    # i: long_str 中的索引
    # j: query_str 中的索引
    # n: 每一个 matching block 的长度
    for i, j, n in s.get_matching_blocks():
        if not n:
            continue
        out.append(long_str[i : i + n])

    match = "".join(out)
    simility = len(match) / len(query_str)
    if simility >= threshold:
        return True
    return False
