import os


class ExtraData:
    def __init__(self):
        self.fields = []
        self.data = {}
        self.add_field()

    def add_field(self):
        with open(os.path.join(os.path.dirname(__file__), 'extra_data_fields.txt')) as f:
            for line in f.readlines():
                self.fields.append(line.strip())

    def read_data_from_request(self, request):
        try:
            self.data["labeled_bbox_list"] = request.labeled_bbox_list
        except:
            self.data["labeled_bbox_list"] = None

        try:
            self.data["multi_image_info"] = request.multi_image_info
        except:
            self.data["multi_image_info"] = None

        try:
            self.data["detection_results"] = request.detection_results
        except:
            self.data["detection_results"] = None

    def read_data_from_file(self, ai_data):
        from ocr_structuring.protos.structuring_pb2 import RotatedBoxWithLabel, RotatedBox
        try:
            self.current_cells = []
            subject = ai_data['subjects'][0]
            bbox_list = []
            for labeled_bbox in subject['table_detectron']['labeled_bboxes']:
                grpc_labeled_bbox = RotatedBoxWithLabel(
                    bbox=RotatedBox(
                        x1=labeled_bbox["bbox"]["x1"],
                        y1=labeled_bbox["bbox"]["y1"],
                        x2=labeled_bbox["bbox"]["x2"],
                        y2=labeled_bbox["bbox"]["y2"],
                        x3=labeled_bbox["bbox"]["x3"],
                        y3=labeled_bbox["bbox"]["y3"],
                        x4=labeled_bbox["bbox"]["x4"],
                        y4=labeled_bbox["bbox"]["y4"],
                        angle=labeled_bbox["bbox"]["angle"],
                    ),
                    label=labeled_bbox["label"],
                )
                bbox_list.append(grpc_labeled_bbox)
            self.data["labeled_bbox_list"] = bbox_list
        except:
            self.data["labeled_bbox_list"] = []


extra_data = ExtraData()
