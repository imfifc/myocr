# encoding=utf-8
import json
from pathlib import Path
from typing import Dict, List

from .const import SUMMARY_TOTAL_MONEY
from .utils import logger


class Testee:
    def __init__(self, gt_path: Path, pred_path: Path):
        self.fid = gt_path.stem
        self.gt_structuring_data = self._load_gt(gt_path)
        self.pred_exists = pred_path is not None

        self.pred_structuring_prob_data = {}
        self.pred_preprocess_result, self.pred_structuring_data, self.pred_meta_result = self._load_pred(pred_path)

        self.item_results: Dict[str, bool] = {}

        self._load_summary_charges_total()

    def is_all_hit(self) -> bool:
        """
        一个 testee 的所有字段结果是否全对
        """
        return all(self.item_results.values())

    def _load_pred(self, pred_path: Path) -> (Dict, Dict, Dict):
        """
        读取结构化输出文件
        """
        with open(str(pred_path), 'r', encoding='utf-8') as f:
            content = json.load(f)

        if 'subjects' in content:
            # AI output format detected
            if len(content['subjects']) == 0:
                raise AssertionError('INSUFFICIENT_SUBJECTS')
            subject = content['subjects'][0]  # select first subject if multiple are detected
            if not subject['structuring']['enabled']:
                raise AssertionError('STRUCTURING_NOT_ENABLED')
            if not subject['structuring']['success']:
                raise AssertionError(f'STRUCTURING_FAILED since {subject["structuring"]["message"]}')
            # TODO: preprocess result not extracted
            return (
                {}, self._process_structuring_data(subject['structuring']['data'] or {}), subject['structuring']['meta']
            )
        elif 'rawImage' in content and 'rawBBoxes' in content:
            # debug_server 输出的结构化结果
            pred = content["pred"]
            self.pred_structuring_prob_data = content["predProbability"]
            return {}, pred, None
        else:
            # structuring output format detected
            preprocess_result = content.get('preprocess_result', {})
            meta_result = content.get('structuring_meta')
            if meta_result:
                meta_result = meta_result[0]

            structuring_data = self._process_structuring_data(content.get('structuring_data') or {})

            return preprocess_result, structuring_data, meta_result

    def _load_gt(self, gt_path: Path) -> Dict:
        with open(str(gt_path), 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self._process_structuring_data(data.get('structuring_data') or {})

    def _get_item_value_gt_or_pred(self, names: List[str] or str):
        if isinstance(names, str):
            names = [names]

        for name in names:
            val = self.gt_structuring_data.get(name)
            if isinstance(val, str):
                try:
                    val = round(float(val), 2)

                # receiptmoney 可能未标注
                except ValueError:
                    val = self.pred_structuring_data.get(name)
                    try:
                        val = round(float(val), 2)
                    except (ValueError, TypeError):
                        val = 0

            if val is not None:
                return val

    @staticmethod
    def _process_structuring_data(structuring_data):
        out = {}

        if isinstance(structuring_data, List):
            structuring_data = structuring_data[0]

        for item_name, val in structuring_data.items():
            # TODO : SKIP OBJECT IS FOR CAIBAO RUN RUNSTRUCTURE
            if item_name == 'object':
                continue
            if isinstance(val, Dict):
                # TODO: make run_structure() output format is exactly with ocr-structuring output format
                if isinstance(val['content'], List):
                    # table detected
                    out[item_name] = [format_raw_table_record(record) for record in val['content']]
                else:
                    # normal-field
                    out[item_name] = val['content']
            elif isinstance(val, List):
                # 针对表格类数据处理
                if len(val) != 0 and isinstance(val[0], Dict):
                    out[item_name] = [format_raw_table_record(record) for record in val]
                else:
                    # 对于没有表头的票据，例如财报，这里 val 是一个二维数组
                    out[item_name] = val
            elif isinstance(val, str):
                out[item_name] = val
        return out

    def _load_summary_charges_total(self):
        # 医疗发票中，大体收费项目的总和(summary_total_money)应该等于 receiptmoney/amountwords
        # 读取 receiptmoney/amountwords 的值作为 summary_total_money 的 gt
        summary_total_money_gt = self._get_item_value_gt_or_pred(['receiptmoney', 'amountinwords'])
        if summary_total_money_gt is not None:
            self.gt_structuring_data[SUMMARY_TOTAL_MONEY] = summary_total_money_gt

        # 求 summary_charges 的总和
        summary_charges = self.pred_structuring_data.get('summary_charges')
        if summary_charges is not None:
            pred_summary_total_money = sum([float(item['charge']) for item in summary_charges])
            pred_summary_total_money = round(pred_summary_total_money, 2)
            self.pred_structuring_data[SUMMARY_TOTAL_MONEY] = pred_summary_total_money

    def print_summary_charges_total_money_info(self):
        if SUMMARY_TOTAL_MONEY not in self.item_results:
            return

        if 'summary_charges' not in self.pred_structuring_data or 'summary_charges' not in self.gt_structuring_data:
            return

        # 记录测试结果用于观察
        if not self.item_results.get(SUMMARY_TOTAL_MONEY):
            logger.debug(f"{'-' * 5} {self.fid} {'-' * 5}")
            pred_summary_charges = {pred['name']: pred['charge'] for pred in
                                    self.pred_structuring_data['summary_charges']}
            gt_summary_charges = self.gt_structuring_data.get('summary_charges')
            if gt_summary_charges is not None:
                for gt in gt_summary_charges:
                    gt_charge = gt['charge']
                    pred_charge = pred_summary_charges.get(gt['name'])
                    try:
                        gt_charge = float(gt_charge)
                    except ValueError:
                        gt_charge = 0

                    try:
                        pred_charge = float(pred_charge)
                    except (ValueError, TypeError):
                        pred_charge = 0

                    if pred_charge != gt_charge:
                        logger.debug(
                            f'name: {gt["name"]} gt: {gt["charge"]} pred {pred_summary_charges.get(gt["name"])}')
            else:
                logger.debug(pred_summary_charges)
            logger.debug(f"{self.gt_structuring_data[SUMMARY_TOTAL_MONEY]} "
                         f"{self.pred_structuring_data[SUMMARY_TOTAL_MONEY]}")
            logger.debug('-' * 20 + '\n')


def format_raw_table_record(record):
    # record can have multiple structure:
    #   1. simple K-V pair: {'name': 'xxx'}
    #   2. normal-field: {'name': {'content': 'xxx', 'probability': 1.0}}

    # 财报这种没有表头的数据，输出的是二维数组，进到这里的 record 是一个数组
    if isinstance(record, list):
        return record

    result = {}
    for k, v in record.items():
        if isinstance(v, str) or isinstance(v, float) or isinstance(v, int):
            result[k] = v
        elif isinstance(v, float):
            result[k] = str(v)
        else:
            result[k] = v['content']
    return result
