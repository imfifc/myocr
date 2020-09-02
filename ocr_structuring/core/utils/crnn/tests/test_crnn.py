# encoding=utf-8

import os
from pathlib import Path

import cv2
import unittest

from ocr_structuring.core.utils.crnn.crnn_factory import CRNNFactory

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


class TestCrnn(unittest.TestCase):
    def test_sh_pay_money(self):
        infer = CRNNFactory.get_shanghai_paymoney_model()
        self._infer(infer, 'sh_pay_money')

    def _infer(self, infer, test_dir_name):
        test_dir = Path(CURRENT_DIR) / test_dir_name

        for it in test_dir.iterdir():
            if it.suffix != '.jpg':
                continue

            filename = it.name
            gt = filename.split('___')[0]

            img = cv2.imread(str(it))
            roi = (0, 0, img.shape[1], img.shape[0])
            pred, _ = infer.run(img, roi)

            self.assertEqual(gt, pred)


if __name__ == '__main__':
    unittest.main()
