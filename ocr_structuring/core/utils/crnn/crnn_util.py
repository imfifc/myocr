from __future__ import unicode_literals

from .crnn_factory import CRNNFactory


class CRNNUtil:
    _instance = None
    shanghai_paymoney = None
    number_space = None
    medical_charges = None
    number_capital_eng = None
    chinese_date = None
    car_number_capital_eng = None
    car_model_capital_eng = None
    number_amount = None
    bill_eng = None
    bank_acceptance_bill_num = None
    bank_acceptance_bill_amount_in_words = None
    amount_in_chinese = None
    amount_in_chinese_zjg = None
    number = None
    date_small_model = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        # TODO 检查模型和字符文件存不存在
        pass

    def run_number_capital_eng(self, img, roi):
        if self.number_capital_eng is None:
            self.number_capital_eng = CRNNFactory.get_number_capital_eng_model()
        return self.number_capital_eng.run(img, roi)

    def run_shanghai_paymoney(self, img, roi):
        if self.shanghai_paymoney is None:
            self.shanghai_paymoney = CRNNFactory.get_shanghai_paymoney_model()

        return self.shanghai_paymoney.run(img, roi)

    def run_number_space(self, img, roi):
        if self.number_space is None:
            self.number_space = CRNNFactory.get_number_space_model()
        return self.number_space.run(img, roi)

    def run_medical_charges(self, img, roi):
        if self.medical_charges is None:
            self.medical_charges = CRNNFactory.get_medical_charges_model()
        return self.medical_charges.run(img, roi)

    def run_chinese_date(self, img, roi):
        if self.chinese_date is None:
            self.chinese_date = CRNNFactory.get_big_chinese_date_model()

        return self.chinese_date.run(img, roi)

    def run_car_number_capital_eng(self, img, roi):
        if self.number_capital_eng is None:
            self.number_capital_eng = CRNNFactory.get_car_number_capital_eng_model()
        return self.number_capital_eng.run(img, roi)

    def run_number_amount(self, img, roi):
        if self.number_amount is None:
            self.number_amount = CRNNFactory.get_number_amount_model()
        return self.number_amount.run(img, roi)

    def run_bill_eng_model(self, img, roi):
        if self.bill_eng is None:
            self.bill_eng = CRNNFactory.get_bill_eng_model()
        return self.bill_eng.run(img, roi)

    # def run_car_model_capital_eng(self, img, roi):
    #     if self.car_model_capital_eng is None:
    #         self.car_model_capital_eng = CRNNFactory.get_car_model_capital_eng_model()
    #     return self.car_model_capital_eng.run(img, roi)

    def run_bank_acceptance_bill_num_model(self, img, roi):
        if self.bank_acceptance_bill_num is None:
            self.bank_acceptance_bill_num = CRNNFactory.get_bank_acceptance_bill_num_model()
        return self.bank_acceptance_bill_num.run(img, roi)
    
    def run_amount_in_chinese(self, img, roi):
        if self.amount_in_chinese is None:
            self.amount_in_chinese = CRNNFactory.get_amount_in_chinese_model()
        return self.amount_in_chinese.run(img, roi)

    def run_amount_in_chinese_zjg(self, img, roi):
        if self.amount_in_chinese_zjg is None:
            self.amount_in_chinese_zjg = CRNNFactory.get_amount_in_chinese_model_zjg()
        return self.amount_in_chinese_zjg.run(img, roi)

    def run_number(self, img, roi):
        if self.number is None:
            self.number = CRNNFactory.get_number()
        return self.number.run(img, roi)

    def run_date_small_model(self, img, roi):
        if self.date_small_model is None:
            self.date_small_model = CRNNFactory.get_date_small_model()
        return self.date_small_model.run(img, roi)

    def run_bank_acceptance_bill_amount_in_words(self, img, roi):
        if self.bank_acceptance_bill_amount_in_words is None:
            self.bank_acceptance_bill_amount_in_words = CRNNFactory.get_bank_acceptance_bill_amount_in_words()
        return self.bank_acceptance_bill_amount_in_words.run(img, roi)


crnn_util = CRNNUtil()
