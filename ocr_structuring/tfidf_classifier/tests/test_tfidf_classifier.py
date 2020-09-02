import os
import json
import unittest
from ocr_structuring.tfidf_classifier import TfidfClassifier

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, 'data')


class TestClassify(unittest.TestCase):
    def test_yiliao_classifier(self):
        classes_name = [
            'beijing_menzhen',
            'beijing_menzhen_teshu',
            'beijing_zhuyuan',
            'shanghai_menzhen',
            'shanghai_zhuyuan',
        ]

        self.classifier = TfidfClassifier()
        self._test_files(classes_name)

        self.classifier = TfidfClassifier('medical_invoice')
        self._test_files(classes_name)

    def test_huarui_classifier(self):
        classes_name = [
            # "huarui_yuxiang_jida1",
            "huarui_yuxiang_jida2",
            "huarui_yuxiang_shouxie",
            "huarui_zhongjian_jida",
            "huarui_zhongjian_shouxie_h",
            "huarui_zhongjian_shouxie_v",
        ]

        self.classifier = TfidfClassifier()
        self._test_files(classes_name)

        self.classifier = TfidfClassifier('huarui_huodan')
        self._test_files(classes_name)

    def test_idcard_classifier(self):
        classes_name = [
            'idcard',
            'idcard_bk'
        ]

        self.classifier = TfidfClassifier()
        self._test_files(classes_name)

        self.classifier = TfidfClassifier('idcard')
        self._test_files(classes_name)

    def _test_files(self, classes_name):
        for class_name in classes_name:
            file_path = os.path.join(DATA_DIR, class_name + '.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                pred, score = self.classifier.eval(data['raw_data'], classes_name)
                print(f'gt:{class_name} pred:{pred}')
                self.assertEqual(class_name, pred)


if __name__ == "__main__":
    unittest.main()
