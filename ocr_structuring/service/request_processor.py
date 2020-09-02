import json
import threading
import traceback
from datetime import datetime

from ..core.utils.debug_data import DebugData
from ..protos.structuring_pb2 import (
    StructuringResponse,
    StructuringRequest,
    StructuringRequestRotated,
)
from ..protos.structuring_pb2_grpc import StructuringServicer
from ..protos.structuring_pb2 import StructuringTimeInfo
from .util import image_from_image_data, images_from_image_datas
from ocr_structuring.service.extra_data import extra_data


class RequestProcessor:
    session = None
    lock = threading.Lock()

    def process(self, request, rpc_name, preload_tpl=True, **kwargs):
        structuring_data = None
        debug_data = DebugData()
        debug_data.fid = kwargs.get('item_name', '')
        # grpc string empty value is ''
        class_name = request.class_name if request.class_name != "" else None

        try:
            if self.session is None:
                with self.lock:
                    if self.session is None:
                        from .main import Session
                        if debug_data.fid:  # 结构化工具调试模式，只加载当前class_name对应模板
                            self.session = Session(preload_tpl, class_name)
                        else:  # 生产逻辑
                            self.session = Session(preload_tpl)
        except Exception as e:
            traceback.print_exc()
            return None

        if rpc_name in ["Process", "ProcessRotated"]:
            # grpc int empty value 0
            primary_class = (
                request.primary_class if request.primary_class != 0 else None
            )

            secondary_class = (
                request.secondary_class if request.secondary_class != 0 else None
            )

        if rpc_name == "Process":
            label_list = []
            for text in request.texts_full_data:
                label_list.append(
                    [
                        text.word,
                        text.bbox.left,
                        text.bbox.top,
                        text.bbox.right,
                        text.bbox.bottom,
                        text.label,
                        *text.probabilities,
                    ]
                )
            # 读取raw_data中的表格数据，存入extra_data单例中
            extra_data.read_data_from_request(request)

            with image_from_image_data(request.image_data) as image:
                structuring_data = self.session.process(
                    raw_data=label_list,
                    image=image,
                    class_name=class_name,
                    primary_class=primary_class,
                    secondary_class=secondary_class,
                    ltrb=True,
                    debug_data=debug_data
                )

        elif rpc_name == "ProcessRotated":
            label_list = []
            for text in request.texts_full_data:
                label_list.append(self._TextFullDataRotated_to_raw(text))
                # 读取raw_data中的表格数据，存入extra_data单例中

            extra_data.read_data_from_request(request)

            with image_from_image_data(request.image_data) as image:
                structuring_data = self.session.process(
                    raw_data=label_list,
                    image=image,
                    class_name=class_name,
                    primary_class=primary_class,
                    secondary_class=secondary_class,
                    ltrb=False,
                    debug_data=debug_data
                )

        elif rpc_name == "ProcessMultiImage":
            raw_datas = []
            image_datas = []
            extra_data.read_data_from_request(request)

            for single in request.multi_image_info:
                raw_data = []
                for text in single.texts_full_data:
                    raw_data.append(self._TextFullDataRotated_to_raw(text))
                raw_datas.append(raw_data)
                image_datas.append(single.image_data)

            with images_from_image_datas(image_datas) as images:
                structuring_data = self.session.process_multi(
                    raw_datas=raw_datas, images=images, class_name=class_name
                )

        return structuring_data

    def _TextFullDataRotated_to_raw(self, text_full_data_rotated):
        return [
            text_full_data_rotated.word,
            text_full_data_rotated.rbox.x1,
            text_full_data_rotated.rbox.y1,
            text_full_data_rotated.rbox.x2,
            text_full_data_rotated.rbox.y2,
            text_full_data_rotated.rbox.x3,
            text_full_data_rotated.rbox.y3,
            text_full_data_rotated.rbox.x4,
            text_full_data_rotated.rbox.y4,
            text_full_data_rotated.rbox.angle,
            text_full_data_rotated.label,
            *text_full_data_rotated.probabilities,
        ]
