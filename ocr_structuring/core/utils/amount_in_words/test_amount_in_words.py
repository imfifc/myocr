import json
import os
from unittest import TestCase

from ocr_structuring.core.utils.amount_in_words.amount_in_words import AmountUtils


def get_data_file_path(filename):
    CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(CURRENT_DIR, filename)


class TestAmountInWords(TestCase):
    def test_amount_in_words(self):
        data_path = get_data_file_path("amount_in_words_test_data.json")
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        correct = 0
        new_cn_amount_util = AmountUtils()
        for it in data:
            cn = it["cn"]
            val = it["val"]

            a = new_cn_amount_util.word2num(cn)
            if val == float(a):
                correct += 1

        acc = correct / len(data)
        print(f"Acc: {acc}")
        self.assertEqual(acc, 1.0)

    def test_case(self):
        data = [
            ("万贰拾肆元陆角柒分", "24.67"),
            ("捌佰玖拾元零零角壹分", "890.01"),
            ("贰佰柒拾固叁角陆分整", "270.36"),
            ("肆捡圆整(40.00)___7", "40"),
            ("壹拾捌回整", "18"),
            ("贰拾伍捌整", "25"),
            ("合计大零贰佰肆拾捌元陆角捌分", "248.68"),
            ("叁佰固整", "300"),
            ("叁佰零壹园陆角(301.60)", "301.6"),
            ("贰万陆仟零叁拾零圆伍角肆分", "26030.54"),
            ("零万贰万零陆佰伍拾伍元伍角叁分", "20655.53"),
        ]
        cn_amount_util = AmountUtils()
        for cn, gt in data:
            self.assertEqual(gt, cn_amount_util.word2num(cn))
