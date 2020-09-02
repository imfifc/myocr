"""
不同字段特殊的比较逻辑
"""
from ocr_structuring.core.utils.amount_in_words import cn_amount_util


def date_compare(gt: str, pred: str) -> bool:
    if not gt or not pred:
        return False

    gt = gt.replace('年', '-').replace('月', '-').replace('日', '')
    gt = "-".join([x.zfill(2) for x in gt.split("-", 2)])

    pred = pred.replace('年', '-').replace('月', '-').replace('日', '')
    pred = "-".join([x.zfill(2) for x in pred.split("-", 2)])

    return pred == gt


def city_compare_func(gt: str, pred: str) -> bool:
    if not gt or not pred:
        return False

    return pred in gt


def amountinwords_compare_func(gt, pred) -> bool:
    if not gt or not pred:
        return False

    _gt = gt
    if gt is not None and isinstance(gt, str):
        try:
            _gt = float(gt)
        except:
            _gt = cn_amount_util.word2num(gt)

        if _gt:
            _gt = float(_gt)

    try:
        _pred = float(pred)
    except:
        _pred = pred
        pass

    return _gt == _pred


def contains_compare(gt, pred) -> bool:
    if not gt or not pred:
        return False

    return str(gt) in str(pred)


item_compare_funcs = {
    'date': date_compare,
    'city': city_compare_func,
    'amountinwords': amountinwords_compare_func,
}
