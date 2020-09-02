from typing import List, Dict, Tuple

import cv2
import numpy as np

from .shapes import Point, VectorizedPoint, Rectangle, Quadrilateral, Grid

color_list = [
    (0, 255, 0),
    (0, 0, 255),
    (255, 0, 0),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (255, 111, 0),
    (111, 0, 255),
    (255, 0, 111),
    (111, 255, 0),
    (0, 111, 255),
]

class PointSet:
    '''
    维护一个字典 key： x,y  value: point
    '''

    @staticmethod
    def get_high_privilege_point(p1, p2):
        def get_pri(p):
            if p.label == 4:
                return 2
            if p.label in [1, 3, 5, 7]:
                return 1
            return 0

        if get_pri(p2) > get_pri(p1):
            return p2
        else:
            return p1

    def __add_point(self, point: VectorizedPoint):
        assert isinstance(point, VectorizedPoint)
        if self.d.get((point.x, point.y)):
            self.d[(point.x, point.y)] = self.get_high_privilege_point(
                self.d[(point.x, point.y)], point)
        else:
            self.d[(point.x, point.y)] = point

    def __getitem__(self, point) -> VectorizedPoint:
        return self.d.get((point.x, point.y), None)

    def add(self, point: VectorizedPoint):
        self.__add_point(point)

    def __init__(self, points: List[VectorizedPoint] = None):
        self.d: Dict[Tuple, VectorizedPoint] = {}
        if points:
            for p in points:
                self.__add_point(p)

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, index: int):
        assert 0 <= index < 2, "index out of length"
        return self.x if index == 0 else self.y

    def __sub__(self, other: "Vector"):
        return Vector(self.x - other.x, self.y - other.y)

    def __add__(self, other: "Vector"):
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, other: float):
        return Vector(other * self.x, other * self.y)

    def cross_mul(self, v2: "Vector"):
        return self.cross_multiply(self, v2)

    @staticmethod
    def cross_multiply(v1: "Vector", v2: "Vector"):
        return v1.x * v2.y - v2.x * v1.y


def restore_points(points: List[Point], image: np.ndarray):
    # connect horiz. and vertic. lines
    # if intersected, restore a point with label 4 at intersection
    hlines = []
    vlines = []
    img_w, img_h, img_c = image.shape
    unit_length = min(img_w, img_h) * 0.007

    points.sort(key=lambda pp: (pp.x, pp.y))
    for i, p in enumerate(points):
        tp = None
        if p.label % 3 == 2:
            continue
        for u in points[i + 1 :]:
            if u is p:
                continue
            if u.label % 3 == 0:
                continue
            if abs(p.y - u.y) < unit_length:
                if tp is not None:
                    if abs(p.x - u.x) > abs(p.x - tp.x):
                        continue
                tp = u
        if tp is not None:
            hlines.append((p, tp))

    points.sort(key=lambda pp: (pp.y, pp.x))
    for i, p in enumerate(points):
        tp = None
        if p.label // 3 == 2:
            continue
        for u in points[i + 1 :]:
            if u is p:
                continue
            if u.label // 3 == 0:
                continue
            if abs(p.x - u.x) < unit_length:
                if tp is not None:
                    if abs(p.y - u.y) > abs(p.y - tp.y):
                        continue
                tp = u
        if tp is not None:
            vlines.append((p, tp))

    hlines.sort(key=lambda ll: ll[0].y)
    vlines.sort(key=lambda ll: ll[0].x)

    def intersection_point(l1, l2):
        a = Vector(l1[0].x, l1[0].y)
        a1 = Vector(l1[1].x, l1[1].y)
        b = Vector(l2[0].x, l2[0].y)
        b1 = Vector(l2[1].x, l2[1].y)
        v1 = a1 - a
        v2 = b1 - b
        if (
            v1.cross_mul(b - a) * v1.cross_mul(b1 - a) < 0
            and v2.cross_mul(a - b) * v2.cross_mul(a1 - b) < 0
        ):
            t = ((b - a).cross_mul(v2)) / (v1.cross_mul(v2))
            v = a + v1 * t
            # if 0.2 < t < 0.8 :
            return Point(label=4, x=v.x, y=v.y)
        return None

    for l1 in hlines:
        for l2 in vlines:
            if min(l2[0].x, l2[1].x) > l1[1].x:
                break
            p = intersection_point(l1, l2)
            if p:
                points.append(p)
    return points


def remove_wrong_point(points: List[Point], image: np.ndarray):
    h, w, c = image.shape
    thresh = max(8, int(max(w, h) * 0.006))
    R = max(int(max(w, h) * 0.001), 4)
    scope = max(8, int(max(w, h) * 0.003))
    comp = np.zeros([thresh])
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(image, 222, 255, cv2.THRESH_BINARY)[1]

    new_points = []

    def inspect(mat: np.ndarray) -> int:
        cnt = 0
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1] - thresh + 1):
                if (mat[i][j : j + thresh] == comp).all():
                    cnt += 1
                    break
        return cnt

    for p in points:
        if p.label == 1:
            temp = image[p.y - thresh : p.y + thresh + R, p.x - scope : p.x + scope]
            temp = temp.T
        elif p.label == 7:
            temp = image[p.y - thresh - R : p.y + thresh, p.x - scope : p.x + scope]
            temp = temp.T
        elif p.label == 3:
            temp = image[p.y - scope : p.y + scope, p.x - thresh : p.x + thresh + R]
        elif p.label == 5:
            temp = image[p.y - scope : p.y + scope, p.x - thresh - R : p.x + thresh]
        elif p.label == 4:
            temp = image[p.y - scope : p.y + scope, p.x - thresh - R : p.x + thresh]
            if inspect(temp) >= 1:
                temp = image[p.y - thresh - R : p.y + thresh, p.x - scope : p.x + scope]
                temp = temp.T
            else:
                continue
        else:
            new_points.append(p)
            continue
        if inspect(temp) >= 1:
            new_points.append(p)
    return new_points


def connect_points(points: List[Point], thr: int) -> List[VectorizedPoint]:
    points = [VectorizedPoint(p) for p in points]
    max_iter = 1
    unit_length = thr
    # 找右侧的点
    points.sort(key=lambda pp: (pp.x, -pp.y), reverse=True)
    for i, p in enumerate(points):
        edge_flag = False
        if p.label // 3 == 2 or p.label % 3 == 2:  # 没有 right
            if p.label // 3 == 2:
                edge_flag = True
            else:
                continue
        threshold = unit_length
        iter_x = 0
        while p.right is None and iter_x < max_iter:
            iter_x += 1
            candidates = []
            for j, _p in enumerate(points):
                if not edge_flag and (_p.label % 3 == 0 or _p.label // 3 == 2):  # 没有┐
                    continue
                if edge_flag and (_p.label % 3 == 0):
                    continue
                if i == j or _p.x - p.x < 5:  # horizontal
                    break
                if abs(p.y - _p.y) < threshold:
                    candidates.append(
                        ((0 if abs(p.y - _p.y) < 4 else abs(p.y - _p.y)), j)
                    )
            threshold += unit_length
            if len(candidates) == 0:
                continue
            candidates.sort(key=lambda xx: (-xx[1], xx[0]))
            for dis, j in candidates:
                _p = points[j]
                if _p.left is None or _p.left.x < p.x or _p.left.label == 7:
                    p.right = _p
                    _p.left = p
                    break

    # 找下方的点
    points.sort(key=lambda pp: (pp.y, -pp.x), reverse=True)
    for i, p in enumerate(points):
        edge_flag = False
        if p.label // 3 == 2 or p.label % 3 == 2:  # 没有┌
            if p.label % 3 == 2:
                edge_flag = True
            else:
                continue
        threshold = unit_length
        iter_x = 0
        while p.down is None and iter_x < max_iter:
            iter_x += 1
            candidates = []
            for j, _p in enumerate(points):
                if not edge_flag and (_p.label % 3 == 2 or _p.label // 3 == 0):  # 没有┗
                    continue
                if edge_flag and (_p.label // 3 == 0):
                    continue
                if i == j or _p.y - p.y < 3:  # vertical
                    break
                if abs(p.x - _p.x) < threshold:
                    candidates.append(
                        ((0 if abs(p.x - _p.x) < 4 else abs(p.x - _p.x)), j)
                    )
            threshold += unit_length
            if len(candidates) == 0:
                continue
            candidates.sort(key=lambda xx: (-xx[1], xx[0]))
            for dis, j in candidates:
                _p = points[j]
                if _p.up is None or _p.up.y < p.y or _p.up.label == 5:
                    p.down = _p
                    _p.up = p
                    break

    return points


def add_lost_points(points: List[VectorizedPoint], threshold):
    def check_if_should_add(new_p: VectorizedPoint):
        """
        为了避免重复添加点，这里需要检查在添加的点当中，是否有和new_p 位置特别接近的，如果有，直接使用已经创建的点
        """
        for p in point_st.d.values():
            if p.dis(new_p) < threshold:
                return None
        return new_p

    points.sort(key=lambda p: (p.x, p.y))
    point_st = PointSet(points)

    def comp_point(p, other):
        return (p.x, p.y) < (other.x, other.y)

    for p in points:
        if p.label // 3 == 2 or p.label % 3 == 2:  # 没有┌
            continue
        ori_p = None
        if p.down and p.right:
            # dn = points[lower_bound(points, 0, len(points), p.down, comp_point)]
            # ri = points[lower_bound(points, 0, len(points), p.right, comp_point)]
            dn = point_st[p.down]
            ri = point_st[p.right]
            if dn.right and ri.down and dn.right.dis(ri.down) > threshold:
                if dn.right.label // 3 == 0 or dn.right.label % 3 == 0:
                    continue
                if ri.down.label // 3 == 0 or ri.down.label % 3 == 0:
                    continue
                if ri.down.y < dn.y - threshold and ri.down.label % 3 != 0:
                    ori_p = p.down
                    p.down = None
                elif dn.right.x < ri.x - threshold and dn.right.label // 3 != 0:
                    ori_p = p.right
                    p.right = None
        if not ori_p:
            continue
        if not ((p.right is None) ^ (p.down is None)):
            # p.right and p.down both are None or not None
            continue
        if p.right is None:
            """
            #####    ####  up   ######    
            ##  p    ####  new  ## ori
            ##  _p   ####  ri   ###
            """
            # _p = points[lower_bound(points, 0, len(points), p.down, comp_point)]
            _p = point_st[p.down]
            if _p.right:
                # ri = points[lower_bound(points, 0, len(points), _p.right, comp_point)]
                ri = point_st[_p.right]

                if (
                    abs(ri.x - _p.right.x) > threshold
                    or abs(ri.y - _p.right.y) > threshold
                ):
                    continue

                new_p = VectorizedPoint(
                    Point(1 if p.label // 3 == 0 else 4, _p.right.x, p.y)
                )

                new_p = check_if_should_add(new_p)
                if new_p is None:
                    continue

                # new_p.down = points[lower_bound(points, 0, len(points), _p.right, comp_point)]
                new_p.down = point_st[_p.right]
                # notice up point
                if ri.up:
                    # _up_point = points[lower_bound(points, 0, len(points), ri.up, comp_point)]
                    _up_point = point_st[ri.up]
                    if new_p.y - _up_point.y > 3 * threshold:
                        _up_point.down = new_p
                ri.up = new_p

                new_p.left = p
                # new_p.right = points[lower_bound(points, 0, len(points), ori_p,comp_point)] if ori_p else None
                new_p.right = point_st[ori_p]
                p.right = new_p
                point_st.add(new_p)
                # points.append(new_p)
        elif p.down is None:
            """
            #       ##  p    ####_p
            left    ##  new  ####dn
            #       ##  ori  ######
            """
            # _p = points[lower_bound(points, 0, len(points), p.right, comp_point)]
            _p = point_st[p.right]
            if _p.down:
                # dn = points[lower_bound(points, 0, len(points), _p.down, comp_point)]
                dn = point_st[_p.down]

                if (
                    abs(dn.x - _p.down.x) > threshold
                    or abs(dn.y - _p.down.y) > threshold
                ):
                    continue

                new_p = VectorizedPoint(
                    Point(3 if p.label % 3 == 0 else 4, p.x, _p.down.y)
                )

                new_p = check_if_should_add(new_p)
                if new_p is None:
                    continue

                # new_p.right = points[lower_bound(points, 0, len(points), _p.down, comp_point)]
                new_p.right = point_st[_p.down]
                # notice left
                if dn.left:
                    # _left_point = points[lower_bound(points, 0, len(points), dn.left,comp_point)]
                    _left_point = point_st[dn.left]
                    if new_p.x - _left_point.x > 3 * threshold:
                        _left_point.right = new_p
                dn.left = new_p

                new_p.up = p
                # new_p.down = points[lower_bound(points, 0, len(points), ori_p,comp_point)] if ori_p else None
                new_p.down = point_st[ori_p]
                p.down = new_p
                # add_points.append(new_p)
                # points.append(new_p)
                point_st.add(new_p)

    # # 可能重复恢复， 去重
    # for i, p in enumerate(add_points):
    #     if p.label == -1:
    #         continue
    #     for _p in add_points[i + 1:]:
    #         if _p.label != -1 and p.dis(_p) < threshold * 0.5:
    #             _p.point.label = -1

    # 遍历所有恢复的点
    # points += [p for p in add_points if p.label >= 0]
    points = list(point_st.d.values())
    return points


def generate_quadrilaterals(
    points: List[VectorizedPoint], unit_length=15
) -> List[Quadrilateral]:
    quadrilaterals = []
    for i, p in enumerate(points):
        if p.label // 3 == 2 or p.label % 3 == 2:  # 没有┌
            continue
        if p.down is None or p.right is None:
            continue
        # 确定平行四边形，左上三点，找右下角点
        virtual_point = Point(
            x=p.right.x + abs(p.x - p.down.x), y=p.down.y + abs(p.y - p.right.y)
        )
        candidate_point = virtual_point
        for j, _p in enumerate(points):
            if _p.label % 3 == 0 or _p.label // 3 == 0:
                continue
            if j == i:
                continue
            if virtual_point.dis(_p) > unit_length:
                continue
            if candidate_point.label != -1 and virtual_point.dis(
                _p
            ) > virtual_point.dis(candidate_point):
                continue
            candidate_point = _p.point
        quadrilaterals.append(
            Quadrilateral(p.point, p.point, p.right, p.down, candidate_point)
        )
    return quadrilaterals


def generate_rectangles(points: List[VectorizedPoint]) -> List[Rectangle]:
    """
    :param points:
    :return: 这里rectangle为四个点的水平外接矩形
    """
    rects = []
    point_map = dict((p.point, p) for p in points)

    for p in points:
        if p.label % 3 == 2 or p.label // 3 == 2:
            continue
        if p.down is None or p.right is None:
            continue
        left, top, right, bottom = (
            min(int(p.x), int(p.down.x)),
            min(int(p.y), int(p.right.y)),
            int(p.right.x),
            int(p.down.y),
        )

        _p1, _p2 = point_map[p.down].right, point_map[p.right].down
        if _p1 is not None and (_p1.label % 3 == 0 or _p1.label // 3) == 0:
            _p1 = None
        if _p2 is not None and (_p2.label % 3 == 0 or _p2.label // 3) == 0:
            _p2 = None
        if _p1 is not None:
            right, bottom = max(right, int(_p1.x)), max(bottom, int(_p1.y))
        if _p2 is not None:
            if _p1 is None or p.dis(_p2) < p.dis(_p1):
                right, bottom = max(right, int(_p2.x)), max(bottom, int(_p2.y))
        r = Rectangle(p.point, Point(x=left, y=top), Point(x=right, y=bottom))
        rects.append(r)

    return rects


def paint(
    points: List[Point],
    img_h,
    img_w,
    return_pic=True,
    return_shape="rect",
    ori_image=None,
):
    img = (np.zeros([img_h, img_w, 3], dtype=np.uint8) - 1) if return_pic else None
    if ori_image is not None:
        img = ori_image
    if return_pic:
        for p in points:
            cv2.circle(img, (p.x, p.y), 4, color_list[p.label], 4)
    points = connect_points(points, img_h, img_w)
    if return_shape == "rect":
        rects = generate_rectangles(points)
        if return_pic:
            for i, r in enumerate(rects):
                color = color_list[i % 11]
                img = cv2.rectangle(
                    img, tuple(r.points[0].values), tuple(r.points[1].values), color, 2
                )
            return img, rects
        return rects
    quads = generate_quadrilaterals(points)
    return quads


def get_grids(shapes: List[Quadrilateral], threshold) -> List[Grid]:
    # shapes 是四边形 Grid 是shape加col row
    # 构造一个dict shape->Grid, 目的是可通过shape找到对应的Grid
    if len(shapes) == 0:
        return []
    grids = dict([(quad, Grid(shape=quad)) for quad in shapes])

    def count_row():
        shapes.sort(key=lambda r: (r.keypoint.y, r.keypoint.x))
        _rows: List[List[Quadrilateral]] = []
        grids[shapes[0]].row = 0
        _rows.append([shapes[0]])
        for shape in shapes[1:]:
            for i in range(len(_rows) - 1, -1, -1):
                _dis = [
                    (c.keypoint.dis(shape.keypoint), c.keypoint.y) for c in _rows[i]
                ]
                dis, y = min(_dis)
                if abs(min(_dis)[1] - shape.keypoint.y) < threshold:
                    grids[shape].row = i
                    _rows[i].append(shape)
                    break
            else:
                grids[shape].row = len(_rows)
                _rows.append([shape])
        # --- deprecated ---
        # _threshold = -1
        # n_row = -1
        # for i, r in enumerate(shapes):
        #     if r.keypoint.y > _threshold:
        #         n_row += 1
        #
        #     _threshold = r.keypoint.y + threshold
        #     grids[r].row = n_row

    def count_col():
        shapes.sort(key=lambda r: (r.keypoint.x, r.keypoint.y))
        _cols: List[List[Quadrilateral]] = []
        grids[shapes[0]].col = 0
        _cols.append([shapes[0]])
        for shape in shapes[1:]:
            for i in range(len(_cols) - 1, -1, -1):
                _dis = [
                    (c.keypoint.dis(shape.keypoint), c.keypoint.x) for c in _cols[i]
                ]

                if abs(min(_dis)[1] - shape.keypoint.x) < threshold:
                    grids[shape].col = i
                    _cols[i].append(shape)
                    break
            else:
                grids[shape].col = len(_cols)
                _cols.append([shape])

        # --- deprecated ---
        # _threshold = -1
        # n_col = -1
        #
        # for i, r in enumerate(shapes):
        #     if r.keypoint.x > _threshold:
        #         n_col += 1
        #
        #     _threshold = r.keypoint.x + threshold
        #     grids[r].col = n_col

    count_row()
    count_col()
    return list(grids.values())


def get_lines(img):
    h, w, c = img.shape
    threshold = int(w * 0.006) * 2 + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (threshold // 2 + 1, threshold // 2 + 1)
    )
    _img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    _img = cv2.cvtColor(_img, cv2.COLOR_BGR2GRAY)
    _img = cv2.adaptiveThreshold(
        _img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        threshold,
        threshold // 2,
    )
    lines = cv2.HoughLinesP(
        _img, rho=1, theta=np.pi / 180, threshold=500, minLineLength=1000, maxLineGap=10
    )

    return lines


def test_main():
    def load_from_txt(filename):
        points = []
        imgh, imgw = 0, 0
        with open(filename) as f:
            for line in f.readlines():
                x = line.split()
                points.append(Point(label=int(x[0]), x=float(x[1]), y=float(x[2])))
        imgw = max(points, key=lambda p: p.x).x
        imgh = max(points, key=lambda p: p.y).y
        return points, imgh, imgw

    points, imgh, imgw = load_from_txt(
        "../../../processor/cai_bao_table/src/postprocess/temp/test.txt"
    )
    img = cv2.imread("../../../processor/cai_bao_table/src/postprocess/temp/test.jpg")
    imgh, imgw, imgc = img.shape
    points = remove_wrong_point(points, img)
    paint(points, imgh, imgw, ori_image=img)


def remove_duplicated_point(points: List[Point], threshold):
    points.sort(key=lambda p: (p.x, p.y))

    def get_high_privilege_point(p1: Point, p2: Point):
        def get_pri(p: Point):
            if p.label == 4:
                return 2
            if p.label in [1, 3, 5, 7]:
                return 1
            return 0

        if get_pri(p2) > get_pri(p1):
            return p2
        else:
            return p1

    for i, p in enumerate(points):
        if p.label == -1:
            continue
        for _p in points[i + 1 :]:
            if _p.label == -1:
                continue
            if abs(_p.x - p.x) >= threshold:
                break
            if p.dis(_p) < threshold:
                high_point = get_high_privilege_point(p, _p)
                if id(p) == id(high_point):
                    _p.label = -1
                else:
                    p.label = -1
    return [p for p in points if p.label in range(9)]


if __name__ == "__main__":
    test_main()
