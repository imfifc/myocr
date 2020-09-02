import re
from typing import Dict, List, Callable

from ocr_structuring.easy_test.compare_funcs import item_compare_funcs
from .item import Item
import editdistance


class TableItem:
    def __init__(self, name: str):
        self.name = name
        self._items = {}

        self.headless_table_item = None
        self.headless_table_items = {}

    def compare_by_row_headless(
        self, gt_table: List[List[str]], pred_table: List[List[str]], fid
    ):
        """
        比较没有表头的表格，例如 财报
        这里的比较使用最严格的模式，如果错行了，那从错行那行以下的算全错
        """
        if self.headless_table_item is None:
            self.headless_table_item = Item("headless_table")
            self._items["headless_table"] = self.headless_table_item

        self.headless_table_items[fid] = Item(fid)

        for i, gt_row in enumerate(gt_table):
            for j, gt in enumerate(gt_row):
                if i <= len(pred_table) - 1:
                    pred_row = pred_table[i]

                    if j > len(pred_row) - 1:
                        pred = Item.PRED_VALUE_NOT_EXIST
                    else:
                        pred = pred_row[j]
                else:
                    # gt 的行比 pred 多，认为对应位置的 pred 是错的
                    pred = Item.PRED_VALUE_NOT_EXIST

                if isinstance(gt, str):
                    gt = gt.strip()
                    gt = re.sub("[,， ]", "", gt)
                if isinstance(pred, str):
                    pred = pred.strip()
                    pred = re.sub("[,， ]", "", pred)
                self.headless_table_item.compare(gt, pred, fid)
                self.headless_table_items[fid].compare(gt, pred, fid)

    def compare_by_row(
        self, gt_table: List[Dict[str, str]], pred_table: List[Dict[str, str]], fid
    ):
        """
        按行比较 ground truth 和 prediction
        - 如果 gt 的行比 prediction 多，则会认为是错误的
        - TODO 如果 prediction 的行比 gt 多，目前没有做处理
        """
        self._add_item(gt_table)

        for i, row in enumerate(gt_table):
            for item_name, gt in row.items():
                if i <= len(pred_table) - 1:
                    pred = pred_table[i].get(item_name, Item.PRED_VALUE_NOT_EXIST)
                else:
                    # gt 的行比 pred 多，认为对应位置的 gt 是错的
                    pred = Item.PRED_VALUE_NOT_EXIST

                self._items[item_name].compare(gt, pred, fid)

    def compare_by_special_key(
        self,
        gt_table: List[Dict[str, str]],
        pred_table: List[Dict[str, str]],
        fid,
        unique_key="name",
        value_key: List[str] = None,
    ):
        """
        默认 unique_key 的值在 table 中只出现一次，如果出现多次，TODO 目前是使用第一次出现的
        :param unique_key: 通过 unique_key 来确认 gt 和 pred 的行对应关系
        :param value_key: if not None，表格只输出某些字段的统计结果
        :return:
        """
        self._add_item(gt_table)

        if pred_table is None:
            pred_table = []
        if gt_table is None:
            gt_table = []

        # 文本替换列表
        for gt_row in gt_table:
            # 忽略没有 unique_key 的 gt
            if unique_key not in gt_row:
                continue

            # 每行都会有一个key值，根据key值去predict中找对应key的内容的value
            find_match = False
            for pred_row in pred_table:
                gt_unique_value = gt_row[unique_key]
                pred_unique_value = pred_row[unique_key]

                preprocessed_gt_unique_value = self._unique_key_value_preprocess(
                    unique_key, gt_unique_value
                )

                gt = gt_unique_value
                pred = pred_unique_value
                unique_key_match = False
                if gt_unique_value == pred_unique_value:
                    unique_key_match = True
                elif self._is_unique_key_value_equal(
                    unique_key, preprocessed_gt_unique_value, pred_unique_value
                ):
                    unique_key_match = True
                    gt = preprocessed_gt_unique_value
                    pred = gt

                if unique_key_match:
                    find_match = True
                    self._items[unique_key].compare(gt, pred, fid)

                    if value_key is None:
                        for key in gt_row:
                            if key != unique_key:
                                # 拿到所有的其余的key
                                self._items[key].compare(
                                    gt_row[key], pred_row.get(key), fid
                                )
                    else:
                        for key in value_key:
                            if key != unique_key and key in self._items.keys():
                                self._items[key].compare(
                                    gt_row[key], pred_row.get(key), fid
                                )
                    # 默认一个key值在pred中只出现一次，出现两次，则默认使用第一次出现进行比较
                    break

            if not find_match:
                for key in gt_row:
                    # 只统计 unique_key 和 value_key 中列举的字段
                    if key != unique_key and (
                        value_key is not None and key not in value_key
                    ):
                        continue

                    v = gt_row[key]
                    if not v:
                        v = "&&"
                    self._items[key].compare(v, None, fid)

    def _is_unique_key_value_equal(self, key, gt, pred) -> bool:
        """
        判断 gt 和 pred 中 unique_key 对应的值是否一样
        :param key: unique_key
        :param gt: gt unique_key 对应的值
        :param pred: pred unique_key 对应的值
        :return:
        """
        if self.name == "detail_charges" and key == "name":
            # detail charges 容许一定的偏差
            return editdistance.eval(gt, pred) <= 2
        else:
            return gt == pred

    def _unique_key_value_preprocess(self, key, gt):
        if self.name == "detail_charges" and key == "name":
            return self._detail_charges_name_preprocess(gt)
        return gt

    def _detail_charges_name_preprocess(self, gt):
        if not gt:
            return gt

        if gt in Item.INVALID_ITEM_VALUES:
            return gt

        res = gt
        modify = {"（": "(", "）": ")", "_": ""}
        for k, v in modify.items():
            res = res.replace(k, v)
        res = res.replace("中药饮片及药材", "")
        regx = re.compile("(/[^\u4e00-\u9fa5]*[^/]*)|(\(.*)")
        res = regx.sub("", res)
        regx = re.compile("[^\u4e00-\u9fa5]")
        res = regx.sub("", res)
        return res

    @property
    def items(self):
        return self._items.values()

    def empty(self) -> bool:
        return not any([x.cnt_gt > 0 for x in self.items])

    def _add_item(self, gt_table: List[Dict[str, str]]):
        for row in gt_table:
            for item_name in row:
                if item_name not in self._items:
                    self._items[item_name] = Item(
                        item_name, compare_func=item_compare_funcs.get(item_name)
                    )
