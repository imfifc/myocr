import json
import logging
import multiprocessing as mp
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import List

import cv2
import git
import requests
from tornado import ioloop, httpclient
from tqdm import tqdm

from ocr_structuring.core.utils.debug_data import DebugData
from ocr_structuring.service.main import Session
from ocr_structuring.utils.load_ai_data import ai_data_2_raw_data
from .image import rotate_image_by_90, rotate_image, rotate_image_expand
from ..service.extra_data import extra_data

logger = logging.getLogger('run_structure')
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)

# pytorch CPU 模式下和 multiprocessing 一起使用时会很慢
# Issue: https://github.com/pytorch/pytorch/issues/9873
# From xl.li: https://stackoverflow.com/questions/15414027/multiprocessing-pool-makes-numpy-matrix-multiplication-slower
os.environ['OMP_NUM_THREADS'] = '1'


def dump_data(data, structure_result, out_dir: Path, filename):
    data['structuring_data'] = structure_result['data']
    data['structuring_meta'] = [
        {
            'class_name': structure_result['metadata']['class_name'],
            # 'template_category': structure_result['metadata']['template_category'],
        }
    ]

    # 在这里添加一些对医疗发票相关的逻辑
    # 对 detail_charges/summary_charges 的结果提取成table_data相关的东西
    def convert_to_table_data_for_easy_test(item_name, keys):
        charges = data['structuring_data'].get(item_name)
        if charges is not None:
            format_charges = []
            for item in charges['content']:
                format_charges.append({k: item[k] for k in keys})
            data['structuring_data'][item_name] = format_charges

    convert_to_table_data_for_easy_test('detail_charges', ['name', 'unit_price', 'total_price'])
    convert_to_table_data_for_easy_test('summary_charges', ['name', 'charge'])

    with open(str(out_dir / filename), mode='w', encoding='utf-8') as f:
        data['structuring_data'] = [data['structuring_data']]
        json.dump(data, f, default=lambda obj: obj.__dict__, ensure_ascii=False, indent=2)


def load_gt_data(gt_img_path, data):
    gt_img = cv2.imread(str(gt_img_path))
    if 'preprocess_result' not in data:
        return gt_img, []

    if data['preprocess_result'].get('scale') is not None and data['preprocess_result']['scale'][0] != -1:
        gt_img = cv2.resize(gt_img, tuple(data['preprocess_result']['scale']))

    roi = data['preprocess_result']['roi']
    if len(roi) != 0:
        cropped_img = gt_img[roi[1]: roi[3], roi[0]: roi[2]]
    else:
        cropped_img = gt_img

    try:
        rotation = data['preprocess_result']['orientation']['executed_rotation'] or 0
    except Exception:
        logger.warning('failed to get rotation from raw_data: %s', data)
        rotation = 0
    img = rotate_image_by_90(cropped_img, rotation)

    try:
        angle = data['preprocess_result']['small_angle_adjust'].get('angle')
        if angle is not None:

            expand_enabled = data['preprocess_result']['small_angle_adjust_expand_enabled']
            img = rotate_image_expand(img, angle) if expand_enabled else rotate_image(img, angle)
    except Exception:
        logger.warning('failed to get small angle adjust from raw_data')

    return img, roi


def find_gt_img_path(gt_dir: Path, raw_file: Path):
    """
    这里假设 gt 图片可能是 jpg 或者 png，优先找 jpg
    """
    jpg = gt_dir / raw_file.with_suffix('.jpg').name
    png = gt_dir / raw_file.with_suffix('.png').name

    if jpg.exists():
        return jpg

    if png.exists():
        return png


class MyProcessor:
    def __init__(self, class_name: str, raw_dir: Path, gt_dir: Path, output_dir: Path, ltrb=True,
                 should_init_tp_structure=True, sts_skip_structure=False):
        self.class_name = class_name
        self.raw_dir = raw_dir
        self.gt_dir = gt_dir
        self.output_dir = output_dir
        self.session = Session(should_init_tp_structure)
        self.sts_skip_structure = sts_skip_structure
        self.ltrb = ltrb

    def __call__(self, raw_file: Path):
        print(f'Processing file: {raw_file}')
        gt_img_path = find_gt_img_path(self.gt_dir, raw_file)
        if not gt_img_path:
            return

        with open(str(raw_file), mode='r', encoding='utf-8') as f:
            data = json.load(f)
        extra_data.read_data_from_file(data)
        if 'subjects' in data:
            # AI output format detected. Transfer it
            data = ai_data_2_raw_data(data)

        gt_img, roi = load_gt_data(gt_img_path, data)

        debug_data = DebugData()
        debug_data.fid = gt_img_path.stem
        debug_data.gt_img_name = gt_img_path.name
        debug_data.roi = roi
        debug_data.is_ltrb = self.ltrb
        debug_data.set_raw_data(data['raw_data'], self.ltrb)

        start_time = time.time()
        if self.sts_skip_structure:
            debug_data.set_structure_result({'dummy_item': {'content': 1}})
            return debug_data

        structure_result = self.session.process(data['raw_data'],
                                                gt_img,
                                                class_name=self.class_name,
                                                debug_data=debug_data,
                                                ltrb=self.ltrb)
        end_time = time.time()
        debug_data.process_time['session.process'] = (end_time - start_time) * 1000
        debug_data.set_structure_result(structure_result['data'])

        dump_data(data, structure_result, self.output_dir, raw_file.name)
        return debug_data


class StsServerConfig:
    def __init__(self, url, category, name, dataset_name):
        self.url = url
        self.category = category
        self.name = name
        self.dataset_name = dataset_name

        self.experiments_url = f"{self.url}/api/core/experiments/"
        self.subjects_url = f"{self.url}/api/core/subjects/"

    def check_exit(self):
        with requests.Session() as r:
            resp = r.request(
                method='GET',
                url=self.experiments_url,
                timeout=60,
                params={
                    'category': self.category,
                    'name': self.name,
                }
            )
            resp.raise_for_status()
            resp_data = resp.json()
            if resp_data['code'] != 0:
                raise AssertionError('[Backend] create experiment failed since %s: %s' % (resp_data['code'],
                                                                                          resp_data['message']))
            if len(resp_data['data']['results']) > 0:
                # 已经拥有同类同名的实验了
                logger.error(f'category: {self.category}, name: {self.name} already exist.')
                raise AssertionError(f'[Backend] category: {self.category}, name: {self.name} already exist.')

    def upload_to_sts_server(self, class_name: str, debug_datas: List[DebugData]):
        try:
            root_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
            repo = git.Repo(root_dir)
            branch_name = repo.active_branch.name
            commit = repo.head.object.hexsha
        except Exception:
            branch_name = 'unknown'
            commit = 'unknown'

        with requests.Session() as r:
            resp = r.request(
                method='POST',
                url=self.experiments_url,
                timeout=60,
                json={
                    'template_name': class_name,
                    'category': self.category,
                    'name': self.name,
                    'dataset_name': self.dataset_name,
                    'branch_name': branch_name,
                    'commit': commit,
                }
            )
            resp.raise_for_status()
            resp_data = resp.json()
            if resp_data['code'] != 0:
                raise AssertionError('[Backend] create experiment failed since %s: %s' % (resp_data['code'],
                                                                                          resp_data['message']))
            experiment_id = resp_data['data']['id']
            logger.info(f"Create experiment successful: {experiment_id}")

        tornado_client = httpclient.AsyncHTTPClient(force_instance=True, defaults={
            'request_timeout': 3600,
            'connect_timeout': 3600,
        })
        counter = tqdm(total=len(debug_datas))

        def handle_response(response):
            response = response.result()  # 这里的response是一个Future

            data = json.loads(response.body.decode('utf-8'))
            if data['code'] != 0:
                print('[Backend] create subject failed since %s: %s' % (data['code'], data['message']))
                tornado_client.io_loop.stop()
                return
            counter.update(1)
            if counter.n >= counter.total:
                tornado_client.io_loop.stop()

        for exp_data in debug_datas:
            if exp_data is None:
                continue

            def prepare_func(data: DebugData):
                def request_func():
                    query_body = {
                        'fid': data.fid,
                        'input': {},
                        'gt': {},
                        'output': {},
                        'experiment_id': experiment_id,
                        'data': data
                    }

                    future = tornado_client.fetch(
                        httpclient.HTTPRequest(
                            method='POST',
                            url=self.subjects_url,
                            headers={
                                'Content-Type': 'application/json',
                            },
                            body=json.dumps(query_body, default=lambda obj: obj.__dict__, ensure_ascii=False),
                        )
                    )
                    ioloop.future_add_done_callback(future, handle_response)

                return request_func

            tornado_client.io_loop.call_later(0, prepare_func(exp_data))
        tornado_client.io_loop.start()

        # 最后检查一下是不是全部做完了
        if counter.n < counter.total:
            raise AssertionError('[Backend] failed to upload everything: %s/%s' % (counter.n, counter.total))
        counter.close()


def run(class_name: str, raw_dir: Path, gt_dir: Path, output_dir: Path, num_processes=1, target_fid=None,
        ltrb=True, should_init_tp_structure=True, sts_cfg: StsServerConfig = None, sts_skip_structure=False):
    # torch 在多进程模式下，fork 会有问题，见：https://github.com/pytorch/pytorch/issues/17199
    # issue 中提到的 set_num_threads 的方法不生效，需要结合 os.environ['OMP_NUM_THREADS'] = '1' 才有用
    mp.set_start_method('spawn', force=True)

    file_list = list(raw_dir.glob('*.json'))
    if len(file_list) == 0:
        file_list = list(raw_dir.glob('*.txt'))

    # FID_SUPPORT_LIST = [
    #     # '40abb5a0cfc9444393e38cdeed96527f'
    #     # '0002555881'
    #     '0000396391'
    # ]
    # file_list = [it for it in file_list if it.stem in FID_SUPPORT_LIST]

    if target_fid:
        file_list = [it for it in file_list if it.stem == target_fid]

    if num_processes == 1:
        processer = MyProcessor(class_name, raw_dir, gt_dir, output_dir, ltrb=ltrb,
                                should_init_tp_structure=should_init_tp_structure,
                                sts_skip_structure=sts_skip_structure)
        debug_datas = [processer(it) for it in file_list]
    else:
        with mp.Pool(num_processes) as pool:
            debug_datas = list(tqdm(pool.imap_unordered(
                MyProcessor(class_name, raw_dir, gt_dir, output_dir, ltrb=ltrb,
                            should_init_tp_structure=should_init_tp_structure,
                            sts_skip_structure=sts_skip_structure),
                file_list), total=len(file_list)))

    debug_datas = list(filter(lambda x: x is not None, debug_datas))

    process_time = defaultdict(list)
    for it in debug_datas:
        for k, v in it.process_time.items():
            process_time[k].append(v)

    for name, it in process_time.items():
        print(f'Average [{name}] time: {sum(it) / len(it):.3f}ms')

    if sts_cfg is not None:
        sts_cfg.upload_to_sts_server(class_name, debug_datas)
