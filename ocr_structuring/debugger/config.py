import functools
import logging
from typing import Dict

import numpy as np

from ocr_structuring.core.utils.node_item import NodeItem

logger = logging.getLogger("debugger")


def check_enabled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from . import enabled

        if enabled:
            func(*args, **kwargs)

    return wrapper


class CommonVars:
    def __init__(self):
        # 模板图片的base64
        self.tplImage = None


class Vars:
    """
        用于保存结构化过程中需要上传到结构化工具的数据。
        可以通过 Vars 的单例来调用接口 `from ocr_structuring.debugger import variables`
    """

    def __init__(self):
        # 原始识别图片，由服务端提供
        self.rawImage = None
        # 原始识别框，由服务端提供
        self.rawBBoxes = []
        # 预测结果
        self.pred = {}
        # 预测结果置信度
        self.predProbability = {}
        # 结构化时间
        self.structuringDuration = 0

        self.resultsTemplate = self._get_base_template()

    def clean(self):
        """ 因为我们是用单例存储数据，所以处理不同的图片前需要 clean 一下 """
        self.pred.clear()
        self.predProbability.clear()
        self.structuringDuration = 0
        self.resultsTemplate = self._get_base_template()

    @check_enabled
    def set_H(self, H: np.ndarray):
        """
        对测试图片进行投影变换

        Args:
            H: cv2.findHomography 函数返回的单应性矩阵(3x3)

        Returns:

        """
        H_name = "perspectiveMatrix"
        name = "perspective"

        tpl = {
            "name": name,
            "text": "投影变换",
            "image": {
                "data": "#{rawImage}",
                "func": "transform",
                "args": "#{%s}" % H_name,
            },
        }
        self.__setattr__(H_name, H.tolist())

        self.delete_group(name)
        self.resultsTemplate.append(tpl)

    def add_group(self, name, text, raw_data, desc=""):
        """
        在测试图片上显示文本框

        Args:
            name: key
            text: 中文名
            raw_data:
                .. code-block:: python

                    [
                        ["text", 0, 0, 100, 100],
                        ["text2", 60, 89, 100, 100],
                    ]

            desc: 描述

        """
        self._add_group(name, text, raw_data, desc, "rawImage")

    def add_group2tpl(self, name, text, raw_data, desc=""):
        """
        在模板图片上显示文本框

        Args:
            name: key
            text: 中文名
            raw_data:
                .. code-block:: python

                    [
                        ["text", 0, 0, 100, 100],
                        ["text2", 60, 89, 100, 100],
                    ]
            desc: 描述

        """
        self._add_group(name, text, raw_data, desc, "tplImage")

    def add_nodes(self, name, text, node_items: [NodeItem], desc=""):
        """
        在测试图片上显示文本框

        Args:
            name: key
            text: 中文名
            node_items: List[NodeItem]
            desc: 描述

        """
        self._add_nodes_group(name, text, node_items, desc, "rawImage")

    def add_nodes_on_tpl(self, name, text, node_items: [NodeItem], desc=""):
        """
        在模板图片上显示文本框

        Args:
            name: 英文名
            text: 中文名
            node_items: List[NodeItem]
            desc: 描述

        """
        self._add_nodes_group(name, text, node_items, desc, "tplImage")

    @check_enabled
    def _add_group(self, name, text, raw_data, desc, img_name):
        assert img_name in ["tplImage", "rawImage"]

        self.__setattr__(name, self.raw_2_bboxes(raw_data))
        group_tpl = {
            "name": name,
            "text": text,
            "desc": desc,
            "image": {"data": "#{%s}" % img_name},
            "bboxes": {"data": "#{%s}" % name},
        }

        self.delete_group(name)
        self.resultsTemplate.append(group_tpl)

    def _node_item_to_bbox(self, node_item: NodeItem):
        content, x1, y1, x2, y2, x3, y3, x4, y4 = node_item.raw_node[:9]
        probability = node_item.raw_node[11:]
        return {
            "points": [
                {"x": x1, "y": y1},
                {"x": x2, "y": y2},
                {"x": x3, "y": y3},
                {"x": x4, "y": y4},
            ],
            "content": content,
            "probability": probability,
        }

    @check_enabled
    def _add_nodes_group(self, name, text, node_items: [NodeItem], desc, img_name):
        box_data = [self._node_item_to_bbox(node_item) for node_item in node_items]
        setattr(self, name, box_data)
        group_tpl = {
            "name": name,
            "text": text,
            "desc": desc,
            "image": {"data": "#{%s}" % img_name},
            "bboxes": {"data": "#{%s}" % name},
        }
        self.delete_group(name)
        self.resultsTemplate.append(group_tpl)

    def delete_group(self, name):
        """
        删除一个 group
        Args:
            name: key

        """
        for i, it in enumerate(self.resultsTemplate):
            if it["name"] == name:
                self.resultsTemplate.pop(i)
                break

    def raw_2_bboxes(self, raw_data) -> Dict:
        """
        把 raw_data 转换成结构化工具需要的格式

        Args:
        raw_data: List[ [text,x1,y1,x2,y2] ]

        Returns:
            .. code-block:: python

                 {
                     'points': {'x':2, 'y':1},
                     'content': '123',
                     'probability': [0.9, 0.8, 0.7]
                 }
        """
        bboxes = []
        for it in raw_data:
            it_len = len(it)
            if it_len != 5 and it_len != 9 and it_len > 0:
                str_len = len(it[0]) if len(it[0]) > 0 else 1
                it_len = it_len - str_len - 2  # raw_data的长度-字符串的长度-两位其他信息
            if it_len == 5:
                points = [
                    {"x": it[1], "y": it[2]},
                    {"x": it[3], "y": it[2]},
                    {"x": it[3], "y": it[4]},
                    {"x": it[1], "y": it[4]},
                ]
                probabilities = it[7:]
            elif it_len == 9:
                points = [
                    {"x": it[1], "y": it[2]},
                    {"x": it[3], "y": it[4]},
                    {"x": it[5], "y": it[6]},
                    {"x": it[7], "y": it[8]},
                ]
                probabilities = it[11:]
            else:
                raise Exception("raw_data format error")

            bboxes.append({"points": points, "content": it[0], "probabilities": probabilities})
        return bboxes

    def _get_base_template(self):
        return [
            {
                "name": "rawData",
                "text": "原始识别结果",
                "desc": "Pipeline 输出的原始结果",
                "image": {"data": "#{rawImage}"},
                "bboxes": {"data": "#{rawBBoxes}"},
            },
        ]


variables = Vars()
