import math
from typing import List, Union

import numpy as np
from shapely.geometry import Polygon

from ocr_structuring.core.utils.algorithm import order_points
from ocr_structuring.protos.structuring_pb2 import RotatedBoxWithLabel


class RBox:
    def __init__(self, rotate_rect: List[int], label=-1):
        """
        :param rotate_rect: [x1, y1, x2, y2, x3, y3, x4, y4, angle]
        """
        assert len(rotate_rect) == 9
        self.update(rotate_rect)
        self.label = label

    def update(self, rotate_rect: List[int]):
        self.rotate_rect = rotate_rect

        self.x1 = rotate_rect[0]
        self.y1 = rotate_rect[1]
        self.x2 = rotate_rect[2]
        self.y2 = rotate_rect[3]
        self.x3 = rotate_rect[4]
        self.y3 = rotate_rect[5]
        self.x4 = rotate_rect[6]
        self.y4 = rotate_rect[7]
        self.angle = rotate_rect[8]

        self.center = (self.x1 + self.x3) / 2, (self.y1 + self.y3) / 2
        self.cx = self.center[0]
        self.cy = self.center[1]

        self.points = [
            (rotate_rect[0], rotate_rect[1]),
            (rotate_rect[2], rotate_rect[3]),
            (rotate_rect[4], rotate_rect[5]),
            (rotate_rect[6], rotate_rect[7]),
        ]

        self.poly = Polygon(self.points)

        self.meaningful_angle = self.get_meaningful_angle()

    def ioo(self, other: Union["RBox", Polygon]):
        if self.poly.area == 0:
            return 0
        if isinstance(other, Polygon):
            inter = self.poly.intersection(other).area
        else:
            inter = self.poly.intersection(other.poly).area
        return inter / self.poly.area

    def _is_same(self, rbox: "RBox"):
        for i in range(9):
            if self.rotate_rect[i] != rbox.rotate_rect[i]:
                return False

        return True

    def get_meaningful_angle(self):
        # 返回易于理解的angle
        # 当框为顺时针旋转时，返回的角度大于0
        ordered_points = order_points(np.array(self.points))
        self.up_left = ordered_points[0, :]
        self.up_right = ordered_points[1, :]
        self.down_right = ordered_points[2, :]
        self.down_left = ordered_points[3, :]

        angle = (
                np.arctan2(
                    [self.up_right[1] - self.up_left[1]],
                    [self.up_right[0] - self.up_left[0]],
                )
                / np.pi
                * 180
        )
        return angle[0]

    def get_relative_rbox(self, center_point, delta_l, delta_t, delta_r, delta_b,
                          angle=None):  # delta_xxx 为非负数 相对center_point的偏移
        """
        用于找和当前rbox倾斜角度一样的rbox，通常用于以背景框找前景框，center_point为锚点,delta_ltrb为各个边距锚点的距离
        """
        p1 = (-delta_l, delta_b)
        p2 = (delta_r, delta_b)
        p3 = (delta_r, -delta_t)
        p4 = (-delta_l, -delta_t)
        points = [p4, p3, p2, p1]
        # p1-4为左上角起顺时针四点的转正后坐标系的坐标，本函数目的是求该四个点转正前的坐标,注意直角坐标系y轴向上
        # 先按本rbox的angle旋转
        if angle is None:
            angle = self.meaningful_angle
        theta = -angle
        cos_theta = math.cos(theta / 180 * math.pi)
        sin_theta = math.sin(theta / 180 * math.pi)
        rotated_points = []
        for point in points:
            x = point[0] * cos_theta + point[1] * sin_theta
            y = -point[0] * sin_theta + point[1] * cos_theta
            rotated_points.append((x, y))
        # 平移，将up_left_point 从原点
        trans_point = []
        for point in rotated_points:
            x = int(point[0] + center_point[0])
            y = int(point[1] + center_point[1])
            trans_point.extend([x, y])

        return RBox([*trans_point[0:8], angle])

    @property
    def height(self):
        return np.sqrt(
            (self.up_left[0] - self.down_left[0]) ** 2
            + (self.up_left[1] - self.down_left[1]) ** 2
        )

    @staticmethod
    def from_RotatedBoxWithLabel(data: RotatedBoxWithLabel) -> "RBox":
        return RBox(
            [
                data.bbox.x1,
                data.bbox.y1,
                data.bbox.x2,
                data.bbox.y2,
                data.bbox.x3,
                data.bbox.y3,
                data.bbox.x4,
                data.bbox.y4,
                data.bbox.angle,
            ],
            label=data.label,
        )

    @property
    def width(self):
        return np.sqrt(
            (self.up_left[0] - self.up_right[0]) ** 2 + \
            (self.up_left[1] - self.up_right[1]) ** 2
        )

    def __eq__(self, other: "RBox"):
        return self._is_same(other)

    def __ne__(self, other: "RBox"):
        return not self._is_same(other)

    def __getitem__(self, index):
        return self.rotate_rect[index]

    def __len__(self):
        return len(self.rotate_rect)

    def __str__(self):
        return "[%.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f]" % tuple(self.rotate_rect)
