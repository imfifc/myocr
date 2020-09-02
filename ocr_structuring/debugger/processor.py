import base64
import json
import multiprocessing as mp
import os
import shutil
import sys
import time
from typing import Optional

import cv2
from tqdm import tqdm

from ocr_structuring import debugger
from ocr_structuring.protos.structuring_pb2 import StructuringRequest, StructuringRequestRotated, BBox, RotatedBox, \
    SingleDetectionResult
from ocr_structuring.service.main import Session
from ocr_structuring.service.request_processor import RequestProcessor
from ocr_structuring.service.util import dump_image
from ocr_structuring.utils.logging import logger

# pytorch CPU 模式下和 multiprocessing 一起使用时会很慢
# Issue: https://github.com/pytorch/pytorch/issues/9873
# From xl.li: https://stackoverflow.com/questions/15414027/multiprocessing-pool-makes-numpy-matrix-multiplication-slower
os.environ['OMP_NUM_THREADS'] = '1'


class ProcessConfig:
    result_dirname = "structure_result"
    recognition_data_dirname = "rec_data"
    recognition_img_dirname = "rec_img"

    def __init__(self,
                 class_name: str,
                 primary_class: int,
                 secondary_class: int,
                 preload_tpl: bool,
                 use_img: bool,
                 process_count: int = 0,
                 debug_server_addr: Optional[str] = None,
                 lab_id: int = 0,
                 exp_id: int = 0,
                 raw_data_id: int = 0,
                 work_dir: Optional[str] = None,
                 ):
        self.class_name = class_name
        self.primary_class = primary_class
        self.secondary_class = secondary_class
        self.work_dir = work_dir
        self.preload_tpl = preload_tpl
        self.use_img = use_img
        self.process_count = process_count
        self.debug_server_addr = debug_server_addr
        self.lab_id = lab_id
        self.exp_id = exp_id
        self.raw_data_id = raw_data_id

    @property
    def is_single_debug(self):
        return bool(self.raw_data_id)

    @property
    def rec_data_dir_path(self):
        return os.path.join(self.work_dir, self.recognition_data_dirname)

    @property
    def rec_img_dir_path(self):
        return os.path.join(self.work_dir, self.recognition_img_dirname)

    def __str__(self):
        return json.dumps(self.__dict__)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)


class Processor:
    def __init__(self, config: ProcessConfig):
        self.config = config
        self.session = Session(self.config.preload_tpl, config.class_name)
        self.request_processor = RequestProcessor()

    def process_single(self, item_name: str):
        logger.info(f'processing {item_name}')
        # 开始前清理变量
        debugger.variables.clean()
        config = self.config

        if config.preload_tpl:
            debugger.variables.resultsTemplate.append({
                "name": "tplImage",
                "text": "模板图",
                "image": {
                    "data": "#{tplImage}"
                }
            })

        rec_data_dir = os.path.join(config.work_dir, config.recognition_data_dirname)
        rec_img_dir = os.path.join(config.work_dir, config.recognition_img_dirname)
        rec_data_path = os.path.join(rec_data_dir, item_name) + '.json'
        rec_img_path = os.path.join(rec_img_dir, item_name) + '.jpg'

        # 读取识别结果数据
        with open(rec_data_path, mode='r', encoding='utf-8') as f:
            rec_data = json.load(f)
        if not rec_data:
            logger.warning(f'raw_data is not present. path={rec_data_path}')
            return
        rec_img = cv2.imread(rec_img_path)

        if isinstance(rec_data, list):
            rec_data = [_convert_ai_rec_data_item(item) for item in rec_data]
            start_time = time.time()
            structure_result = self.session.process(
                rec_data,
                rec_img,
                class_name=self.config.class_name,
                primary_class=self.config.primary_class,
                secondary_class=self.config.secondary_class,
                ltrb=False
            )
        else:  # 新rawdata
            start_time = time.time()
            rec_img = cv2.imread(rec_img_path)
            request, rpc_name = _convert_request(rec_data, rec_img, self.config)
            # 开始结构化

            structure_result = self.request_processor.process(request, rpc_name, self.config.preload_tpl,
                                                              item_name=item_name)

        process_duration = time.time() - start_time
        logger.debug(f'耗时{process_duration}')
        debugger.variables.structuringDuration = process_duration

        # 收集结构化结果
        self._pack_debug_data(structure_result)
        self._dump_debug_data(item_name)

    def _dump_debug_data(self, item_name):
        dir_path = os.path.join(self.config.work_dir, self.config.result_dirname)
        filepath = os.path.join(dir_path, item_name + '.json')
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(filepath, mode='w', encoding='utf-8') as f:
            json.dump(debugger.variables, f, default=lambda obj: obj.__dict__, ensure_ascii=False)

    def _pack_debug_data(self, structure_result):
        # 只取content和probability
        pred = {}
        pred_probability = {}
        for k, v in structure_result['data'].items():
            if isinstance(v['content'], list):
                if not v['content']:
                    pred[k] = []
                    pred_probability[k] = []
                    continue
                if isinstance(v['content'][0], dict):
                    rows = []
                    row_probs = []
                    for index, subV in enumerate(v['content']):
                        row = {}
                        prob = {}
                        for rowK, rowV in subV.items():
                            row[rowK] = rowV['content']
                            prob[rowK] = rowV['probability']
                        rows.append(row)
                        row_probs.append(prob)
                    pred[k] = rows
                    pred_probability[k] = row_probs
                elif isinstance(v['content'][0], list):
                    # 支持没有定义列名的情况 List[List]
                    rows = []
                    for row in v['content']:
                        rows.append(row)
                    pred[k] = rows
                    pred_probability[k] = [1] * len(rows)
            else:
                pred[k] = v['content']
                pred_probability[k] = v['probability']
        debugger.variables.pred = pred
        debugger.variables.predProbability = pred_probability

    def process(self):
        config = self.config
        # 读取模板文件
        # 如果是基于模板的且开启debug，则读取模板图片
        if config.preload_tpl and debugger.enabled:
            debugger.commonVariables.tplImage = _read_tpl_as_base64(config.class_name)

        # torch 在多进程模式下，fork 会有问题，见：https://github.com/pytorch/pytorch/issues/17199
        # issue 中提到的 set_num_threads 的方法不生效，需要结合 os.environ['OMP_NUM_THREADS'] = '1' 才有用
        mp.set_start_method('spawn', force=True)
        # 删除旧结果目录
        result_dir = os.path.join(config.work_dir, config.result_dirname)
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
        os.makedirs(result_dir)

        rec_data_dir = os.path.join(config.work_dir, config.recognition_data_dirname)
        all_items = []
        for rec_data_filename in os.listdir(rec_data_dir):
            if not rec_data_filename.endswith('.json'):
                continue
            item_name, _ = os.path.splitext(rec_data_filename)
            all_items.append(item_name)

        if len(all_items) == 0:
            logger.warning('raw data not found')
            return

        # process_count为0表示根据CPU个数确定
        # 一般获取到的数字==所在机器的CPU个数，但部署在docker中后，实际可用的CPU个数可能比机器的CPU个数少
        # 所以这里使用代码获取真实的CPU个数，而不是给Pool传递None让其自动获取
        process_count = config.process_count or _get_available_cpu_count()
        logger.debug(f'process count is {process_count}')
        if process_count == 1 or len(all_items) == 1:
            for item_name in tqdm(all_items, file=sys.stdout):
                self.process_single(item_name)
        else:
            with mp.Pool(process_count, initializer=_process_pool_initializer, initargs=(debugger.enabled,)) as pool:
                list(tqdm(pool.imap_unordered(self.process_single, all_items), total=len(all_items), file=sys.stdout))


def _convert_ai_rec_data_item(item):
    """转换ai跑出的raw_data为结构化需要的格式"""
    points = item['points']
    return [
        item['content'],
        points[0]['x'],
        points[0]['y'],
        points[1]['x'],
        points[1]['y'],
        points[2]['x'],
        points[2]['y'],
        points[3]['x'],
        points[3]['y'],
        0,
        0,
        *item['probabilities']
    ]


def _convert_request(rec_data, img, config):
    if rec_data["request_method"] == "Process":
        request = StructuringRequest(
            class_name=config.class_name,
            primary_class=config.primary_class,
            secondary_class=config.secondary_class,
            image_data=dump_image(img),
        )
        data = rec_data["request_data"]["structuring_request"]
        if "texts_full_data" in data.keys() and data["texts_full_data"] != None:
            texts_full_data = data["texts_full_data"]
            for text_full_data in texts_full_data:
                request.texts_full_data.add(
                    word=text_full_data["word"],
                    bbox=BBox(
                        left=text_full_data["bbox"]["left"],
                        top=text_full_data["bbox"]["top"],
                        right=text_full_data["bbox"]["right"],
                        bottom=text_full_data["bbox"]["bottom"],
                    ),
                    label=text_full_data["label"],
                    probabilities=text_full_data["probabilities"],
                )
        if "labeled_bbox_list" in data.keys() and data["labeled_bbox_list"] != None:
            labeled_bbox_list = data["labeled_bbox_list"]
            for bbox_with_label in labeled_bbox_list:
                request.labeled_bbox_list.add(
                    bbox=RotatedBox(
                        x1=bbox_with_label["bbox"]["x1"],
                        y1=bbox_with_label["bbox"]["y1"],
                        x2=bbox_with_label["bbox"]["x2"],
                        y2=bbox_with_label["bbox"]["y2"],
                        x3=bbox_with_label["bbox"]["x3"],
                        y3=bbox_with_label["bbox"]["y3"],
                        x4=bbox_with_label["bbox"]["x4"],
                        y4=bbox_with_label["bbox"]["y4"],
                        angle=bbox_with_label["bbox"]["angle"],
                    ),
                    label=bbox_with_label["label"],
                )
        if "detection_results" in data.keys() and data["detection_results"]:
            detection_results = data["detection_results"]
            for single_detection_result in detection_results:
                rotated_box_with_label = SingleDetectionResult()
                labeled_bbox_list = single_detection_result["labeled_bboxes"]
                if labeled_bbox_list:
                    for bbox_with_label in labeled_bbox_list:
                        rotated_box_with_label.labeled_bbox_list.add(
                            bbox=RotatedBox(
                                x1=bbox_with_label["bbox"]["x1"],
                                y1=bbox_with_label["bbox"]["y1"],
                                x2=bbox_with_label["bbox"]["x2"],
                                y2=bbox_with_label["bbox"]["y2"],
                                x3=bbox_with_label["bbox"]["x3"],
                                y3=bbox_with_label["bbox"]["y3"],
                                x4=bbox_with_label["bbox"]["x4"],
                                y4=bbox_with_label["bbox"]["y4"],
                                angle=bbox_with_label["bbox"]["angle"],
                            ),
                            label=bbox_with_label["label"],
                        )
                request.detection_results.add(
                    labeled_bbox_list=rotated_box_with_label.labeled_bbox_list
                )
        return request, rec_data["request_method"]
    elif rec_data["request_method"] == "ProcessRotated":
        request = StructuringRequestRotated(
            class_name=config.class_name,
            primary_class=config.primary_class,
            secondary_class=config.secondary_class,
            image_data=dump_image(img),
        )
        data = rec_data["request_data"]["structuring_request_rotated"]
        if "texts_full_data" in data.keys() and data["texts_full_data"] != None:
            texts_full_data = data["texts_full_data"]
            for text_full_data in texts_full_data:
                request.texts_full_data.add(
                    word=text_full_data["word"],
                    rbox=RotatedBox(
                        x1=text_full_data["rbox"]["x1"],
                        y1=text_full_data["rbox"]["y1"],
                        x2=text_full_data["rbox"]["x2"],
                        y2=text_full_data["rbox"]["y2"],
                        x3=text_full_data["rbox"]["x3"],
                        y3=text_full_data["rbox"]["y3"],
                        x4=text_full_data["rbox"]["x4"],
                        y4=text_full_data["rbox"]["y4"],
                        angle=text_full_data["rbox"]["angle"]
                    ),
                    label=text_full_data["label"],
                    probabilities=text_full_data["probabilities"],
                )
        if "labeled_bbox_list" in data.keys() and data["labeled_bbox_list"] != None:
            labeled_bbox_list = data["labeled_bbox_list"]
            for bbox_with_label in labeled_bbox_list:
                request.labeled_bbox_list.add(
                    bbox=RotatedBox(
                        x1=bbox_with_label["bbox"]["x1"],
                        y1=bbox_with_label["bbox"]["y1"],
                        x2=bbox_with_label["bbox"]["x2"],
                        y2=bbox_with_label["bbox"]["y2"],
                        x3=bbox_with_label["bbox"]["x3"],
                        y3=bbox_with_label["bbox"]["y3"],
                        x4=bbox_with_label["bbox"]["x4"],
                        y4=bbox_with_label["bbox"]["y4"],
                        angle=bbox_with_label["bbox"]["angle"],
                    ),
                    label=bbox_with_label["label"],
                )
        if "detection_results" in data.keys() and data["detection_results"]:
            detection_results = data["detection_results"]
            for single_detection_result in detection_results:
                rotated_box_with_label = SingleDetectionResult()
                labeled_bbox_list = single_detection_result["labeled_bboxes"]
                if labeled_bbox_list:
                    for bbox_with_label in labeled_bbox_list:
                        rotated_box_with_label.labeled_bbox_list.add(
                            bbox=RotatedBox(
                                x1=bbox_with_label["bbox"]["x1"],
                                y1=bbox_with_label["bbox"]["y1"],
                                x2=bbox_with_label["bbox"]["x2"],
                                y2=bbox_with_label["bbox"]["y2"],
                                x3=bbox_with_label["bbox"]["x3"],
                                y3=bbox_with_label["bbox"]["y3"],
                                x4=bbox_with_label["bbox"]["x4"],
                                y4=bbox_with_label["bbox"]["y4"],
                                angle=bbox_with_label["bbox"]["angle"],
                            ),
                            label=bbox_with_label["label"],
                        )
                request.detection_results.add(
                    labeled_bbox_list=rotated_box_with_label.labeled_bbox_list
                )
        return request, rec_data["request_method"]
    else:
        return None, None


def _read_img_as_base64(img_path):
    with open(img_path, 'rb') as f:
        return str(base64.b64encode(f.read()), 'utf-8')


def _read_tpl_as_base64(class_name):
    img_path = os.path.join(
        os.path.dirname(__file__),
        f'../core/template/config/{class_name}.jpg'
    )
    return _read_img_as_base64(img_path)


def _process_pool_initializer(debug_enabled):
    # spawn模式下子进程不会继承父进程的变量，需要在这里初始化
    debugger.enabled = debug_enabled


def _get_available_cpu_count():
    """
    获取可用的CPU个数，如果使用了cgroup来控制cpu使用配额，从读取该值，否则使用系统提供的获取cpu
    :return:
    """
    if os.path.isfile('/sys/fs/cgroup/cpu/cpu.cfs_quota_us'):
        cpu_quota = int(open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read().rstrip())
        if cpu_quota != -1 and os.path.isfile('/sys/fs/cgroup/cpu/cpu.cfs_period_us'):
            cpu_period = int(open('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read().rstrip())
            return int(cpu_quota / cpu_period)

    return os.cpu_count()
