import math
from typing import List, Tuple

from ..utils import geometry_cal


class BBox:
    """
    表示一个水平的文本框区域
    """

    def __init__(self, rect: List[int]):
        """
        Args:
            rect: [left, top, right, bottom]
        """
        self.update(rect)

    @property
    def left_top_pnt(self):
        """
        返回左上角点

        Returns:
            (x, y)
        """
        return self.rect[0], self.rect[1]

    @property
    def right_bottom_pnt(self):
        """
        返回右下角点

        Returns:
            (x, y)

        """
        return self.rect[2], self.rect[3]

    @property
    def left_top_bbox(self) -> 'BBox':
        """
        返回当前 BBox 的左上区域
        """
        return BBox([self.left, self.top, self.cx, self.cy])

    @property
    def right_top_bbox(self) -> 'BBox':
        """
        返回当前 BBox 的右上区域
        """
        return BBox([self.cx, self.top, self.right, self.cy])

    @property
    def left_bottom_bbox(self) -> 'BBox':
        """
        返回当前 BBox 的左下区域
        """
        return BBox([self.left, self.cy, self.cx, self.bottom])

    @property
    def right_bottom_bbox(self) -> 'BBox':
        """
        返回当前 BBox 的左下区域
        """
        return BBox([self.cx, self.cy, self.right, self.bottom])

    def contain(self, bbox: 'BBox') -> bool:
        """
        判断是否完全包含一个 BBox
        """
        if self.top > bbox.top:
            return False

        if self.bottom < bbox.bottom:
            return False

        if self.left > bbox.left:
            return False

        if self.right < bbox.right:
            return False

        return True

    def contain_point(self, point: List[int]) -> bool:
        """
        判断是否包含一个点

        Args:
            point: (x, y)

        """
        if self.left <= point[0] <= self.right and self.top <= point[1] <= self.bottom:
            return True
        return False

    def contain_center(self, bbox: 'BBox') -> bool:
        """
        判断是否包含某个 BBox 的中心点
        """
        if self.left < bbox.cx < self.right and self.top < bbox.cy < self.bottom:
            return True
        return False

    def is_x_overlap(self, other: 'BBox') -> bool:
        """
        判断 x 方向是否与 other 相交
        """
        if self.left >= other.right:
            return False

        if self.right <= other.left:
            return False

        return True

    def is_y_overlap(self, other: 'BBox') -> bool:
        """
        判断 y 方向是否与 other 相交
        """
        if self.bottom >= other.top:
            return False

        if self.top <= other.bottom:
            return False

        return True

    def is_center_in(self, area) -> bool:
        """
        判断box 的中心是否在这个指定的区域内
        """
        xmin, ymin, xmax, ymax = area
        if self.cx < xmax and self.cx > xmin and self.cy < ymax and self.cy > ymin:
            return True
        else:
            return False

    def is_xaxis_in(self, other: 'BBox'):
        """判断self 是否在x 方向上完全在另一个bbox 内部"""
        if self.left > other.left and self.right < other.right:
            return True
        return False

    def is_same_line(self, other: 'BBox', thresh=0.15) -> bool:
        """
        判断 bbox 是否在同一行

        Args:
            other: BBox
            thresh: 以高度均值的比例作为判断的偏差
        """

        _thresh = self._cal_thresh(other, thresh)
        if abs(self.top - other.top) <= _thresh and abs(self.bottom - other.bottom) <= _thresh:
            return True

        return False

    def is_below(self, other: 'BBox', thresh=0.15) -> bool:
        """
        使用中心 y 坐标判断当前 box 是否位于 other 的下方

        Args:
            other:
            thresh: 以高度均值的比例作为判断的偏差

        """
        if (self.cy - other.cy) > self._cal_thresh(other, thresh):
            return True
        return False

    def is_above(self, other: 'BBox', thresh=0.15) -> bool:
        """
        使用中心 y 坐标判断当前 box 是否位于 other 的上方

        Args:
            other:
            thresh: 以高度均值的比例作为判断的偏差

        """
        if (other.cy - self.cy) > self._cal_thresh(other, thresh):
            return True
        return False

    def is_left(self, other: 'BBox', thresh=0.15) -> bool:
        """
        使用中心 x 坐标判断当前 box 是否位于 other 的左侧

        Args:
            other:
            thresh: 以高度均值的比例作为判断的偏差

        """
        if (other.cx - self.cx) > self._cal_thresh(other, thresh):
            return True
        return False

    def is_close_left(self, bbox: 'BBox', thresh=0.15) -> bool:
        # 判断输入bbox 是否是紧挨着当前bbox，并且在右侧
        # 即当前box 在输入bbox 的左侧
        if abs(bbox.left - self.right) < thresh * (bbox.width + self.width) and \
                bbox.cx - self.cx > self._cal_thresh(bbox, thresh):
            return True
        return False

    def is_close_up(self, bbox: 'BBox', thresh=0.5) -> bool:
        # 判断输入bbox 是否是紧挨着当前bbox，并且在下方
        # 即当前box 在输入bbox 的上方
        if abs(bbox.top - self.bottom) < thresh * (bbox.height + self.height) and \
                bbox.cy - self.cy > self._cal_thresh(bbox, thresh):
            return True
        return False

    def relation_to_other(self, bbox: 'BBox', thresh_x=2.5, thresh_y=4):
        """

        :param bbox: other bbox
        :return:
            tuple 是  left, right, up, down ， 每一个值是个bool，表示这个bbox是否在主体的上下左右
            返回 四个false时，表示这个框不在对应的搜索区域内
            thresh 用于确定搜索区域，在指定node_item的高宽*thresh内进行搜索
            因为一般y会比较短，所以y的设置的时候一般需要比x大一些

        """
        search_width = (self.rect[2] - self.rect[0]) * thresh_x
        search_height = (self.rect[3] - self.rect[1]) * thresh_y
        search_xmin = self.cx - search_width / 2
        search_xmax = self.cx + search_width / 2
        search_ymin = self.cy - search_height / 2
        search_ymax = self.cy + search_height / 2
        left = right = up = down = False

        if bbox.cx > search_xmin and bbox.cx < search_xmax and bbox.cy > search_ymin and bbox.cy < search_ymax:
            box_width = (self.rect[2] - self.rect[0])
            box_height = (self.rect[3] - self.rect[1])

            if bbox.cx < self.cx - box_width / 3:
                left = True
            if bbox.cx > self.cx + box_width / 3:
                right = True
            if bbox.cy > self.cy + box_height / 2:
                down = True
            if bbox.cy < self.cy - box_height / 2:
                up = True
        return {'left': left, 'right': right, 'up': up, 'down': down}

    def align_left(self, other: 'BBox', thresh=1.5) -> bool:
        """
        判断当前 bbox 是否与 other 左对齐

        Args:
            other:
            thresh: 以高度均值的比例作为判断的偏差
        """
        if abs(self.left - other.left) <= self._cal_thresh(other, thresh):
            return True
        return False

    def align_right(self, other: 'BBox', thresh=1.5):
        """
        以 right 为基准，判断当前 bbox 是否与 other 右对齐

        Args:
            other:
            thresh: 以高度均值的比例作为判断的偏差
        """
        if abs(self.right - other.right) <= self._cal_thresh(other, thresh):
            return True
        return False

    def center_dis(self, bbox: 'BBox'):
        """
        中心点的欧氏距离
        :param bbox:
        :return:
        """
        dx = self.cx - bbox.cx
        dy = self.cy - bbox.cy
        return math.sqrt(dx * dx + dy * dy)

    def left_center_dis(self, other: 'BBox'):
        """
        bbox 左边的中点的距离
        :param other:
        :return:
        """
        dx = self.left - other.left
        # left 边 y 轴中点
        dy = (self.top + self.bottom) / 2 - (other.top + other.bottom) / 2
        return math.sqrt(dx * dx + dy * dy)

    def center_man_dis(self, bbox: 'BBox'):
        """
        中心点的曼哈顿距离
        :param bbox:
        :return:
        """
        dx = self.cx - bbox.cx
        dy = self.cy - bbox.cy
        return abs(dx) + abs(dy)

    def left_top_dis(self, bbox: 'BBox'):
        """
        左上角点的欧氏距离
        :param bbox:
        :return:
        """
        dx = self.left - bbox.left
        dy = self.top - bbox.top
        return math.sqrt(dx * dx + dy * dy)

    def left_top_man_dis(self, bbox: 'BBox'):
        """
        左上角点的曼哈顿距离
        :param bbox:
        :return:
        """
        dx = self.left - bbox.left
        dy = self.top - bbox.top
        return abs(dx) + abs(dy)

    def cal_ioo(self, other: 'BBox'):
        """
        计算当前 bbox 的百分之多少处于 another 中
        """
        rect1 = self.rect
        rect2 = other.rect
        x_i = min(rect1[2], rect2[2]) - max(rect1[0], rect2[0])
        y_i = min(rect1[3], rect2[3]) - max(rect1[1], rect2[1])
        x_i = max(x_i, 0)
        y_i = max(y_i, 0)
        return (x_i * y_i) / (self.area + 1e-8)

    def cal_iou(self, other: 'BBox'):
        rect1 = self.rect
        rect2 = other.rect
        x_i = min(rect1[2], rect2[2]) - max(rect1[0], rect2[0])
        y_i = min(rect1[3], rect2[3]) - max(rect1[1], rect2[1])
        x_i = max(x_i, 0)
        y_i = max(y_i, 0)

        intersect = x_i * y_i
        return intersect / (self.area + other.area - intersect) \
            if (self.area + other.area - intersect) > 0 else 0

    def merge_(self, bbox: 'BBox'):
        """
        In place merge
        :param bbox:
        :return:
        """
        rect = self._get_merge_rect(bbox)
        self.update(rect)

    def merge(self, bbox: 'BBox') -> 'BBox':
        """
        :param bbox:
        :return:
        """
        rect = self._get_merge_rect(bbox)
        return BBox(rect)

    @staticmethod
    def merge_all(bbox: 'BBox', *other_bboxes: 'BBox'):
        """提供静态方法，merge一组bbox， 并返回一个新的bbox"""
        result = BBox([bbox.left, bbox.top, bbox.right, bbox.bottom])
        for other_bbox in other_bboxes:
            result.merge_(other_bbox)
        return result

    def transform(self, offset1, scale: float = 1, angle: float = 0, offset2=(0, 0)) -> 'BBox':
        """
        先将 bbox 按照 offset1 平移，经过 scale 和 angle 旋转以后再按照 offset2 平移
        :param offset1: (x, y)
        :param scale:
        :param angle:
        :param offset2: (x, y)
        :return:
        """
        trans_rect = []
        for i in range(4):
            trans_rect.append(self.rect[i] - offset1[i & 1])

        x1, y1, x2, y2 = trans_rect

        res_vector = BBox([x1 * scale, y1 * scale, x2 * scale, y2 * scale])

        if angle != 0:
            rect_size = [res_vector.width, res_vector.height]
            mid_vector = [res_vector.cx, res_vector.cy]
            rotated_mid_vector = geometry_cal.rotate_vector(mid_vector, angle)

            out_rect = []
            for i in range(4):
                out_rect.append(
                    rotated_mid_vector[i & 1] + ((i // 2) * 2 - 1) * (rect_size[i & 1] / 2.0) + offset2[i & 1]
                )
            res_vector.update(out_rect)

        return res_vector

    def _get_merge_rect(self, bbox: 'BBox'):
        left = min(self.left, bbox.left)
        top = min(self.top, bbox.top)
        right = max(self.right, bbox.right)
        bottom = max(self.bottom, bbox.bottom)
        return [left, top, right, bottom]

    def get_offset_box(self, col_offset=0, row_offset=0, width_ratio=1, height_ratio=1):
        """
        计算框上下左右的，平移一到两个位置的对应位置上框的坐标
        :param col_offset:  在列方向上的移动的单位，设置为整数，大于零表示向右移动col_offset个框
        :param row_offset: 在行方向上的移动的单位，设置为整数，大于零表示向下移动row_offset个框
        :return:
        """
        rect = self.rect
        height = int(self.height * height_ratio)
        width = int(self.width * width_ratio)
        # 计算上一个点的坐标
        new_box_rect = [0] * 4
        new_box_rect[0] = max(0, rect[0] + width * col_offset)
        new_box_rect[1] = max(0, rect[1] + height * row_offset)
        new_box_rect[2] = new_box_rect[0] + width
        new_box_rect[3] = new_box_rect[1] + height
        new_box_rect = [int(loc) for loc in new_box_rect]
        return BBox(new_box_rect)

    def unoffset_bbox(self, offset_x: int, offset_y: int) -> 'BBox':
        return self.offset_bbox(-1 * offset_x, -1 * offset_y)

    def offset_bbox(self, offset_x: int, offset_y: int) -> 'BBox':
        """
        获取一定偏移量后的bbox
        :param offset_x: 水平偏移量，向左偏移为负数
        :param offset_y: 垂直偏移量
        :return: 返回一个新的bbox
        """
        return BBox([
            self.left + offset_x,
            self.top + offset_y,
            self.right + offset_x,
            self.bottom + offset_y,
        ])

    def get_offset_box2(self, col_offset=0, row_offset=0, width_ratio=1, height_ratio=1):
        """
        - 把 box 的左上角点移动 col/row 个距离
        - 宽度和高度分别乘以 width_ratio/height_ratio
        """
        rect = self.rect
        height = int(self.height)
        width = int(self.width)
        # 计算上一个点的坐标
        new_box_rect = [0] * 4
        new_box_rect[0] = max(0, rect[0] + width * col_offset)
        new_box_rect[1] = max(0, rect[1] + height * row_offset)
        new_box_rect[2] = new_box_rect[0] + width * width_ratio
        new_box_rect[3] = new_box_rect[1] + height * height_ratio
        new_box_rect = [int(loc) for loc in new_box_rect]
        return BBox(new_box_rect)

    @property
    def left(self):
        return self.rect[0]

    @left.setter
    def left(self, x):
        self.rect[0] = x

    @property
    def top(self):
        return self.rect[1]

    @top.setter
    def top(self, x):
        self.rect[1] = x

    @property
    def right(self):
        return self.rect[2]

    @right.setter
    def right(self, x):
        self.rect[2] = x

    @property
    def bottom(self):
        return self.rect[3]

    @bottom.setter
    def bottom(self, x):
        self.rect[3] = x


    @property
    def center(self) -> Tuple:
        return self.cx, self.cy

    @property
    def cx(self):
        return (self.left + self.right) / 2

    @property
    def cy(self):
        return (self.top + self.bottom) / 2

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def area(self):
        return self.width * self.height

    @property
    def points(self) -> List[Tuple]:
        return [
            (self.rect[0], self.rect[1]),
            (self.rect[2], self.rect[1]),
            (self.rect[2], self.rect[3]),
            (self.rect[0], self.rect[3]),
        ]

    def update(self, rect: List[int]):
        self.rect = rect

    def _cal_thresh(self, bbox: 'BBox', thresh: float) -> float:
        return ((self.height + bbox.height) / 2) * thresh

    def _is_same(self, bbox: 'BBox'):
        for i in range(4):
            if self.rect[i] != bbox.rect[i]:
                return False
        return True

    def union(self, bbox: 'BBox'):
        """返回两个bbox 的交集"""
        from shapely.geometry import Polygon
        self_polygon = Polygon(
            [(self.left, self.top), (self.right, self.top),
             (self.right, self.bottom), (self.left, self.bottom)])
        other_polygon = Polygon(
            [(bbox.left, bbox.top), (bbox.right, bbox.top),
             (bbox.right, bbox.bottom), (bbox.left, bbox.bottom)])

        intersect = self_polygon.intersection(other_polygon)
        if intersect.area > 0:
            x, y = intersect.exterior.coords.xy
            xmin, xmax = min(x), max(x)
            ymin, ymax = min(y), max(y)
            return BBox([xmin, ymin, xmax, ymax])
        else:
            return None

    @staticmethod
    def get_bbox_bounding_rect(bboxes: List['BBox']) -> 'BBox':
        """计算一系列的bbox 的bounding rect 区域"""
        left_min = min([box.left for box in bboxes])
        right_max = max([box.right for box in bboxes])
        top_min = min([box.top for box in bboxes])
        bottom_max = max([box.bottom for box in bboxes])
        return BBox([left_min, top_min, right_max, bottom_max])

    def __eq__(self, other: 'BBox'):
        return self._is_same(other)

    def __ne__(self, other: 'BBox'):
        return not self._is_same(other)

    def __getitem__(self, index):
        return self.rect[index]

    def __len__(self):
        return len(self.rect)

    def __str__(self):
        return "[%.2f %.2f %.2f %.2f]" % (
            self.left, self.top, self.right, self.bottom)
