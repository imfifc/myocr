import argparse
import json
import logging
import os
import sys
from concurrent.futures.thread import ThreadPoolExecutor

import requests
# noinspection PyUnresolvedReferences
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from ocr_structuring import debugger
from ocr_structuring.debugger.processor import Processor, ProcessConfig
from ocr_structuring.utils.logging import logger
from scripts.st_client import StClient

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def _bool_arg_converter(text):
    return str(text).lower().strip() not in ['false', '']


def nullable_int_converter(text):
    if text is None or text == '':
        return None
    return int(text)


def _rec_cache_available(config):
    paths_exists = os.path.exists(config.rec_data_dir_path) and os.path.exists(config.rec_img_dir_path)
    if not paths_exists:
        return False
    data_count = len(os.listdir(config.rec_data_dir_path))
    img_count = len(os.listdir(config.rec_img_dir_path))
    return data_count == img_count and data_count > 0


def prepare_data(config, with_cache=True):
    if with_cache:
        if _rec_cache_available(config):
            logger.info('recognition result data and image exists, using cache')
            return
        logger.info('recognition result data and image not exists, fetching from server')

    st_client = StClient(config.debug_server_addr)
    raws = st_client.fetch_raw_data_list(config.lab_id, 1, 10000)
    rec_data_dir = os.path.join(config.work_dir, config.recognition_data_dirname)
    rec_img_dir = os.path.join(config.work_dir, config.recognition_img_dirname)
    img_pool_dir = os.path.join(os.path.dirname(config.work_dir), "ocr_structuring_img_pool")
    os.makedirs(img_pool_dir, exist_ok=True)
    os.makedirs(rec_data_dir, exist_ok=True)
    os.makedirs(rec_img_dir, exist_ok=True)

    def get_data(raw):
        if not os.path.exists(os.path.join(rec_data_dir, str(raw['id'])) + '.json'):
            with open(os.path.join(rec_data_dir, str(raw['id'])) + '.json', 'w', encoding='utf-8') as f:
                json.dump(raw['data'], f, ensure_ascii=False, indent=2)
        if config.use_img:
            assert raw['media_id'] is not None
            if not os.path.exists(os.path.join(img_pool_dir, str(raw['media_id']) + '.jpg')):
                st_client.download_media(raw['media_id'], os.path.join(img_pool_dir, str(raw['media_id']) + '.jpg'))
            if not os.path.exists(os.path.join(rec_img_dir, str(raw['id']) + '.jpg')):
                os.symlink(os.path.join(img_pool_dir, str(raw['media_id']) + '.jpg'),
                           os.path.join(rec_img_dir, str(raw['id']) + '.jpg'))

    def get_data_by_gt_id(raw):
        # 保存时使用 gt_id 作为文件名
        with open(os.path.join(rec_data_dir, str(raw['gt_id'])) + '.json', 'w', encoding='utf-8') as f:
            json.dump(raw['data'], f, ensure_ascii=False, indent=2)
        if config.use_img:
            assert raw['media_id'] is not None
            st_client.download_media(raw['media_id'], os.path.join(rec_img_dir, str(raw['gt_id']) + '.jpg'))

    with ThreadPoolExecutor(3) as executor:
        for raw in raws['items']:
            executor.submit(get_data, raw)
            # executor.submit(get_data_by_gt_id, raw)


def upload_to_server(config):
    result_dir_path = os.path.join(config.work_dir, config.result_dirname)

    if not os.path.exists(result_dir_path):
        logger.info('experiment result not exists, abort upload')
        return
    filenames = os.listdir(result_dir_path)
    if len(filenames) == 0:
        return
    data = {
        'items': {},
        'commonVariables': debugger.commonVariables,
    }
    for filename in filenames:
        item_name, _ = os.path.splitext(filename)
        with open(os.path.join(result_dir_path, filename), encoding='utf-8') as f:
            json_data = json.load(f)
            data['items'][item_name] = json_data
    # result_json = json.dumps(data, ensure_ascii=False, default=lambda x: x.__dict__)
    # logger.debug(f'experiment result: {result_json}')
    StClient(config.debug_server_addr).upload_experiment_result(config.exp_id, data)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--class_name', type=str, required=False, default=None)
    parser.add_argument('--primary_class', type=nullable_int_converter, required=False)
    parser.add_argument('--secondary_class', type=nullable_int_converter, required=False)
    parser.add_argument('--preload_tpl', type=_bool_arg_converter, required=True)
    parser.add_argument('--process_count', type=int, required=True)
    parser.add_argument('--use_img', type=_bool_arg_converter, required=True)
    parser.add_argument('--debug_server_addr', type=str, required=True)
    parser.add_argument('--lab_id', type=int, required=True)
    parser.add_argument('--exp_id', type=int, required=True)
    parser.add_argument('--raw_data_id', type=int, required=False, default=0)
    parser.add_argument('--work_dir', type=str, required=True)

    opts = parser.parse_args()
    debugger.enabled = True
    config = ProcessConfig(
        class_name=opts.class_name,
        primary_class=opts.primary_class,
        secondary_class=opts.secondary_class,
        use_img=opts.use_img,
        preload_tpl=opts.preload_tpl,
        process_count=opts.process_count,
        debug_server_addr=opts.debug_server_addr,
        lab_id=opts.lab_id,
        exp_id=opts.exp_id,
        raw_data_id=opts.raw_data_id,
        work_dir=opts.work_dir,
    )

    processor = Processor(config)
    if config.is_single_debug:
        # 处理单张
        processor.process_single(str(config.raw_data_id))
    else:
        logger.info('preparing debug data')
        prepare_data(config)
        logger.info('processing')
        processor.process()
        if config.debug_server_addr:
            logger.info('uploading experiment result...')
            upload_to_server(config)
            logger.info('upload experiment result success.')
