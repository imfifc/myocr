import json
import sys
from pathlib import Path
from typing import List

import cv2

sys.path.insert(0, "../")
sys.path.insert(0, "../ocr_structuring")
import multiprocessing

multiprocessing.freeze_support()
from scripts.common_args import get_common_parser
from ocr_structuring.service.request_processor import RequestProcessor
from ocr_structuring.protos.structuring_pb2 import (
    MultiImageStructuringRequest,
    RotatedBox,
    SingleImageInfo,
)
from ocr_structuring.service.util import dump_image


def convert_rawdata_to_singleImageInfo(raw_file_path, img_file_path):
    img = cv2.imread(str(img_file_path))
    single_image_info = SingleImageInfo(image_data=dump_image(img))

    with open(str(raw_file_path), mode="r", encoding="utf-8") as f:
        json_data = json.load(f)
    rotated_texts = json_data["subjects"][0]["recognition"]["rotated_texts"]
    for text in rotated_texts:
        single_image_info.texts_full_data.add(
            word=text["chars"]["content"],
            label=text["labeled_bbox"]["label"],
            rbox=RotatedBox(
                x1=text["labeled_bbox"]["bbox"]["x1"],
                y1=text["labeled_bbox"]["bbox"]["y1"],
                x2=text["labeled_bbox"]["bbox"]["x2"],
                y2=text["labeled_bbox"]["bbox"]["y2"],
                x3=text["labeled_bbox"]["bbox"]["x3"],
                y3=text["labeled_bbox"]["bbox"]["y3"],
                x4=text["labeled_bbox"]["bbox"]["x4"],
                y4=text["labeled_bbox"]["bbox"]["y4"],
                angle=text["labeled_bbox"]["bbox"]["angle"],
            ),
            probabilities=text["chars"]["probabilities"],
        )

    labeled_bboxes = json_data["subjects"][0]["table_detectron"]["labeled_bboxes"]
    if labeled_bboxes is not None:
        for labeled_bbox in labeled_bboxes:
            single_image_info.labeled_bbox_list.add(
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
    # else:
    #     # 确保角点检测的页码顺序和 OCR 的结果对齐
    #     single_image_info.labeled_bbox_list = None
    return single_image_info


def zhong_hang_classifity_test():
    pass


def convert_request(single_image_info_list, class_name):
    request = MultiImageStructuringRequest(class_name=class_name)
    for single_image_info in single_image_info_list:
        request.multi_image_info.add(
            image_data=single_image_info.image_data,
            texts_full_data=single_image_info.texts_full_data,
            labeled_bbox_list=single_image_info.labeled_bbox_list,
        )
    return request


if __name__ == "__main__":

    def parse_args():
        parser = get_common_parser()
        parser.add_argument("--class_name", required=True, help="结构化的类型")
        parser.add_argument("--raw_dir", required=True, help="存放检测识别json结果")
        parser.add_argument("--img_dir", required=True, help="存放图片")
        parser.add_argument("--out_dir", required=True, help="保存结构化结果")
        parser.add_argument("--num_processes", type=int, default=1, help="跑结构化的进程数")
        parser.add_argument("--target_fid", default=None, help="指定跑某一个文件")
        parser.add_argument(
            "--skip_load_tp_config",
            action="store_true",
            help="不加载模板结构化的配置文件，对于调试非模板的结构化可以提高调试效率",
        )
        parser.add_argument("--not_ltrb", action="store_true")

        args = parser.parse_args()

        args.raw_dir = Path(args.raw_dir)
        args.img_dir = Path(args.img_dir)
        args.out_dir = Path(args.out_dir)
        args.ltrb = not args.not_ltrb

        if not args.raw_dir.exists():
            parser.error(f"raw_dir not exist: {args.raw_dir}")

        if not args.out_dir.exists():
            args.out_dir.mkdir(exist_ok=True, parents=True)

        return args

    cmd_args = parse_args()

    img_dir_subdir_names: List[Path] = list(
        filter(lambda x: x.is_dir(), cmd_args.img_dir.iterdir())
    )
    img_dir_subdir_names: List[str] = [it.name for it in img_dir_subdir_names]

    raw_sub_dirs: List[Path] = []
    for raw_it in cmd_args.raw_dir.iterdir():
        if not raw_it.is_dir():
            continue
        if raw_it.name not in img_dir_subdir_names:
            print(f"Can't find img_dir for raw_dir {raw_it}")
            continue
        raw_sub_dirs.append(raw_it)

    def get_sub_num(file_name: Path):
        return int(file_name.stem.split("-")[-1])

    structure_results = {}

    request_processor = RequestProcessor()
    for raw_sub_dir in raw_sub_dirs:
        print(f"Process pdf: {raw_sub_dir}")
        single_image_info_list = []
        raw_paths = sorted(raw_sub_dir.glob("*.json"), key=lambda x: get_sub_num(x))
        for i, raw_path in enumerate(raw_paths):
            img_path: Path = cmd_args.img_dir / raw_path.parent.name / raw_path.with_suffix(
                ".jpg"
            ).name
            if not img_path.exists():
                print(f"raw data image: {img_path} not exist")
                continue
            single_image_info = convert_rawdata_to_singleImageInfo(raw_path, img_path)
            single_image_info_list.append(single_image_info)

        request = convert_request(single_image_info_list, cmd_args.class_name)

        structure_result = request_processor.process(
            request, "ProcessMultiImage", False
        )
        structure_results[raw_sub_dir.name] = structure_result

        for doc_content in structure_result["data"]["contents"]:
            print(f"{doc_content['doc_type']} page: {doc_content['pages']}")

        with open(
            cmd_args.out_dir / (raw_sub_dir.name + ".json"), "w", encoding="utf-8"
        ) as f:
            json.dump(structure_result, f, indent=2, ensure_ascii=False)
