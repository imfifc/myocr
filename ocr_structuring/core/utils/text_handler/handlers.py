import re
from typing import Dict

from ...utils import str_util
from .handler import handle


def remove_symbols_handler(symbols: str, ) -> handle:
    """
    去除特殊字符
    :param symbols:
    :return:
    """

    def f(text: str) -> str or None:
        return ''.join([c for c in text if c not in symbols])

    return f


def cut_by_regex_handler(pattern: str) -> handle:
    """
    通过正则截取字符串
    :param pattern:
    :return:
    """

    def f(text: str) -> str or None:
        if str_util.is_none_or_white_space(text):
            return None
        matcher = re.search(pattern, text)
        return matcher.group(0) if matcher is not None else None

    return f


def handler_group(*handlers) -> handle:
    """
    一组处理器
    :param handlers:
    :return:
    """

    def f(text: str) -> str or None:
        input_text = text
        for handler in handlers:
            input_text = handler(input_text)
        return input_text

    return f


def replace_symbols(symbols: Dict[str, str]) -> handle:
    """
    替换一组文本
    :param symbols: {'old_str': 'new_str'}
    :return:
    """

    def f(text: str) -> str or None:
        result = text
        for old_str, new_str in symbols.items():
            result = result.replace(old_str, new_str)
        return result

    return f


def regex_matcher_handler(pattern, matcher_handler) -> handle:
    """
    正则匹配
    :param pattern:
    :param matcher_handler: 当匹配成功后，把matcher传递给处理函数进行处理
    :return:
    """

    def f(text: str) -> str or None:
        matcher = re.match(pattern, text)
        return matcher_handler(matcher) if matcher else None

    return f


def rtrim(strs: [str], max_remove_one_type=False) -> handle:
    """
    从右边移除指定的文本
    如strs=['吨','千克']，被测试字符串为'1000千克吨'，如果max_remove_one_type为False，则结果为1000，否则结果为1000千克。
    如strs=['吨','千克']，被测试字符串为'1000吨千克'，无论max_remove_one_type是否为False，结果都为1000吨。

    :param strs: 被移除的文本列表
    :param max_remove_one_type: 是否最多只移除strs中的一种
    :return:
    """
    def f(text: str) -> str or None:
        if text is None:
            return text
        next_text = text
        for s in strs:
            if text.endswith(s):
                next_text = text.rstrip(s)
        return next_text

    return f
