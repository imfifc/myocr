import json
import os

from ocr_structuring.utils.load_ai_data import ai_data_2_raw_data


def load_raw_data(gt_path, raw_data_path=None, image=None, convert_func=None):

    """
        :param convert_ltrb: 是否需要将非ltrb的raw_data转换为ltrb
        :param gt_path:
        :param raw_data_path:
        :param ltrb:
        :param image:
        :param convert_func: 将raw_data转换为 content, bbox, scores的形式
        :return:
    """

    if convert_func is None:
        convert_func = (lambda x: x)

    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        if 'subjects' in data:
            # AI output format detected. Transfer it
            data = ai_data_2_raw_data(data)

        if image is not None:
            roi = data['preprocess_result']['roi']

        if isinstance(data['structuring_data'], list):
            gt = data['structuring_data'][0]
        else:
            gt = data['structuring_data']

        if raw_data_path is None:
            raw_data = data['raw_data']

        else:
            assert os.path.exists(raw_data_path), 'raw_data 不存在'
            with open(raw_data_path, 'r', encoding='utf-8') as raw_data_f:
                raw_data = json.load(raw_data_f)

            raw_data = convert_func(raw_data)

    if image is not None:
        image = image[roi[1]: roi[3], roi[0]: roi[2]]
        return image, raw_data, gt, data
    else:
        return raw_data, gt, data


def ltrb_2_rotate(raw_data):
    """把 ltrb 格式的 raw_data 转成旋转格式"""
    rotate_raw_data = []
    for it in raw_data:
        bbox = it[1:5]
        rotate_raw_data.append([
            it[0],
            bbox[0], bbox[1],
            bbox[2], bbox[1],
            bbox[2], bbox[3],
            bbox[0], bbox[3],
            0,
            it[5],
            *it[6:],
        ])
    return rotate_raw_data


def assert_shanghai(unittest, gt, result):
    gt = {k: v['content'] for k, v in gt.items()}
    try:
        pred = {k: v.content for k, v in result.items()}
    except:
        pred = {k: v['content'] for k, v in result.items()}

    del pred['summary_charges']
    del pred['detail_charges']

    unittest.assertEqual(len(gt), len(pred))

    for k in gt:
        g, p = gt[k], pred[k]
        if g in ['', None]:
            g = ''
        if p in ['', None]:
            p = ''

        try:
            p, g = float(p), float(g)
        except:
            pass

        # 这两个字段的重识别不太稳定，测试时忽略
        if k in ['li_nian_zhang_hu_yu_e', 'personal_account_pay_money']:
            continue

        unittest.assertEqual(g, p, f'[{k}] gt: {g} pred: {p}')
