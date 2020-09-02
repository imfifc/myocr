# reference : https://github.com/Sanster/tf_ctpn/blob/master/tools/mlt17_to_voc.py
# 这里存放的函数用于存放一些和直线计算相关的内容
# 比如判断一个点是否在一条直线的上方或者下方 is_under_line
# 比如计算一条直线在某个点上的垂线（法线）


class Point:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def __str__(self):
        return "({}, {})".format(self.x, self.y)


class Line:
    def __init__(self, p0: Point, p1: Point):
        self.p0 = p0
        self.p1 = p1

        if p0.x - p1.x == 0:
            self.k = None
        else:
            self.k = (self.p0.y - self.p1.y) / (self.p0.x - self.p1.x)

        # f = ax+by+c = 0
        self.a = self.p0.y - self.p1.y
        self.b = self.p1.x - self.p0.x
        self.c = self.p0.x * self.p1.y - self.p1.x * self.p0.y

    def cross(self, line) -> Point:
        d = self.a * line.b - line.a * self.b
        if d == 0:
            return None

        x = (self.b * line.c - line.b * self.c) / d
        y = (line.a * self.c - self.a * line.c) / d

        return Point(x, y)

    def contain(self, p: Point) -> bool:
        if p is None:
            return False

        # 输入的点应该吃 cross(求出来的交点)
        # p 点是否落在 p0 和 p1 之间, 而不是延长线上
        if p.x > max(self.p1.x, self.p0.x):
            return False

        if p.x < min(self.p1.x, self.p0.x):
            return False

        if p.y > max(self.p1.y, self.p0.y):
            return False

        if p.y < min(self.p1.y, self.p0.y):
            return False

        return True

    def get_yaxis(self, x):
        # 输入一个x ，返回对应的y
        if self.b == 0:
            # 说明是一条垂线
            return None
        return (-self.c - self.a * x) / self.b

    def is_under(self, p: Point):
        # 判断 p 是否是在 直线的下方还是上方
        if self.b == 0:
            return None

        y_on_line = self.get_yaxis(p.x)
        if y_on_line > p.y:
            # 注意，图像的原点在左上角，所以 此时应该是 p 在线的上方
            return False
        else:
            return True

    @staticmethod
    def gen_parallel_line(line, p: Point):
        # 返回一条新的直线，直线穿过点p ， 斜率和传入的line 平行
        # 首先获取原先的直线的斜率
        k = line.k
        if k is None:
            # 制作一条垂直的线
            return Line(p, Point(x=p.x, y=10))
        else:
            b = p.y - k * p.x
            # 点斜式
            basex = 0
            basey = k * basex + b
            return Line(p, Point(basex, basey))

    def get_normal_line(self, p: Point):
        # 给出在某个点处的法线方程
        assert self.contain(p)
        normal_k = - 1 / self.k
        b = p.y - normal_k * p.x
        basex = 0
        basey = normal_k * basex + b
        return Line(p, Point(basex, basey))


def generate_line(x1, y1, x2, y2):
    return Line(Point(x1, y1), Point(x2, y2))


def is_under_line(x1, y1, x2, y2, x, y):
    """
    判断 点 (x,y) 是否在 （x1,y1 , x2 , y2） 构成的直线下方
    :param line_x:
    :param line_y:
    :param x:
    :param y:
    :return:
    """
    p1 = Point(x1, y1)
    p2 = Point(x2, y2)
    line = Line(p1, p2)
    return line.is_under(Point(x, y))


def gen_parallel_line(x1, y1, x2, y2, x, y):
    return Line.gen_parallel_line(Line(Point(x1, y1), Point(x2, y2)), Point(x, y))
