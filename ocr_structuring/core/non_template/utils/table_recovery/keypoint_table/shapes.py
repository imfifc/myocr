# Author 金明熠
import math
from typing import List


class Point():
    def __init__(self, label: int = -1, x=0, y=0):
        self.values = [int(x), int(y)]
        self.label = label

    @property
    def x(self) -> int:
        return self.values[0]

    @x.setter
    def x(self, v):
        self.values[0] = v

    @property
    def y(self) -> int:
        return self.values[1]

    @y.setter
    def y(self, v):
        self.values[1] = v

    def distance(self, p2):
        return math.sqrt((self.x - p2.x) ** 2 + (self.y - p2.y) ** 2)

    def dis(self, p2):
        return self.distance(p2)

    def __str__(self):
        return f'label:{self.label} x:{self.x} y:{self.y}'


class VectorizedPoint:

    def __init__(self, point: Point):
        self.point: Point = point
        self.points: List[Point] = [None, None,
                                    None, None]  # up, left, down, right

    @property
    def up(self) -> Point:
        return self.points[0]

    @up.setter
    def up(self, vp: 'VectorizedPoint'):
        self.points[0] = vp.point if vp else None

    @property
    def down(self) -> Point:
        return self.points[2]

    @down.setter
    def down(self, vp: 'VectorizedPoint'):
        self.points[2] = vp.point if vp else None

    @property
    def right(self) -> Point:
        return self.points[3]

    @right.setter
    def right(self, vp: 'VectorizedPoint'):
        self.points[3] = vp.point if vp else None

    @property
    def left(self) -> Point:
        return self.points[1]

    @left.setter
    def left(self, vp: 'VectorizedPoint'):
        self.points[1] = vp.point if vp else None

    @property
    def label(self) -> int:
        return self.point.label

    @label.setter
    def label(self,x):
        self.point.label=x

    @property
    def x(self):
        return self.point.x

    @property
    def y(self):
        return self.point.y

    def dis(self, p2):
        return self.point.dis(p2)

    def __str__(self):
        return f'{str(self.point)}\n' + \
               f'up:{str(self.up)}\n' + \
               f'left:{str(self.left)}\n' + \
               f'down:{str(self.down)}\n' + \
               f'right:{str(self.right)}'


class Shape:
    def __init__(self, keypoint: Point):
        self.__point = keypoint

    @property
    def keypoint(self):
        return self.__point


class Quadrilateral(Shape):
    def __init__(self, keypoint: Point,
                 left_top: Point = None,
                 right_top: Point = None,
                 left_bottom: Point = None,
                 right_bottom: Point = None,
                 points=None):
        super().__init__(keypoint)
        self.points = [left_top, right_top, left_bottom, right_bottom]
        if points is not None and len(points) >= 4:
            self.points = points[:4]

    def __str__(self):
        return str([str(p) for p in self.points])

    @property
    def left_top(self) -> Point:
        return self.points[0]

    @property
    def right_top(self) -> Point:
        return self.points[1]

    @property
    def left_bottom(self) -> Point:
        return self.points[2]

    @property
    def right_bottom(self) -> Point:
        return self.points[3]


class Rectangle(Shape):
    def __init__(self, keypoint,
                 left_top: Point = None,
                 right_bottom: Point = None,
                 points: List[Point] = None,
                 quadrilateral: Quadrilateral = None):
        super().__init__(keypoint)
        self.points = [left_top, right_bottom]
        if quadrilateral is not None:
            self.points = quadrilateral.points[::2]
        if points is not None:
            self.points = points

    @property
    def top(self):
        return self.points[0].y

    @property
    def left(self):
        return self.points[0].x

    @property
    def bottom(self):
        return self.points[1].y

    @property
    def right(self):
        return self.points[1].x

    def __str__(self):
        return super().__str__()


class Grid:

    def __init__(self, row=-1, col=-1, shape: Quadrilateral = None):
        self.row: int = row  # the first row is 0
        self.col: int = col
        self.shape: Quadrilateral = shape

    def __str__(self):
        return "row:{} col:{} shape:{}".format(self.row, self.col,
                                               str(self.shape))


if __name__ == "__main__":
    pass
