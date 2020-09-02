import copy
import time
from functools import wraps

from typing import List
from ocr_structuring import debugger

from ocr_structuring.core.models.structure_item import StructureItem

# 定义不同类型 rect 的颜色，RGB 顺序，用于前端画图
DEBUG_TEMPLATE_FILTER_OUTPUT_COLOR = (0, 255, 0)
DEBUG_TEMPLATE_FILTER_INPUT_COLOR = (0, 0, 0)
DEBUG_RAW_DATA_COLOR = (15, 138, 245)
DEBUG_RECT_GROUP_DEFAULT_COLOR = (15, 138, 245)
DEBUG_BG_SCALE_RESULT_COLOR = (255, 0, 0)


class RectGroupData:
    def __init__(self, group_name, raw_data, color, item_name=None):
        """
        :param group_name:
        :param raw_data: [[text,x1,y1,x2,y2],...]
        :param item_name: 结构化字段的名字，如果为空，则在 debug 工具中对所有 item_name 都有效
        """
        self.item_name = item_name
        self.name = group_name
        self.raw_data = copy.deepcopy(raw_data)
        self.color = color


class DebugData:
    def __init__(self):
        self.fid = ""
        self.is_ltrb = True
        self.roi = None
        self.gt_img_name = ""
        self.is_template = False

        # 自定义展示某些矩形框
        self.rect_groups: List[RectGroupData] = []

        # key value 形式的结构化结果
        self.key_value_result = {}

        # 使用投影变换进行背景缩放获得的变换矩阵
        self.H = None
        self.bg_scale_rect_group: RectGroupData = None
        self.above_offset_rect_group: RectGroupData = None

        self.process_time = {}  # ms

    def set_process_time(self, name, time_ms):
        self.process_time[name] = time_ms

    def set_H(self, H):
        """
        把投影变换的举证转成可以 json dump 的格式
        :param H:
        :return:
        """
        if H is None:
            return
        self.H = {
            "shape": H.shape,
            "data": H.flatten().tolist(),
        }

    def set_raw_data(self, raw_data, is_ltrb=True):
        """
        移除 CRNN 的置信度
        :param raw_data:
        :return:
        """
        if is_ltrb:
            raw = [it[:5] for it in raw_data]
        else:
            raw = [it[:9] for it in raw_data]
        self.add_rect_group(None, "raw", raw)

    def set_bg_scale_result(self, raw_data):
        self.bg_scale_rect_group = RectGroupData(
            "bg scale", raw_data, DEBUG_BG_SCALE_RESULT_COLOR
        )

    def set_above_offset_result(self, raw_data):
        self.above_offset_rect_group = RectGroupData(
            "above offset", raw_data, DEBUG_BG_SCALE_RESULT_COLOR
        )

    def add_rect_group(
        self, item_name, group_name, raw_data, color=DEBUG_RECT_GROUP_DEFAULT_COLOR
    ):
        """
        :param item_name: 结构化字段的名字，如果为空，则在 debug 工具中所有字段都为显示
        :param group_name: 该组文本框的名字
        :param raw_data: [[text,x1,y1,x2,y2], ... ]
        :param color: RGB 例如 红色为 [255,0,0]
        :return:
        """
        self.rect_groups.append(RectGroupData(group_name, raw_data, color, item_name))

    def set_structure_result(self, structure_result):
        if isinstance(structure_result, dict):
            # key-value 形式的结构化结果
            for k, v in structure_result.items():
                try:
                    content = v["content"]
                except:
                    print("!" * 20, k, v, structure_result)
                    continue
                if content is None:
                    continue
                self.key_value_result[k] = content

    # def to_backend_data(self):
    #     """
    #     将ExpData转化为python的简单结构，送给Backend保存
    #     :return:
    #     """
    #     output = {
    #         'fid': self.fid,
    #         'input': self.raw_data,
    #         'key_value_result': self.key_value_result,
    #     }
    #     data = self.__dict__
    #     # 删除已经转化的字段
    #     del data['label_node_list']
    #     del data['fid']
    #     del data['raw_data']
    #     del data['pred_structure_data']
    #     # # 将复杂结构的字段进行处理
    #     # if data['H'] is not None:
    #     #     data['H'] = {
    #     #         'shape': data['H'].shape,
    #     #         'data': data['H'].flatten().tolist(),
    #     #     }
    #     output['data'] = data
    #     return output


# 表示某个字段的配置文件没有这个过滤器
DEBUG_FLAG_FILTER_NOT_RUN = -1


def debug_filter_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        fg_item = args[0]
        if fg_item.debug_data or debugger.enabled:
            input_raw_data = [
                [it.text, *it.bbox] for it in fg_item.get_passed_nodes().values()
            ]

        flag = func(*args, **kwargs)
        if flag == DEBUG_FLAG_FILTER_NOT_RUN:
            return

        if fg_item.debug_data or debugger.enabled:
            output_raw_data = [
                [it.text, *it.bbox] for it in fg_item.get_passed_nodes().values()
            ]

            filter_name = func.__name__

        if fg_item.debug_data:
            if filter_name != "filter_area":
                # filter_area 的输入都是全部的 raw_data，没有必要保存输入
                fg_item.debug_data.add_rect_group(
                    fg_item.item_name,
                    f"{filter_name}_input",
                    input_raw_data,
                    DEBUG_TEMPLATE_FILTER_INPUT_COLOR,
                )

            fg_item.debug_data.add_rect_group(
                fg_item.item_name,
                f"{filter_name}_output",
                output_raw_data,
                DEBUG_TEMPLATE_FILTER_OUTPUT_COLOR,
            )

        if debugger.enabled:
            prefix = f"{fg_item.item_name}_{filter_name}"
            if filter_name != "filter_area":
                debugger.variables.add_group(
                    f"{prefix}_input", f"{prefix}_input", input_raw_data
                )

            debugger.variables.add_group(
                f"{prefix}_output", f"{prefix}_output", output_raw_data
            )

    return wrapper


class timeblock:
    def __init__(self, name="", debug_data=None):
        self.name = name
        self.elapsed_ms = 0
        self._debug_data = debug_data

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, type, value, traceback):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        if self._debug_data is not None:
            self._debug_data.set_process_time(self.name, self.elapsed_ms)
