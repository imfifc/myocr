import os
import json
import unittest

import cv2
import grpc

from ocr_structuring.main import setup_grpc_server
from ocr_structuring.protos.structuring_pb2 import (
    StructuringRequest,
    BBox,
)
from ocr_structuring.protos.structuring_pb2_grpc import StructuringStub
from ocr_structuring.service import util

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
dummy_tpl_img_path = os.path.join(
    os.path.dirname(CURRENT_DIR), "core", "template", "config", "dummy_tpl.jpg"
)

GRPC_PORT = 30123

raw_data = [
    {
        "points": [
            {"x": 242, "y": 187},
            {"x": 319, "y": 187},
            {"x": 319, "y": 228},
            {"x": 242, "y": 228},
        ],
        "content": "金额",
        "probabilities": [0.55333686, 0.9999473],
    },
    {
        "points": [
            {"x": 629, "y": 345},
            {"x": 704, "y": 345},
            {"x": 704, "y": 386},
            {"x": 629, "y": 386},
        ],
        "content": "号码",
        "probabilities": [0.6288694, 0.99998415],
    },
    {
        "points": [
            {"x": 89, "y": 340},
            {"x": 163, "y": 340},
            {"x": 163, "y": 381},
            {"x": 89, "y": 381},
        ],
        "content": "日期",
        "probabilities": [0.99996376, 0.9999975],
    },
    {
        "points": [
            {"x": 626, "y": 77},
            {"x": 702, "y": 77},
            {"x": 702, "y": 116},
            {"x": 626, "y": 116},
        ],
        "content": "地址",
        "probabilities": [0.9999956, 0.99969506],
    },
    {
        "points": [
            {"x": 89, "y": 62},
            {"x": 163, "y": 62},
            {"x": 163, "y": 102},
            {"x": 89, "y": 102},
        ],
        "content": "姓名",
        "probabilities": [0.99886715, 0.99980885],
    },
    {
        "points": [
            {"x": 360, "y": 193},
            {"x": 397, "y": 193},
            {"x": 397, "y": 222},
            {"x": 360, "y": 222},
        ],
        "content": "42",
        "probabilities": [0.9891472, 0.99995244],
    },
]


class TestDummy(unittest.TestCase):
    def setUp(self):
        self.server = setup_grpc_server(GRPC_PORT)

    def tearDown(self):
        self.server.stop(0)

    def test_non_template_structuring(self):
        image = cv2.imread(dummy_tpl_img_path)

        with grpc.insecure_channel(
            "localhost:%s" % GRPC_PORT,
            options=[
                ("grpc.max_receive_message_length", 104857600),
                ("grpc.max_send_message_length", 104857600),
            ],
        ) as channel:
            stub = StructuringStub(channel)

            request = StructuringRequest(
                class_name="dummy_non_tpl", image_data=util.dump_image(image),
            )

            for it in raw_data:
                request.texts_full_data.add(
                    bbox=BBox(
                        left=it["points"][0]["x"],
                        top=it["points"][0]["y"],
                        right=it["points"][2]["x"],
                        bottom=it["points"][2]["y"],
                    ),
                    word=it["content"],
                    label=1,
                    probabilities=it["probabilities"],
                )

            response = stub.Process(request, timeout=30)
            pred = json.loads(response.data)
            print("Non template result", pred)
            self.assertEqual(pred["money"]["content"], "42")

    def test_template_structuring(self):
        image = cv2.imread(dummy_tpl_img_path)

        with grpc.insecure_channel(
            "localhost:%s" % GRPC_PORT,
            options=[
                ("grpc.max_receive_message_length", 104857600),
                ("grpc.max_send_message_length", 104857600),
            ],
        ) as channel:
            stub = StructuringStub(channel)

            request = StructuringRequest(
                class_name="dummy_tpl", image_data=util.dump_image(image),
            )

            for it in raw_data:
                request.texts_full_data.add(
                    bbox=BBox(
                        left=it["points"][0]["x"],
                        top=it["points"][0]["y"],
                        right=it["points"][2]["x"],
                        bottom=it["points"][2]["y"],
                    ),
                    word=it["content"],
                    label=1,
                    probabilities=it["probabilities"],
                )

            response = stub.Process(request, timeout=30)
            pred = json.loads(response.data)
            print("template result", pred)
            self.assertEqual(pred["money"]["content"], "42")


if __name__ == "__main__":
    unittest.main()
