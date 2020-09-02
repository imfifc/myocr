import os
from typing import List
from .labels import ShippingBill, ZyhyInovice

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR = os.path.join(CURRENT_DIR, "models")


class FastTextClassifier:
    _instance = None
    shipping_bill = None
    zyhy_invoice = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def run_shipping_bill(self, texts: List[str]):
        """
        :param texts:
        :return:
        """
        if self.shipping_bill is None:
            self.shipping_bill = self._load_model("shipping_bill")
        # tuple ((label1, label2,), (score1, score2,])
        ret = self.shipping_bill.predict(texts)

        # tuple ((label1, score1), (label2, score2))
        return self._convert(ret, ShippingBill)

    def run_zyhy_invoice(self, texts: List[str]):
        """
        :param texts:
        :return:
        """
        if self.zyhy_invoice is None:
            self.zyhy_invoice = self._load_model("zyhy_model")
        # tuple ((label1, label2,), (score1, score2,])
        ret = self.zyhy_invoice.predict(texts)

        # tuple ((label1, score1), (label2, score2))
        return self._convert(ret, ZyhyInovice)

    def _load_model(self, name):
        try:
            import fasttext
        except ModuleNotFoundError as e:
            print("fasttext is not installed. Please run 'pip3 install git+http://git.tianrang-inc.com/tianshi/fastText.git'")
            raise e
        return fasttext.load_model(os.path.join(MODELS_DIR, name + ".bin"))

    def _convert(self, ret, enum_cls):
        # convert label to enum
        # zip label and score
        # TODO: handle result label and Enum class value mismatch
        out = []
        for it in zip(ret[0], ret[1]):
            out.append((enum_cls(it[0][0]), it[1][0]))
        return out


fastText_classifier = FastTextClassifier()
