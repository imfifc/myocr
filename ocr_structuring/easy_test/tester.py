import copy
import json
from collections import defaultdict

import editdistance
from tqdm import tqdm

from .compare_funcs import item_compare_funcs
from typing import Dict, List, Tuple
from .table_item import TableItem
from tabulate import tabulate
from .testee import Testee
from .utils import logger
from pathlib import Path
from .item import Item
from .const import SUMMARY_TOTAL_MONEY
import numpy as np

GT_SUFFIX = ".json"
PRED_SUFFIX = ".json"


class Tester:
    def __init__(
        self,
        gt_dir: Path,
        pred_dir: Path,
        output_dir: Path,
        table_compare_method,
        table_compare_unique_key,
        table_compare_values,
        ignore_items,
        compare_item_group_path,
        thresh_search=False,
    ):
        self.gt_dir = gt_dir
        self.output_dir = output_dir
        self.pred_dir = pred_dir
        self.ignore_items = ignore_items
        self.thresh_search = thresh_search

        if compare_item_group_path is None:
            self.compare_items = []
        else:
            with open(compare_item_group_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.compare_items = [_.strip() for _ in lines]
            self.compare_items_group_name = Path(compare_item_group_path).stem

        self.testee_dict = self._load_testee_dict(gt_dir, pred_dir)
        self.items, self.table_items = self._create_items(self.testee_dict)

        self.table_compare_method = table_compare_method
        self.table_compare_unique_key = table_compare_unique_key
        self.table_compare_values = table_compare_values

    def run(self):
        for testee in self.testee_dict.values():
            for item in self.items:

                # 如果某一个字段 gt 中不存在，则跳过统计
                if item.name not in testee.gt_structuring_data:
                    continue

                correct = item.compare(
                    testee.gt_structuring_data[item.name],
                    # 如果一个字段在 pred 中不存在，而在 gt 中存在，则应该认为统计错误
                    testee.pred_structuring_data.get(
                        item.name, Item.PRED_VALUE_NOT_EXIST
                    ),
                    testee.fid,
                )

                testee.item_results[item.name] = correct

            for table_item in self.table_items:
                if table_item.name not in testee.gt_structuring_data:
                    continue
                self._table_compare(table_item, testee)

            testee.print_summary_charges_total_money_info()

        self.write_result(self.items)

        if self.compare_items:
            _items = [_ for _ in self.items if _.name in self.compare_items]
            self.write_result(_items, name=self.compare_items_group_name)

        self.write_table_result()
        self.write_wrong_file(self.items)

    def run_thresh_search(self, start_thresh=0.8, step=0.0001):
        """
        根据 testee 中的 structuring_prob_data 进行阈值搜索
        Args:
            start_thresh:
            step:

        Returns:

        """
        logger.info("searching threshold...")
        items_out = []
        for item in self.items:
            if not item.has_gt():
                logger.warning("item not exist in gt: {}".format(item.name))
                continue
            items_out.append(item)
        items_out.sort(key=lambda x: x.name)

        threshes = np.arange(start_thresh, 1.0, step)
        np.insert(threshes, 0, 0)
        thresh_search_result = self._thresh_search(
            copy.deepcopy(self.items), threshes, True
        )

        target_keep_acc_list = [0.7, 0.8, 0.9, 0.95]
        target_acc_search_result = self._find_thresh_for_target_acc(
            thresh_search_result, target_keep_acc_list
        )

        table_headers = ["", "Total", "keep/keep acc"]
        for it in target_keep_acc_list:
            table_headers.append(f"keep/keep acc({int(it*100):d})")

        items = {it.name: it for it in self.items}
        table_rows = []
        item_names = list(target_acc_search_result.keys())
        item_names.sort()
        for item_name in item_names:
            if item_name not in items:
                continue

            # (target_keep_acc, thresh, item)
            item_target_search_result = target_acc_search_result[item_name]
            row = [
                item_name,
                items[item_name].cnt_gt,
                f"{items[item_name].keep:.1f}/{items[item_name].keep_acc:.1f}",
            ]
            for it_keep_acc in target_keep_acc_list:
                added = False
                for val in item_target_search_result:
                    target_keep_acc, thresh, item = val
                    if target_keep_acc == it_keep_acc:
                        row.append(f"{item.keep*100:.1f}/{item.keep_acc * 100:.1f}")
                        added = True
                        break
                if not added:
                    row.append("N/A")
            table_rows.append(row)

        table = tabulate(
            table_rows,
            headers=table_headers,
            showindex="always",
            numalign="right",
            stralign="right",
        )
        print(table)

        # 每个字段 keep/keep acc 的平均
        field_avg_keep, field_avg_keep_acc = self._cal_overall_keep_and_keepacc(
            thresh_search_result
        )

        # 每个字段 keep/keep acc 的平均
        average_keep, average_keep_acc = self._cal_keep_and_keepacc(
            thresh_search_result
        )

        # print("\nAverage item keep: %.2f" % field_avg_keep)
        # print("Average item keep acc: %.2f" % field_avg_keep_acc)
        print("Average keep: %.2f" % average_keep)
        print("Average keep acc: %.2f" % average_keep_acc)
        search_result_path = self.output_dir / "thresh_search_result.txt"
        with open(search_result_path, mode="w", encoding="utf-8") as f:
            f.write(table)
            # f.write("\nAverage thresh search keep: %.2f\n" % field_avg_keep)
            # f.write("Average thresh search keep acc: %.2f\n" % field_avg_keep_acc)
            f.write("Average keep: %.2f\n" % average_keep)
            f.write("Average keep acc: %.2f\n" % average_keep_acc)

    def _thresh_search(
        self,
        items: List[Item],
        threshes: List[float],
        consider_zero_as_one: bool = False,
    ):
        """

        Args:
            threshes:
            consider_zero_as_one:

        Returns:

        """
        items_thresh_result = defaultdict(list)

        valid_item_names = set()

        for thresh in tqdm(threshes):
            for it in items:
                it.clear()

            for _, testee in self.testee_dict.items():
                for item in items:
                    if (
                        item.name not in testee.gt_structuring_data
                        or item.name not in testee.pred_structuring_data
                        or item.name not in testee.pred_structuring_prob_data
                    ):
                        continue

                    valid_item_names.add(item.name)
                    pred_prob = testee.pred_structuring_prob_data[item.name]
                    if consider_zero_as_one:
                        if pred_prob == 0:
                            pred_prob = 1
                    skip = True if pred_prob < thresh else False
                    item.compare(
                        testee.gt_structuring_data[item.name],
                        # 如果一个字段在 pred 中不存在，而在 gt 中存在，则应该认为统计错误
                        testee.pred_structuring_data.get(
                            item.name, Item.PRED_VALUE_NOT_EXIST
                        ),
                        testee.fid,
                        skip=skip,
                    )

            for item in items:
                if item.name not in valid_item_names:
                    continue

                items_thresh_result[item.name].append((thresh, copy.deepcopy(item)))

        return items_thresh_result

    def _cal_keep_and_keepacc(self, thresh_search_result):
        """
        不同阈值的结果按照 F-Score 排序，取 F-Score 最大时的 keep_acc 和 keep 求平均
        Args:
            thresh_search_result:
                key: item_name
                value: [(thresh, item)]
        Returns:
            average_keep, average_keep_acc
        """
        cnt_gt = 0
        cnt_pred_pass = 0
        cnt_pred_pass_hit = 0

        for item_name, val in thresh_search_result.items():
            val.sort(key=lambda x: x[1].keep_acc, reverse=True)

            min_keep = 0.6

            # 如果能找到 keep > 0.6 的，则取对应的保留率
            find_good = False
            for thresh, item in val:
                if item.keep >= min_keep:
                    find_good = True
                    cnt_gt += item.cnt_gt
                    cnt_pred_pass += item.cnt_pred_pass
                    cnt_pred_pass_hit += item.cnt_pred_pass_hit
                    break

            if find_good:
                continue

            # 如果没能找到满足要求的结果，则取 f-score 最高的结果
            val.sort(key=lambda x: x[1].fscore, reverse=True)
            cnt_gt += val[0][1].cnt_gt
            cnt_pred_pass += val[0][1].cnt_pred_pass
            cnt_pred_pass_hit += val[0][1].cnt_pred_pass_hit

        keep = cnt_pred_pass / cnt_gt if cnt_gt != 0 else 0
        keep_acc = cnt_pred_pass_hit / cnt_pred_pass if cnt_pred_pass != 0 else 0
        return keep, keep_acc

    def _cal_overall_keep_and_keepacc(self, thresh_search_result):
        """
        不同阈值的结果按照 F-Score 排序，取 F-Score 最大时的 keep_acc 和 keep 求平均
        Args:
            thresh_search_result:
                key: item_name
                value: [(thresh, item)]
        Returns:
            average_keep, average_keep_acc
        """
        total_keep = []
        total_keep_acc = []
        for item_name, val in thresh_search_result.items():
            val.sort(key=lambda x: x[1].keep_acc, reverse=True)

            min_keep = 0.6

            # 如果能找到 keep > 0.6 的，则取对应的保留率
            find_good = False
            for thresh, item in val:
                if item.keep >= min_keep:
                    find_good = True
                    total_keep.append(item.keep)
                    total_keep_acc.append(item.keep_acc)
                    break

            if find_good:
                continue

            # 如果没能找到满足要求的结果，则取 f-score 最高的结果
            val.sort(key=lambda x: x[1].fscore, reverse=True)
            total_keep.append(val[0][1].keep)
            total_keep_acc.append(val[0][1].keep_acc)

        if len(total_keep) == 0 or len(total_keep_acc) == 0:
            return 0, 0

        return (
            sum(total_keep) / len(total_keep),
            sum(total_keep_acc) / len(total_keep_acc),
        )

    def _find_thresh_for_target_acc(self, thresh_search_result, keep_acc_list):
        """
        不同阈值的结果按照 F-Score 排序，取第一个 keep_acc 大于 target_keep_acc 的值
        Args:
            thresh_search_result:
                key: item_name
                value: [(thresh, item)]
            keep_acc_list:

        Returns:
            dict
                key: item_name
                value: (target_keep_acc, thresh, item)
        """
        target_acc_search_result = {}
        for item_name, thresh_results in thresh_search_result.items():
            item_target_search_result = []
            thresh_results.sort(key=lambda x: x[1].fscore, reverse=True)

            for target_keep_acc in keep_acc_list:
                for thresh, item in thresh_results:
                    if item.keep_acc > target_keep_acc:
                        item_target_search_result.append(
                            [target_keep_acc, thresh, item]
                        )
                        break

            target_acc_search_result[item_name] = item_target_search_result
        return target_acc_search_result

    def _table_compare(self, table_item, testee):
        if self.table_compare_method == "by_row":
            table_item.compare_by_row(
                testee.gt_structuring_data[table_item.name],
                testee.pred_structuring_data.get(table_item.name, None),
                testee.fid,
            )

        if self.table_compare_method == "by_key":
            table_item.compare_by_special_key(
                testee.gt_structuring_data[table_item.name],
                testee.pred_structuring_data.get(table_item.name, None),
                testee.fid,
                unique_key=self.table_compare_unique_key,
                value_key=self.table_compare_values,
            )

        if self.table_compare_method == "by_row_headless":
            table_item.compare_by_row_headless(
                testee.gt_structuring_data[table_item.name],
                testee.pred_structuring_data.get(table_item.name, None),
                testee.fid,
            )

    @staticmethod
    def _load_testee_dict(gt_dir: Path, pred_dir: Path) -> Dict:
        """
        加载 gt 和预测结果，该函数假设 gt_dir 的文件和 pred 文件一致
        :return:
        """
        logger.info("loading testee...")
        testee_dict = {}
        for gt_path in gt_dir.iterdir():

            if not gt_path.name.endswith(GT_SUFFIX):
                continue
            pred_path = pred_dir / gt_path.with_suffix(PRED_SUFFIX).name
            if not pred_path.exists():
                pred_path_txt = pred_dir / gt_path.with_suffix(".txt").name
                if not pred_path_txt.exists():
                    logger.warn(f"pred_path not exist: {pred_path}")
                    continue
                else:
                    pred_path = pred_path_txt
            try:
                testee = Testee(gt_path, pred_path)
                testee_dict[gt_path.stem] = testee
            except Exception:
                logger.exception(f"Load testee error")

        logger.info(f"{len(testee_dict)} testee loaded")

        return testee_dict

    def _create_items(
        self, testee_dict: Dict[str, Testee]
    ) -> Tuple[List[Item], List[TableItem]]:
        """
        取 gt 和 pred 公共的字段作为进行统计的字段
        :param testee_dict:
        :return:
        """
        table_item_names = set()
        item_names = set()
        for testee in testee_dict.values():
            for item_name, it in testee.gt_structuring_data.items():
                if isinstance(it, str):
                    # Key value 形式的数据
                    item_names.update([item_name])
                elif isinstance(it, List):
                    # 表格形式的数据
                    table_item_names.update([item_name])

            for item_name, it in testee.pred_structuring_data.items():
                if isinstance(it, str):
                    # Key value 形式的数据
                    item_names.update([item_name])
                elif isinstance(it, List):
                    # 表格形式的数据
                    table_item_names.update([item_name])

        item_names = sorted(
            list(filter(lambda x: x not in self.ignore_items, item_names))
        )
        table_item_names = sorted(list(table_item_names))

        items = [Item(it, item_compare_funcs.get(it)) for it in item_names]
        table_items = [TableItem(it) for it in table_item_names]

        # 加入大体收费项之和字段，用于和 receiptmoney(amountinwords) 比较
        if SUMMARY_TOTAL_MONEY not in self.ignore_items:
            summary_total_money = Item(
                SUMMARY_TOTAL_MONEY, item_compare_funcs.get("amountinwords")
            )
            items.append(summary_total_money)

        return items, table_items

    def write_table_result(self):
        for table_item in self.table_items:
            if table_item.empty():
                continue
            print(f"\nTable name: {table_item.name}")
            self.write_result(table_item.items, name="table_" + table_item.name)
            self.write_wrong_file(table_item.items, extra=table_item.name)
            self.write_result(
                table_item.headless_table_items.values(),
                name="headless_table_" + table_item.name,
            )

    def write_result(self, items: List[Item], name="easytest"):
        if len(list(items)) == 0:
            return

        eng_table_headers = [
            "Name",
            "Total GT",
            "Valid GT",
            "Total Pred",
            "Pass",
            "Correct",
            "Pass Err",
            "Err",
            "Keep",
            "Keep Acc",
            "Acc",
            "FS",
            "Keep Acc(v)",
            "Acc(v)",
        ]

        tabulate_data = []
        for item in items:
            if not item.has_gt():
                logger.warning(f"item not exist in gt: {item.name}")
                continue
            if not item.has_pred():
                logger.warning(f"item not exist in pred: {item.name}")
                continue

        items = list(filter(lambda it: it.has_gt() and it.has_pred(), items))
        for item in items:
            tabulate_data.append(
                [
                    item.name,
                    item.cnt_gt,
                    item.valid_gt,
                    item.cnt_pred,
                    item.cnt_pred_pass,
                    item.cnt_pred_pass_hit,
                    item.cnt_pred_pass_err,
                    item.cnt_pred_err,
                    item.keep * 100,
                    item.keep_acc * 100,
                    item.acc * 100,
                    item.fscore * 100,
                    item.valid_keep_acc * 100,
                    item.valid_acc * 100,
                ]
            )

        tabulate_data = sorted(tabulate_data, key=lambda x: x[0])

        table = tabulate(
            tabulate_data,
            headers=eng_table_headers,
            showindex="always",
            numalign="right",
            stralign="right",
            floatfmt=".2f",
        )
        print(table)

        avg_item_keep = self.cal_avg_val(items, "keep")
        avg_item_keep_acc = self.cal_avg_val(items, "keep_acc")
        avg_item_acc = self.cal_avg_val(items, "acc")
        avg_item_fscore = self.cal_avg_val(items, "fscore")
        avg_item_valid_keep_acc = self.cal_avg_val(items, "valid_keep_acc")
        avg_item_valid_acc = self.cal_avg_val(items, "valid_acc")

        avg_string_format = lambda k, v: f"Average {k}: {v:.2f}%"
        print_strs = [
            avg_string_format("item keep", avg_item_keep),
            avg_string_format("item keep acc", avg_item_keep_acc),
            avg_string_format("item acc", avg_item_acc),
            avg_string_format("item fscore", avg_item_fscore),
            avg_string_format("item valid keep acc", avg_item_valid_keep_acc),
            avg_string_format("item valid item acc", avg_item_valid_acc),
        ]

        all_hit_rate = len(
            list(filter(lambda x: x.is_all_hit(), self.testee_dict.values()))
        ) / len(self.testee_dict)
        print_strs.append(f"Item all correct acc: {all_hit_rate * 100:.2f}%")

        dummy_item = self.merge_items(items)
        print_strs.extend(
            [
                avg_string_format("keep", dummy_item.keep * 100)
                + f"({dummy_item.cnt_pred_pass}/{dummy_item.cnt_gt})",
                avg_string_format("keep acc", dummy_item.keep_acc * 100)
                + f"({dummy_item.cnt_pred_pass_hit}/{dummy_item.cnt_pred_pass})",
                avg_string_format("acc", dummy_item.acc * 100)
                + f"({dummy_item.cnt_pred_pass_hit}/{dummy_item.cnt_gt})",
                avg_string_format("valid acc", dummy_item.valid_acc * 100)
                + f"({dummy_item.cnt_pred_pass_hit}/{dummy_item.cnt_gt - dummy_item.cnt_invalid_gt})",
            ]
        )

        result_file_path = self.output_dir / (name + ".txt")
        with open(str(result_file_path), mode="w", encoding="utf-8") as fw:
            fw.write(table)
            fw.write("\n")
            for it in print_strs:
                fw.write(f"{it}\n")
                print(it)

        # 保存统计结果的 json 文件，方便结构化读取
        json_save_path = self.output_dir / (name + ".json")
        data = {"result": {}, "items_result": {}}
        for item in items:
            data["items_result"][item.name] = dict(
                cnt_gt=item.cnt_gt,
                cnt_pred=item.cnt_pred,
                cnt_pred_pass=item.cnt_pred_pass,
                cnt_pred_pass_hit=item.cnt_pred_pass_hit,
                cnt_pred_err=item.cnt_pred_err,
                cnt_pred_pass_err=item.cnt_pred_pass_err,
                cnt_invalid_gt=item.cnt_invalid_gt,
                cnt_pass_invalid_gt=item.cnt_pass_invalid_gt,
            )

        data["result"] = {
            "avg_item_keep": avg_item_keep,
            "avg_item_keep_acc": avg_item_keep_acc,
            "avg_item_acc": avg_item_acc,
            "avg_item_fscore": avg_item_fscore,
            "avg_item_valid_keep_acc": avg_item_valid_keep_acc,
            "avg_item_valid_acc": avg_item_valid_acc,
        }

        with open(str(json_save_path), mode="w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def cal_avg_val(items: List[Item], key_name: str):
        """
        :param items:
        :param key_name:  item_out 中的索引
        :return:
        """
        avg_acc = [result.__getattribute__(key_name) for result in items]
        val = sum(avg_acc) / float(len(avg_acc)) if len(avg_acc) != 0 else 0
        return val * 100

    @staticmethod
    def merge_items(items):
        dummy = Item("dummy")
        for item in items:
            dummy.cnt_gt += item.cnt_gt
            dummy.cnt_pred += item.cnt_pred
            dummy.cnt_pred_pass += item.cnt_pred_pass
            dummy.cnt_pred_pass_hit += item.cnt_pred_pass_hit
            dummy.cnt_pred_err += item.cnt_pred_err
            dummy.cnt_pred_pass_err += item.cnt_pred_pass_err
            dummy.cnt_invalid_gt += item.cnt_invalid_gt
            dummy.cnt_pass_invalid_gt += item.cnt_pass_invalid_gt
        return dummy

    def write_wrong_file(self, items, extra=""):
        # extra 对应额外的需要在标题中体现的信息
        for item in items:
            result = []
            for it in item.wrong_items:
                try:
                    ed = editdistance.eval(str(it.gt), str(it.pred))
                except Exception:
                    ed = 0

                result.append({"fid": it.fid, "gt": it.gt, "pr": it.pred, "ed": ed})

            p = self.output_dir / f"wrong_{extra}{item.name}.json"
            with open(str(p), "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
