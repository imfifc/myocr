import os

from .crnn_infer_torch import CRNNInferTorch

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
CHARS_DIR = os.path.join(CURRENT_DIR, 'chars')
MODELS_DIR = os.path.join(CURRENT_DIR, 'models')


class CRNNFactory:
    @staticmethod
    def get_shanghai_paymoney_model():
        return CRNNFactory._get_model('step_54000_loss_0.3736_val_0.9468.pt', 'num.txt')

    @staticmethod
    def get_number_space_model():
        return CRNNFactory._get_model(
            'date_step_260000_loss_0.6393.pt', 'num_with_space.txt'
        )

    @staticmethod
    def get_number_amount_model():
        return CRNNFactory._get_model(
            'num_amount_0904_step_325000_loss_0.2283.pt', 'num_amount.txt'
        )



    # @staticmethod
    # def get_number_capital_eng_model():
    #     return CRNNFactory._get_model('receipt_step_328000_loss_0.7278.pt',
    #                                   'num_big_space.txt')
    @staticmethod
    def get_number_capital_eng_model():
        return CRNNFactory._get_model('receipt_step_320000_loss_2.1066_0926.pt',
                                      'num_big_space.txt')

    @staticmethod
    def get_medical_charges_model():
        return CRNNFactory._get_model('medical_charges_step_660000_loss_0.6309.pt', 'final_words_v2.txt')

    @staticmethod
    def get_car_number_capital_eng_model():
        return CRNNFactory._get_model('step_36000.pt',
                                      'num_and_bigeng.txt')

    @staticmethod
    def get_big_chinese_date_model():
        return CRNNInferTorch('step_90000_loss_0.0124_val_0.9999.pt',
                              'chinese_date.txt')

    @staticmethod
    def get_bill_eng_model():
        return CRNNFactory._get_model('bill_eng_step_715000.pt', 'bill_eng.txt')

    @staticmethod
    def get_bank_acceptance_bill_num_model():
        return CRNNFactory._get_model('bank_acceptance_bill_num_model_1c.pt', 'num_with_minus.txt')

    @staticmethod
    def get_bank_acceptance_bill_amount_in_words():
        return CRNNFactory._get_model('bank_acceptance_bill_num_step_195000_loss_0.0006_test_0.8600.pt', 'amount_in_words.txt')

    @staticmethod
    def get_amount_in_chinese_model():
        return CRNNFactory._get_model("amount.pt", "amount.txt")

    @staticmethod
    def get_amount_in_chinese_model_zjg():
        return CRNNFactory._get_model("amount_zhangjiagang.pt", "amount_zhangjiagang.txt")

    @staticmethod
    def get_number():
        return CRNNFactory._get_model("step_25000_loss_0.1872_test_0.9820.pt", "number-hand.txt")

    @staticmethod
    def get_date_small_model():
        return CRNNFactory._get_model("date_small_model_zhangjiagang.pt", "date_small_model_zhangjiagang.txt")

    @staticmethod
    def _get_model(model_name, char_name):
        model_path = os.path.join(MODELS_DIR, model_name)
        char_path = os.path.join(CHARS_DIR, char_name)
        if model_path.endswith('.pt'):
            return CRNNInferTorch(model_path, char_path)
        else:
            raise NotImplementedError('crnn_factory only support .pt model file!')
