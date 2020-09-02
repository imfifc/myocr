import numpy as np

class BBox:
    def __init__(self, arr):
        """
        :param arr: List
        """
        self.left = float(arr[0])
        self.top = float(arr[1])
        self.right = float(arr[2])
        self.bot = float(arr[3])

    def __str__(self):
        return '[{}-{}-{}-{}]'.format(self.left, self.top, self.right, self.bot)

    __repr__ = __str__

    def react(self):
        # 返回numpy数组是为了方便快速计算
        return np.array([self.left, self.top, self.right, self.bot])

    def center_x(self):
        return round((self.left + self.right) / 2)

    def center_y(self):
        return round((self.top + self.bot) / 2)

    def delta_y(self):
        return self.bot - self.top

    def delta_x(self):
        return self.right - self.left

    def area(self):
        return self.delta_x() * self.delta_y()
