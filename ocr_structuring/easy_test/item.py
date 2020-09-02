from collections import namedtuple

from typing import Callable

WrongItem = namedtuple('WrongItem', 'fid gt pred')


class Item:
    INVALID_ITEM_VALUES = ['&1', '&2', '&3', '&4', '&5', '&&', '-']
    EMPTY_VALUE_TO_KEEP = 'const_value_for_val_keep'
    PRED_VALUE_NOT_EXIST = 'const_value_not_exist'

    def __init__(self, name: str, compare_func: Callable = None):
        self.name = name

        self.cnt_gt = 0  # gt 中这个 item 的总数
        self.cnt_pred = 0  # pred 中这个 item 的总数
        self.cnt_pred_pass = 0  # 通过的数量
        self.cnt_pred_pass_hit = 0  # 通过并且正确的数量
        self.cnt_pred_err = 0  # 错误的预测结果数量
        self.cnt_pred_pass_err = 0  # 通过但是不正确的数量
        self.cnt_invalid_gt = 0  # gt 里面无效的数量
        self.cnt_pass_invalid_gt = 0  # pred 通过时，gt 无效的数量

        self.wrong_items = []
        self.compare_func = compare_func

    def clear(self):
        self.cnt_gt = 0  # gt 中这个 item 的总数
        self.cnt_pred = 0  # pred 中这个 item 的总数
        self.cnt_pred_pass = 0  # 通过的数量
        self.cnt_pred_pass_hit = 0  # 通过并且正确的数量
        self.cnt_pred_err = 0  # 错误的预测结果数量
        self.cnt_pred_pass_err = 0  # 通过但是不正确的数量
        self.cnt_invalid_gt = 0  # gt 里面无效的数量
        self.cnt_pass_invalid_gt = 0  # pred 通过时，gt 无效的数量
        self.wrong_items = []

    def has_gt(self) -> bool:
        return self.cnt_gt != 0

    def has_pred(self) -> bool:
        return self.cnt_pred != 0

    def compare(self, gt, pred, fid, keep_consider_empty=True, skip=False) -> bool:
        """

        :param gt:
        :param pred:
        :param fid:
        :param keep_consider_empty: If true，在计算保留率时会将 pred 的空值与 gt 比较，如果两者都为空，那这个结果是保留的
        :param skip: If True，直接不保留 pred 结果
        :return:
        """
        # 统一输入的空值
        if gt in ['', None]:
            gt = None
        if pred in ['', None]:
            pred = None

        if gt is not None and isinstance(gt, str) and gt[-2:] in self.INVALID_ITEM_VALUES:
            gt = gt[-2:]

        if keep_consider_empty and not gt and not pred:
            pred = self.EMPTY_VALUE_TO_KEEP

        self.cnt_gt += 1
        if gt in self.INVALID_ITEM_VALUES:
            self.cnt_invalid_gt += 1

        if pred != self.PRED_VALUE_NOT_EXIST:
            self.cnt_pred += 1

        if skip:
            return False

        hit = False
        if pred is None or pred == self.PRED_VALUE_NOT_EXIST:
            self.wrong_items.append(WrongItem(fid=fid, gt=gt, pred=pred))
        else:
            self.cnt_pred_pass += 1
            if gt in self.INVALID_ITEM_VALUES:
                self.cnt_pass_invalid_gt += 1
            else:
                # 如果 gt 是无效的，应该直接跳过 gt 和 pred 比较的逻辑，认为是错的
                if self.compare_func:
                    hit = self.compare_func(gt, pred)
                else:
                    if gt == pred:
                        hit = True

                    if pred == self.EMPTY_VALUE_TO_KEEP:
                        hit = True

                    try:
                        if float(gt) == float(pred):
                            hit = True
                    except:
                        pass

            if hit:
                self.cnt_pred_pass_hit += 1
            else:
                self.cnt_pred_pass_err += 1
                self.wrong_items.append(WrongItem(fid=fid, gt=gt, pred=pred))

        if not hit:
            self.cnt_pred_err += 1

        return hit

    @property
    def acc(self):
        return self.cnt_pred_pass_hit / self.cnt_gt if self.cnt_gt != 0 else 0

    @property
    def keep(self):
        return self.cnt_pred_pass / self.cnt_gt if self.cnt_gt != 0 else 0

    @property
    def keep_acc(self):
        return self.cnt_pred_pass_hit / self.cnt_pred_pass if self.cnt_pred_pass != 0 else 0

    @property
    def fscore(self):
        return self.cal_f_score(self.keep, self.acc)

    @property
    def valid_acc(self):
        valid_gt = self.cnt_gt - self.cnt_invalid_gt
        valid_pred_pass_hit = self.cnt_pred_pass_hit
        return valid_pred_pass_hit / valid_gt if valid_gt != 0 else 0

    @property
    def valid_keep_acc(self):
        valid_pass_count = self.cnt_pred_pass - self.cnt_pass_invalid_gt
        valid_pred_pass_hit = self.cnt_pred_pass_hit
        return valid_pred_pass_hit / valid_pass_count if valid_pass_count != 0 else 0

    @property
    def valid_gt(self):
        return self.cnt_gt - self.cnt_invalid_gt

    def cal_f_score(self, keep, acc):
        if (keep + acc) == 0:
            return 0
        return 2 * keep * acc / (keep + acc)
