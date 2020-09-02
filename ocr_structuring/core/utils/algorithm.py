import math
from typing import Callable

import numpy as np


def ternary_max_search(left: float, right: float, cal_fn: Callable, cal_fn_key: Callable = None, eps: float = 1e-5):
    """
    三分法最大值搜索最大值
    :param left: 左值
    :param right: 右值
    :param cal_fn: 计算函数，调用的参数为 mid value
    :param cal_fn_key: 处理 cal_fn 的返回值，选择作为 value 判断的值
    :param eps: 停止条件
    :return:
        left: 取到最大值时搜索到的值
        result: 取到最大值时 cal_fn 的返回值
    """
    result = None
    while left + eps < right:
        m1 = left + (right - left) / 3
        m2 = right - (right - left) / 3
        v1 = cal_fn(m1)
        v2 = cal_fn(m2)

        _v1 = cal_fn_key(v1) if cal_fn_key else v1
        _v2 = cal_fn_key(v2) if cal_fn_key else v2

        if _v1 < _v2:
            left = m1
            result = v2
        else:
            right = m2
            result = v1

    return left, result


def ternary_max_search2(left: float, right: float, cal_fn: Callable, cal_fn_key: Callable = None, eps: float = 1e-5):
    """
    三分法最大值搜索最大值
    :param left: 左值
    :param right: 右值
    :param cal_fn: 计算函数，调用的参数为 mid value
    :param cal_fn_key: 处理 cal_fn 的返回值，选择作为 value 判断的值
    :param eps: 停止条件
    :return:
        left: 取到最大值时搜索到的值
        result: 取到最大值时 cal_fn 的返回值
    """
    result = None
    while left + eps < right:
        # m1 = left + (right - left) / 3
        # m2 = right - (right - left) / 3
        m1 = (left + right) / 2
        m2 = (m1 + right) / 2
        v1 = cal_fn(m1)
        v2 = cal_fn(m2)

        _v1 = cal_fn_key(v1) if cal_fn_key else v1
        _v2 = cal_fn_key(v2) if cal_fn_key else v2

        if _v1 < _v2:
            left = m1
            result = v2
        else:
            right = m2
            result = v1

    return left, result


def max_sub_seq_order_dp(seq, seq_order):
    """
    seq: string to be corrected
    seq_order: string of the target
    dp: 2-D array to compute
    Return:
        - common sub seq of key word
        - indexes of key word in seq
        - indexes of key word in seq_order
    """
    res_seq = ''
    seq_indexes = []
    seq_order_indexes = []
    if not seq or len(seq) > 100:
        return res_seq, seq_indexes, seq_order_indexes
    n = len(seq)
    m = len(seq_order)
    dp = [[[-1, 0] for j in range(m)] for i in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(m)[::-1]:
            dp[i][j][0] = -1
            dp[i][j][1] = dp[i - 1][j][1]
            if seq[i - 1] == seq_order[j]:
                if dp[i][j][1] == 0:
                    dp[i][j][0] = -2
                    dp[i][j][1] = 1
                for k in range(j):
                    if dp[i - 1][k][1] + 1 > dp[i][j][1]:
                        dp[i][j][1] = dp[i - 1][k][1] + 1
                        dp[i][j][0] = k
    # for j in range(m):
    #    for i in range(n+1):
    #        print dp[i][j],
    #    print

    max_len = 0
    cur_j = -1
    for j in range(m):
        if max_len < dp[n][j][1]:
            max_len = dp[n][j][1]
            cur_j = j
    if max_len == 0:
        return res_seq, seq_indexes, seq_order_indexes
    # res_seq = seq_order[cur_j]
    i = n
    while 1:
        if len(res_seq) == max_len:
            break
        while dp[i][cur_j][0] == -1:
            # print dp[i][cur_j]
            i -= 1
        # print dp[i][cur_j]
        res_seq = res_seq + seq_order[cur_j]
        seq_indexes.append(i - 1)
        seq_order_indexes.append(cur_j)
        cur_j = dp[i][cur_j][0]
        i -= 1
    res_seq, seq_indexes, seq_order_indexes = res_seq[::-1], seq_indexes[::-1], seq_order_indexes[::-1]
    if len(res_seq) > 1:
        is_same_index = seq_indexes[0]
        for c in range(seq_indexes[0] + 1, seq_indexes[1]):
            if seq[c] == res_seq[0]:
                is_same_index = c
        diff_old = seq_indexes[1] - seq_indexes[0]
        diff_new = seq_indexes[1] - is_same_index
        diff_order = seq_order_indexes[1] - seq_order_indexes[0]
        if abs(diff_order - diff_new) < abs(diff_order - diff_old):
            seq_indexes[0] = is_same_index
    return res_seq, seq_indexes, seq_order_indexes


def order_points(pts):
    from scipy.spatial import distance as dist
    # https://www.pyimagesearch.com/2016/03/21/ordering-coordinates-clockwise-with-python-and-opencv/
    # sort the points based on their x-coordinates
    xSorted = pts[np.argsort(pts[:, 0]), :]

    # grab the left-most and right-most points from the sorted
    # x-roodinate points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]

    # now, sort the left-most coordinates according to their
    # y-coordinates so we can grab the top-left and bottom-left
    # points, respectively
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost

    # now that we have the top-left coordinate, use it as an
    # anchor to calculate the Euclidean distance between the
    # top-left and right-most points; by the Pythagorean
    # theorem, the point with the largest distance will be
    # our bottom-right point
    D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
    (br, tr) = rightMost[np.argsort(D)[::-1], :]

    # return the coordinates in top-left, top-right,
    # bottom-right, and bottom-left order
    return np.array([tl, tr, br, bl], dtype="float32")


def polygon_to_to_rectangle(bbox):
    """
    :param bbox: The polygon stored in format [x1, y1, x2, y2, x3, y3, x4, y4]
    :return: Rotated Rectangle in format [cx, cy, w, h, theta]
    """
    bbox = np.array(bbox, dtype=np.float32)
    bbox = np.reshape(bbox, newshape=(2, 4), order='F')
    angle = np.arctan2(bbox[1, 1] - bbox[1, 0] , (bbox[0, 1] - bbox[0, 0]))

    center = [[0], [0]]

    for i in range(4):
        center[0] += bbox[0, i]
        center[1] += bbox[1, i]

    center = np.array(center, dtype=np.float32) / 4.0

    R = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]], dtype=np.float32)

    normalized = np.matmul(R.transpose(), bbox - center)

    xmin = np.min(normalized[0, :])
    xmax = np.max(normalized[0, :])
    ymin = np.min(normalized[1, :])
    ymax = np.max(normalized[1, :])

    w = xmax - xmin + 1
    h = ymax - ymin + 1

    return [float(center[0]), float(center[1]), w, h, angle / np.pi * 180]
