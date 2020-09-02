# encoding=utf-8
from __future__ import unicode_literals

import datetime as dt
import re
from datetime import datetime
from typing import List, Tuple

from . import str_util

MIN_YEAR, MAX_YEAR = 1987, 2028


def is_legal_date(year: int, month: int, day: int, min_year=MIN_YEAR, max_year=MAX_YEAR) -> bool:
    """
    判断日期是否合法
        1. 先判断能否构成日期
        2. 再判断年份是否在允许的范围内
    :param year:
    :param month:
    :param day:
    :return:
    """
    try:
        d = datetime(year=year, month=month, day=day)
        if min_year <= d.year <= max_year:
            return True
        return False
    except Exception:
        return False


def contain_number(node_content: str) -> bool:
    if_contain_number = False
    for c in node_content:
        if c.isdigit():
            if_contain_number = True
    return if_contain_number


def is_legal_format_date_str(date_str: str, min_year=MIN_YEAR, max_year=MAX_YEAR) -> bool:
    """
    判断是否为一个合法的日期字符串
        1. 认为合法的字符串是以 '-' 作为日期的分隔符的
    :param date_str:  2017-09-08
    """
    try:
        year_str, month_str, day_str = date_str.split('-')
        return is_legal_date(int(year_str), int(month_str), int(day_str), min_year=min_year, max_year=max_year)
    except Exception:
        return False


def get_format_data_from_crnn_num_model_res(crnn_res):
    """
    :param crnn_res: 日期专用识别模型的输出结果，日期之间可能会包含一个或多个空格, 也可能有小数点
    """
    if crnn_res is None:
        return None

    crnn_res = crnn_res.replace('.', '')
    crnn_res_without_space = crnn_res.replace(' ', '')

    if len(crnn_res_without_space) < 6:
        return None

    res = None

    if len(crnn_res_without_space) == 8:
        # 20170607 -> 2017-06-07
        res = get_format_date_from_num_str(crnn_res_without_space, month_len=2)
    elif len(crnn_res_without_space) == 6:
        # 201715 -> 2017-01-05
        res = get_format_date_from_num_str(crnn_res_without_space, month_len=1)
    else:
        # 根据空格来处理
        nums = crnn_res.split(' ')

        # 数字之间可能有多个空格，要移除空字符
        nums = list(filter(lambda x: x != '', nums))
        nums = nums[:3]

        crnn_res_without_space = ''.join(nums)

        if len(crnn_res_without_space) == 7:
            if len(nums) == 3:
                # ['2017', '8', '26']
                # ['2017', '11', '2']
                res = format_date(nums[0], nums[1], nums[2])
            else:
                res = try_get_format_date_from_7str(crnn_res_without_space)
        else:
            if len(nums) == 3:
                # ['2017', '8', '26']
                # ['2017', '11', '2']
                res = format_date(nums[0], nums[1], nums[2])
            elif len(nums) == 2 and len(nums[0]) > 4 and len(nums[1]) <= 2:
                # ['20174', '24']
                # ['201712', '4']
                res = format_date(nums[0][:4], nums[0][4:], nums[1])

    return res


def try_get_format_date_from_7str(num_str: str) -> str:
    """
    如果字符串是 7 位会有歧义，不能通过位数来判断年月日，如 2017115 可能为 2017-01-15 或 2017-11-05
    月为个位数的概率较大，所以先尝试第五位数为月
    :param num_str:
    :return: 2017-07-09
    """
    if len(num_str) != 7:
        raise AssertionError('length of num_str must be 7')
    res = get_format_date_from_num_str(num_str, 1)

    if not is_legal_format_date_str(res):
        res = get_format_date_from_num_str(num_str, 2)

    return res


def get_format_date_from_num_str(num_str, month_len):
    """
    :param num_str:
    :param month_len: 1 month 为个位数, 2 month 为十位数
    :return:
    """
    assert len(num_str) == 7 or len(num_str) == 8 or len(num_str) == 6

    res = None
    if month_len == 1:
        res = format_date(num_str[0:4],
                          num_str[4:5],
                          num_str[5:])
    elif month_len == 2:
        res = format_date(num_str[0:4],
                          num_str[4:6],
                          num_str[6:])
    return res


def format_date(year, num, day):
    """
    :param year: int or str 2017
    :param num: int or str
    :param day: int or str
    :return:  2017-01-02
    """
    if not isinstance(year, int):
        year = str_util.filter_num(year)

    if not isinstance(num, int):
        num = str_util.filter_num(num)

    if not isinstance(day, int):
        day = str_util.filter_num(day)

    return '{}-{:02}-{:02}'.format(int(year), int(num), int(day))


def is_all_num(text):
    for c in text:
        if c not in '0123456789':
            return False
    return True


def get_format_date_from_serialnum(serial_num, start):
    """
    从序列号中获得年月日(170809)，如果对应位置是英文字母则返回 None
    :param serial_num:
    :param start: included
    :return:  int  (year, month, day)
    """
    date_str = serial_num[start:start + 6]

    if not is_all_num(date_str):
        return None

    year = int('20' + date_str[:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])

    return year, month, day


def get_format_date_from_text(text):
    temp_list = []
    now_number = ''
    for c in text:
        if '0' <= c <= '9':
            now_number += c
        else:
            temp_list.append(now_number)
            now_number = ''
    temp_list.append(now_number)

    number_list = []
    for candidate_number in temp_list:
        try:
            v = int(candidate_number)
            number_list.append(v)
        except Exception as e:
            pass

    date_list = []
    n = len(number_list)
    for i in range(n - 2):
        year = number_list[i]
        month = number_list[i + 1]
        day = number_list[i + 2]
        if is_legal_date(year, month, day):
            date_list.append('{}-{:02}-{:02}'.format(year, month, day))
    return date_list


def get_format_date_diff(start_date: str, end_date: str, date_format="%Y-%m-%d"):
    a = datetime.strptime(start_date, date_format)
    b = datetime.strptime(end_date, date_format)
    delta = b - a
    return delta.days


def get_shift_date(start_date: str, shift: int, date_format="%Y-%m-%d"):
    start = datetime.strptime(start_date, date_format)
    shift = dt.timedelta(shift)
    end = start + shift
    return str(end.date())


def is_legal_month(month: str):
    try:
        int(month)
    except:
        return False
    if int(month) <= 12 and int(month) >= 1:
        return True
    else:
        return False


def is_legal_day(day: str):
    try:
        int_day = int(day)
    except:
        return False

    if int(day) >= 1 and int(day) <= 31:
        return True
    else:
        return False


def is_legal_year(year):
    try:
        int_year = int(year)
    except:
        return False
    if year:

        if int(year) > 1960 and int(year) <= datetime.now().year + 40:
            return True
        else:
            return False
    return False


def is_format_year(year):
    # 用于证明应该是一个年份一类的东西
    if year[0] in ['2', '1'] and len(year) >= 4:
        return True
    else:
        return False


def is_format_date(year, month, day):
    return is_legal_year(year) and is_legal_month(month) and is_legal_day(day)


def filter_year_month_day(passed_nodes):
    """
    用于解决'2017-11-28_9:20:38'这种长的日期
    :param time_info:
    :return:
    """
    changed_res = []
    for node in passed_nodes.values():
        org_text = node.text
        org_text = org_text.replace('年', '').replace('月', '').replace('日', '')
        split_text = re.split('-|:|_|\.', org_text)
        split_text = list(filter(lambda x: x != '', split_text))
        split_text = [str_util.keep_num_char(text) for text in split_text]
        if sum([row.isdigit() for row in split_text]) > 3:
            # 认为存在日期，只保留前三个像日期的字段
            if is_format_date(split_text[0], split_text[1], split_text[2]):
                changed_text = '-'.join(split_text[:3])
                changed_res.append([node.text, changed_text])
                node.text = changed_text

    return changed_res


def greedy_search_content(content: str):
    if len(content) == 3:
        # 现在只处理这种情况
        if content[0] == '0':
            # 应对如 033 的情形
            return content[:2]
    return content


def get_useful_info(crnn_res: str):
    # 首先按照 空格进行 分组：
    crnn_res = crnn_res.replace('.', ' ')
    crnn_res_split = list(filter(lambda x: x != '', crnn_res.split(' ')))
    useful_info = {'useful_year': None, 'useful_month': None, 'useful_day': None}
    format_order = [is_legal_year, is_legal_month, is_legal_day]
    format_name = ['useful_year', 'useful_month', 'useful_day']
    if len(crnn_res_split) == 3:
        if len(crnn_res_split[0]) >= 3:
            # 考虑  ['201707', '06', '34']
            if len(crnn_res_split[0]) == 6:
                if is_legal_year(crnn_res_split[0][:4]) and \
                        is_legal_month(crnn_res_split[0][4:]) and \
                        is_legal_day(crnn_res_split[1]):
                    useful_info['useful_year'] = crnn_res_split[0][:4]
                    useful_info['useful_month'] = crnn_res_split[0][4:]
                    useful_info['useful_day'] = crnn_res_split[1]
            else:
                # 针对 20xx, xx, xx
                for name, type_, content in zip(format_name, format_order, crnn_res_split):
                    if type_(content):
                        useful_info[name] = content
                    else:
                        content_greedy_search = greedy_search_content(content)
                        if type_(content):
                            useful_info[name] = content
        else:
            # 有两种情形， 一种是 07-26-17 和 20 03 24 两个qingxing
            # 针对 07-26-17 两种情形，只做 07-26的部分
            if crnn_res_split[0].startswith('20'):
                concat_last_two = ' '.join(crnn_res_split[1:])
                return get_useful_info(concat_last_two)
            concat_first_two = ' '.join(crnn_res_split[:2])
            return get_useful_info(concat_first_two)
    if len(crnn_res_split) == 2:
        if is_format_year(crnn_res_split[0]):
            if is_legal_year(crnn_res_split[0]):
                useful_info['useful_year'] = crnn_res_split[0]
            # 分析第二个部分是什么样的：
            # 比如 '20xx 06'
            if len(crnn_res_split[1]) == 2:
                # 优先提取月份信息
                if is_legal_month(crnn_res_split[1]):
                    useful_info['useful_month'] = crnn_res_split[1]
                elif is_legal_day(crnn_res_split[1]):
                    useful_info['useful_day'] = crnn_res_split[1]
            if len(crnn_res_split[1]) == 4:
                if is_legal_month(crnn_res_split[1][:2]):
                    useful_info['useful_month'] = crnn_res_split[1][:2]
                if is_legal_month(crnn_res_split[1][-2:]):
                    useful_info['useful_day'] = crnn_res_split[1][-2:]
            if len(crnn_res_split[1]) == 3:
                greedy_res = greedy_search_content(crnn_res_split[1])
                if is_legal_month(greedy_res):
                    useful_info['useful_month'] = greedy_res
                elif is_legal_day(greedy_res):
                    useful_info['useful_day'] = greedy_res
        else:
            # 可能识别出了月和日
            # '06 03'
            if is_legal_month(crnn_res_split[0]):
                useful_info['useful_month'] = crnn_res_split[0]
            if is_legal_day(crnn_res_split[1]):
                useful_info['useful_day'] = crnn_res_split[1]

    return useful_info


def recover_info_from_useful_info(split_res, useful_info):
    text = split_res[0]
    date = datetime.strptime(text, '%Y-%m-%d')
    kwargs = {k.replace('useful_', ''): int(v) for k, v in useful_info.items() if v is not None}
    result = str(date.replace(**kwargs).date())
    return result, split_res[1]


def convert_list_of_date_to_datetime(date_list: List[str], format='%Y-%m-%d'):
    date_format_list = [datetime.strptime(date, format) for date in date_list]
    return date_format_list


def convert_datetime_2_list_of_str(date_format_list):
    return [str(date.date()) for date in date_format_list]


def get_max_diff_of_year_month(date_list: List):
    """
    给一系列的date，算出 年份的最大差距，和 月份的最大差距
    """

    max_year_diff = -1
    max_month_diff = -1
    for idx1, day1 in enumerate(date_list):
        for idx2, day2 in enumerate(date_list):
            if idx2 > idx1:
                year_diff = abs(day1.year - day2.year)
                month_diff = abs(day1.month - day2.month)
                max_year_diff = max(max_year_diff, year_diff)
                max_month_diff = max(max_month_diff, month_diff)
    return max_year_diff, max_month_diff


def judge_date_order(date_list: List):
    """
    判断date_list 中的日期是否是按照顺序的
    """

    flag = True
    for idx, date in enumerate(date_list):
        if idx > 0:
            if date < date_list[idx - 1]:
                flag = False
    return flag


def recover_info_by_year(date_list: List, stay_num):
    if stay_num == '' or stay_num is None:
        stay_num = '1'  # 即不做任何特殊处理
    start_year = date_list[0].year
    end_year = date_list[1].year
    ad_year = date_list[2].year
    shift = dt.timedelta(int(stay_num))
    # 由于addmission date的年份预测的可能会比前面的年份准，所以可以考虑用addmisison date 来恢复
    if start_year != end_year and (start_year > ad_year or end_year > ad_year):
        date_list[1] = date_list[1].replace(year=ad_year)
        predict_start = date_list[1] - shift
        date_list[0] = date_list[0].replace(year=predict_start.year)
        return date_list

    if abs(end_year - ad_year) <= 1:
        predict_start = date_list[1] - shift
        try:
            date_list[0] = date_list[0].replace(year=predict_start.year)
        except:
            # 报错是因为出现了 2018 - 2- 29 ,但是2018 年的二月没有29号
            pass

    elif abs(start_year - ad_year) <= 1:
        predict_end = date_list[1] + shift
        date_list[1] = date_list[1].replace(year=predict_end.year)
    return date_list


def recover_info_by_month(date_list: List, stay_num):
    if not stay_num:
        stay_num = '1'  # 不做特殊处理
    start_month = date_list[0].month
    end_month = date_list[1].month
    ad_month = date_list[2].month
    stay_num = int(stay_num)
    shift = dt.timedelta(stay_num)
    if abs((date_list[1] - date_list[0]).days - stay_num) < 10:
        return date_list
    elif abs(end_month - ad_month) <= 1:
        # 是 start 和 他们差的很多
        predict_start = date_list[1] - shift
        date_list[0] = date_list[0].replace(month=predict_start.month)
    elif abs(start_month - ad_month) <= 1:
        predict_end = date_list[0] + shift

        date_list[1] = date_list[1].replace(month=predict_end.month)
        # 如果这时候不合法，但是把信息偏移到ad时合法，则偏移至ad的月份
        if not (date_list[0] <= date_list[1]) and (date_list[1] <= date_list[2]):
            date_list[1] = date_list[1].replace(month=date_list[2].month)

    else:
        # TODO bugs here
        pass
        # date_list[2] = date_list[2].replace(month=end_month)

    return date_list


def greedy_infer_on_ad(date_list, stay_num):
    pass


def predict_date_by_relation(date_list, stay_num):
    if not stay_num:
        # 没办法执行这种推断，直接返回原始信息
        return date_list

    start, end, ad = date_list
    stay_num = int(stay_num)
    shift = dt.timedelta(stay_num)
    if end < start:
        if start + shift < ad:
            end = start + shift
        elif start + shift > ad:
            start = end - shift
    elif end > ad:
        if start + shift <= ad:
            end = start + shift
        else:
            # 现在是 ad 小于 end 的情况
            # 尝试 10天 10天的加，在该月内进行尝试
            if (ad + dt.timedelta(10)) > end and (ad + dt.timedelta(10)).month == end.month:
                ad = ad + dt.timedelta(10)
            else:
                if (ad + dt.timedelta(20)) > end and (ad + dt.timedelta(20)).month == end.month:
                    ad = ad + dt.timedelta(20)
    elif start <= end and end <= ad and end - start != shift:
        # 即，存在end 和 start 没有办法和 shift 相对应，
        # 处理方法为，计算 start+shift 和 stay 哪一个和 ad 更近，如果 start+ shift 和ad 更近，则认为 end 出错，否则 start 出错
        predict_end = start + shift
        if predict_end < ad:
            # 证明这是一个合法推断
            if predict_end > end and (predict_end - end).days >= 5:
                # 认为是 end 出错了
                end = start + shift
            elif predict_end < end and (end - predict_end).days >= 5:
                start = end - shift
        else:
            pass
            # if end <= ad:
            #     start = end - shift

    return [start, end, ad]


def get_max_days_of_month(year: int, month: int) -> int:
    """
    计算一个月中的最大天数
    :param year: 当前年份
    :param month: 当前月份
    :return:
    """
    if month == 2:
        return 29 if (year % 100 == 0 and year % 4 == 0) or year % 4 == 0 else 28
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    else:
        return 30


def format_date_fields(year: str, month: str, day: str, business_min_year=1949) -> [str] or None:
    """
    根据年月日三个数字格式化日期。注意：请把非数字部分先事先替换掉，这里只接受！！！数字的字符串！！！
    如果年份是2位，则根据后面两位是否小于业务最小年份的后两位来决定前两位是19还是20
    如果年份是3位，则第一位取决于最小年份的第二位
    如果不确定能不能使用你的业务场景，请把你的case添加到单元测试中，并commit。单元测试见test_date_util.py#test_format_date_fields
    :param year:
    :param month:
    :param day:
    :param business_min_year: 业务逻辑上的最小年份，如1949
    :return: 返回字符串数组[年,月,日]（如['2019', '01', '23']）或None
    """
    if str_util.is_none_or_white_space(year) or str_util.is_none_or_white_space(
            month) or str_util.is_none_or_white_space(day):
        return None
    year_len = len(year)
    if year_len < 2:
        return None
    if year_len == 2:
        correct_year = _format_year_len2(year, business_min_year)
    elif year_len == 3:
        correct_year = _format_year_len3(year, business_min_year)
    elif year_len == 4:
        correct_year = _format_year_len4(year, business_min_year)
    else:
        correct_year = _format_year_gt_len4(year, business_min_year)

    if correct_year is None:
        return None
    correct_month = _format_date_month_or_day(month, 12)

    correct_day = _format_date_month_or_day(day, get_max_days_of_month(int(correct_year), int(correct_month)))

    return [correct_year, correct_month, correct_day]


def _format_year_len2(year_str: str, business_min_year: int) -> str:
    maybe_small_year = f'19{year_str}'
    maybe_big_year = f'20{year_str}'
    if int(maybe_small_year) < business_min_year:
        return maybe_big_year
    return maybe_small_year


def _format_year_len3(year_str: str, business_min_year: int) -> str:
    maybe_small_year = f'1{year_str}'
    maybe_big_year = f'2{year_str}'
    if int(maybe_small_year) < business_min_year:
        return maybe_big_year
    return maybe_small_year


def _format_year_len4(year_str: str, business_min_year: int) -> str:
    # FIXME: 纯数字的4位日期纠正？
    return year_str


def _format_year_gt_len4(year_str: str, business_min_year: int) -> str or None:
    for i in range(4, len(year_str) + 1):
        maybe_year = year_str[i - 4:i]
        if int(maybe_year) > business_min_year and maybe_year[0] in ['1', '2']:
            return maybe_year
    # 如果找不到可能的year，则直接返回19或20开头的连续4位
    for i in range(4, len(year_str) + 1):
        if year_str[i - 4:i - 2] in ['19', '20']:
            return year_str[i - 4:i]
    # 还找不到，则返回None
    return None


def _format_date_month_or_day(date_str: str or None, max_num) -> str:
    """
    纠正日期中的月或日
    :param date_str: 只包含月或日的字符串，如'03'、'3'、'303'
    :param max_num: 这个数字最大多大，如果是月，则最大是12，如果是日，根据月而定
    :return: 纠正后的字符串，如'03'
    """
    if len(date_str) == 1:
        return f'0{date_str}'
    if len(date_str) > 2:
        for i in range(1, len(date_str)):
            candi_str = date_str[i - 1:i + 1]
            if int(candi_str) <= max_num:
                return candi_str
    # 长度等于2的

    # 小于最大日期，则直接返回
    if int(date_str) <= max_num:
        return date_str

    # 大于最大日期
    return f'0{date_str[0]}'


class DateParseResultItem:
    # TODO: 暂时不考虑置信度问题
    def __init__(self, original_year, original_month, original_day):
        self.original_year = original_year
        self.original_month = original_month
        self.original_day = original_day

    @property
    def formatted_fields(self) -> (str, str, str):
        """获取已经格式化好的日期字段元组（元素为字符串形式），如('2019', '01', '23')"""
        return tuple(format_date_fields(self.original_year, self.original_month, self.original_day))

    @property
    def formatted_int_fields(self) -> (str, str, str):
        """获取已经格式化好的日期字段元组（元素为整数形式），如(2019, 1, 23)"""
        return tuple(
            map(lambda x: int(x), format_date_fields(self.original_year, self.original_month, self.original_day)))

    def to_string(self, splitter='-'):
        """转成日期字符串形式， 默认使用'-'分割，结果如'2019-01-23'"""
        return splitter.join(self.formatted_fields)

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.__str__()


class DateParseResult:
    """date_util.parse_date()的结果，其中有多个可能的结果(DateParseResultItem)"""

    def __init__(self):
        self._items = []

    @property
    def certain_item(self) -> DateParseResultItem or None:
        """获取可以肯定的结果。必须保证结果的可信度时使用"""
        if len(self._items) == 0:
            return None
        item = self._items[0]
        if item.original_year is None or item.original_month is None or item.original_day is None:
            return None

        return len(item.original_year) >= 2 and len(item.original_month) == 2 and len(item.original_day) == 2

    @property
    def most_possible_item(self) -> DateParseResultItem or None:
        """获取最大可能性的结果。尽最大可能找出一个结果，而不要求结果一定正确"""
        if len(self._items) > 0:
            return self._items[0]
        return None

    def _append(self, item: DateParseResultItem) -> 'DateParseResult':
        self._items.append(item)
        return self

    def _extend(self, iterable) -> 'DateParseResult':
        self._items.extend(iterable)
        return self


def parse_date(date_str: str, min_year, max_year) -> DateParseResult:
    """
    解析日期字符串，返回所有可能的日期字段。可通过运行测试查看是否满足需要。test_date_util.py#test_parse_date
    前提条件：
        1. 该字符串中逻辑上只包含一个有效日期，但解析出来的结果可能有多个，按可能性倒序排列
        2. 该字符串中不存在数字识别错误问题，如2被识别为Z的情况已经提前被解决了
    :param date_str: 如'2019-01-23'、'2019-1-23'、'2019年1月23日'、'2019中123啊'、'20190123'、'190123'等所有人可以分辨的日期字符串
    :param min_year: 业务上的最小日期（含）
    :param max_year: 业务上的最大日期（含）
    :return: 按可能性从大到小排列
    """

    def find_year_by_len(text, year_len) -> Tuple[int, int] or None:
        def year_filter(x: str) -> bool:
            min_prefix = min_year // pow(10, year_len)
            max_prefix = max_year // pow(10, year_len)
            return min_year <= int(f'{min_prefix}{x}') <= max_year or min_year <= int(f'{max_prefix}{x}') <= max_year

        return str_util.find_sub(text, year_len, year_filter)

    def find_years(text: str) -> [str]:
        years = []
        for year_len in range(4, 1, -1):
            year_pos = find_year_by_len(text, year_len)
            if year_pos is not None:
                years.append(year_pos)
        return years

    def find_month_by_len(text, month_len, start_index):
        return str_util.find_sub(text, month_len,
                                 lambda x: str_util.is_all_num(x) and 1 <= int(x) <= 12,
                                 start_index=start_index)

    def find_months_by_len(text, month_len, start_index):
        month_poses_by_len = []
        for offset in range(len(text) - month_len + 1):
            pos = find_month_by_len(text, month_len, start_index + offset)
            if pos is None:
                break
            month_poses_by_len.append(pos)
        return month_poses_by_len

    def find_months(text, start_index) -> [str]:
        months = []
        for month_len in range(2, 0, -1):
            month_poses = find_months_by_len(text, month_len, start_index)
            if len(month_poses) > 0:
                months.extend(month_poses)
        return months

    def find_day_by_len(text, day_len, start_index):
        return str_util.find_sub(text, day_len,
                                 lambda x: str_util.is_all_num(x) and 1 <= int(
                                     x) <= 31,
                                 start_index=start_index)

    def find_days(text, start_index):
        days = []
        for day_len in range(2, 0, -1):
            day_pos = find_day_by_len(text, day_len, start_index)
            if day_pos is not None:
                days.append(day_pos)
        return days

    def parse_when_more_than_3segs(seg1, seg2, seg3) -> [DateParseResultItem]:
        result_3 = []
        year_poses = find_years(seg1)
        # TODO: 找到多个时每种组合的置信度排序
        for year_pos in year_poses:
            month_poses = find_months(seg2, 0)
            for month_pos in month_poses:
                day_poses = find_days(seg3, 0)
                for day_pos in day_poses:
                    dpr = DateParseResultItem(seg1[slice(*year_pos)], seg2[slice(*month_pos)], seg3[slice(*day_pos)])
                    result_3.append(dpr)
        return result_3

    def parse_when_more_than_2segs(seg1, seg2) -> [DateParseResultItem]:
        result_2 = []
        year_poses = find_years(seg1)

        # 年月-日的情况
        for year_pos in year_poses:
            month_poses = find_months(seg1, year_pos[1])
            for month_pos in month_poses:
                day_poses = find_days(seg2, 0)
                for day_pos in day_poses:
                    dpr = DateParseResultItem(seg1[slice(*year_pos)], seg1[slice(*month_pos)], seg2[slice(*day_pos)])
                    result_2.append(dpr)

        # 年-月日的情况
        for year_pos in year_poses:
            month_poses = find_months(seg2, 0)
            for month_pos in month_poses:
                day_poses = find_days(seg2, month_pos[1])
                for day_pos in day_poses:
                    dpr = DateParseResultItem(seg1[slice(*year_pos)], seg2[slice(*month_pos)], seg2[slice(*day_pos)])
                    result_2.append(dpr)
        return result_2

    def parse_when_one_seg(seg) -> [DateParseResultItem]:
        result_3 = []
        year_poses = find_years(seg)
        # TODO: 找到多个时每种组合的置信度排序
        for year_pos in year_poses:
            month_poses = find_months(seg, year_pos[1])
            for month_pos in month_poses:
                day_poses = find_days(seg, month_pos[1])
                for day_pos in day_poses:
                    dpr = DateParseResultItem(seg[slice(*year_pos)], seg[slice(*month_pos)], seg[slice(*day_pos)])
                    result_3.append(dpr)
        return result_3

    # 按非数字进行分割
    date_segs = re.split(r'\D+', date_str)
    segs_len = len(date_segs)
    if segs_len == 0:
        return ()
    # TODO: 提前对可以确认的情况进行判断，直接返回
    # 2-4年1-2月1-2日
    # 可能的分布情况：
    # 1. 年-月-日：至少有三段，且相邻的三段各包含年月日
    # 2. 年月-日：至少有两段，且年份所在段后面有月份，且年份后面的段有日
    # 3. 年-月日：至少有年份所在段后面没有月份，且年份后面的段同时包含月日
    # 4. 年月日：至少有一段同时含有年月日信息
    result = DateParseResult()
    if segs_len >= 3:
        for seg_idx in range(segs_len - 2):
            result._extend(
                parse_when_more_than_3segs(date_segs[seg_idx], date_segs[seg_idx + 1], date_segs[seg_idx + 2]))
    if segs_len >= 2:
        for seg_idx in range(segs_len - 1):
            result._extend(parse_when_more_than_2segs(date_segs[seg_idx], date_segs[seg_idx + 1]))
    for seg_idx in range(segs_len):
        result._extend(parse_when_one_seg(date_segs[seg_idx]))

    def sort_result_key(dpr: DateParseResultItem):
        return len(dpr.original_day) + len(dpr.original_month) + len(dpr.original_year)

    result._items.sort(key=sort_result_key, reverse=True)
    return result


def translate_chinese_time(data_str: str) -> str:
    """
    二〇一四年三月十七日  -> 2014年3月17日
    :param data_str:
    :return:
    """
    chinese_number_dict = {
        '一': '1', '二': '2', '三': '3',
        '四': '4', '五': '5', '六': '6',
        '七': '7', '八': '8', '九': '9',
        '〇': '0', 'O': '0', 'o': '0','零': '0',
        '十': '1'
    }
    out = ''
    for c in data_str:
        out += chinese_number_dict.get(c, c)
    return out
