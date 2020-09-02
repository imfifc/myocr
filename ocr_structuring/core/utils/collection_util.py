from collections import Iterable


def index(items: [] or (), condition: callable, start_index=0) -> int:
    """
    查找第一个满足某个特定条件的item的索引号并返回其索引，如果找不到则返回-1。
    :param items: list或tuple
    :param condition: 查询条件，以item为参数的函数，返回True or False
    :param start_index:
    :return:
    """
    for i in range(start_index, len(items)):
        if condition(items[i]):
            return i
    return -1


def contains_any(col: Iterable, elements: Iterable) -> bool:
    """
    判断集合col中是否存在集合elements中的任何一个
    :param col:
    :param elements:
    :return:
    """
    return any([e in col for e in elements])
