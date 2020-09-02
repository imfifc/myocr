import json
from typing import Tuple, List
import numpy as np

from .painter import paint, remove_wrong_point, \
    connect_points, generate_quadrilaterals, get_grids, restore_points, remove_duplicated_point, add_lost_points
from .shapes import Point


def load_gt(filename: str):
    points = []
    with open(filename) as f:
        for line in f.readlines():
            num = line.strip().split()
            points.append(Point(int(num[0]), float(num[1]), float(num[2])))
    return points


class KeypointPostProcess:
    def __init__(self, points=None, img=None):
        '''
        Args:
            img: opencv image (BGR)
        '''
        assert img is not None
        self.img = img  # const
        self.img_h, self.img_w, self.img_c = img.shape
        self._points = remove_duplicated_point(points, self.img_h * 0.005)

    @property
    def points(self) -> List[Point]:
        return self._points

    def raw_result(self):
        s = ""
        for p in self.points:
            cat = p.label
            x = p.x
            y = p.y
            s += f"{cat} {x} {y}\n"
        return s

    def json_str(self):
        d = {}
        d['shapes'] = []
        pad = min(self.img_w, self.img_h) * 0.005
        for p in self.points:
            shape = {}
            shape['label'] = str(p.label)
            x = p.x
            y = p.y
            shape['points'] = []
            shape['points'].append([max(0, x - pad), max(0, y - pad)])
            shape['points'].append(
                [min(self.img_w - 2, x + pad), min(self.img_h - 2, y + pad)])
            d['shapes'].append(shape)
        return json.dumps(d)

    def table(self, return_pic=True, return_shape='rect'):
        if return_pic:
            image, rects = paint(self.points, self.img_h, self.img_w)
            image = image + 1
            image[image == 0] = self.img[image == 0]
            return image, rects
        shapes = paint(self.points, self.img_h, self.img_w, return_pic=False,
                       return_shape=return_shape)
        return shapes

    def get_acc(self, gt_path: str) -> Tuple:
        '''
        Args:
            gt_path: ground truth
            e.g.
            label x y
        Returns: tuple (precision, recall, f1)
        '''
        pre_points = self.points
        if len(pre_points) == 0:
            return (0.0, 0.0, 0.0)
        gt_points = load_gt(gt_path)
        thresh_dis = .01 * max(self.img_h, self.img_w)

        dis_arr = []
        for gt in gt_points:
            dis_arr.append(list(
                [gt.distance(p) if p.label == gt.label else 99999 for p in
                 pre_points]))

        dis_arr = np.array(dis_arr)

        cnt = 0
        for _t in range(len(gt_points)):
            if dis_arr.min() > thresh_dis:
                break
            _m = dis_arr.argmin()
            gt = int(_m / len(pre_points))
            p = int(_m % len(pre_points))
            cnt += 1
            dis_arr[gt, :] = 99999
            dis_arr[:, p] = 99999

        prec = cnt / len(pre_points) if len(pre_points) > 0 else 0.0
        recall = cnt / len(gt_points)
        f1_score = 2 * prec * recall / (prec + recall) if cnt > 0 else 0.0
        return prec, recall, f1_score

    def get_grids(self, threshold=10):
        # points = remove_wrong_point(self.points, self.img)
        # points = restore_points(points, self.img)
        points = connect_points(self.points, threshold)
        n_points = 0
        cnt = 0
        while len(points) > n_points and cnt <5:
            n_points = len(points)
            points = add_lost_points(points, threshold)
            cnt += 1
        points = remove_duplicated_point(points, threshold*0.75)
        quads = generate_quadrilaterals(points, threshold)
        grids = get_grids(quads, threshold)
        return grids, points


"""
debug 
for p in points : 
    if p.x == 1378 and p.y == 621:
        break
"""
