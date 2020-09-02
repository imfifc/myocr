# encoding=utf-8
import os

from .core import BKTree
from .loader import load_from_disk

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

# BK-TREE的源文件
SHIP_BG = 'ship_bg_item.txt'
SHIP_FG = 'ship_fg_item.txt'
SHANGHAI_HOSPITAL_NAME = 'shanghai_hospital_name.txt'
BEIJING_HOSPITAL_CODE = 'beijing_hospital_code.txt'
IGNORE = 'ignore.txt'
SUMMARY_CHARGE_ITEM_NAME = 'summary_charges.txt'
MEDICAL_INSURANCE_TYPE = 'medical_insurance_type.txt'
MEDICAL_INSTITUTION_TYPE = 'medical_institution_type.txt'
BANK = 'bank.txt'
DEGREE = 'degree.txt'
MAJOR = 'major.txt'
COLLEGE = 'colleges.txt'
CAR_MODEL = 'car_model.txt'

CITY = 'city.txt'
DISTRICT = 'district.txt'
PROVINCE = 'province.txt'

BUSINESS_LICENCE_TYPE = 'business_licence_type.txt'
JING_YING_FAN_WEI = 'jing_ying_fan_wei.txt'
VEHICLE_TYPE = 'vehicle_type.txt'

# 医疗bk_tree
MEDICAL_DRUG = 'medical_drug.txt'
MEDICAL_EQUI = 'medical_equi.txt'
MEDICAL_EXAM = 'medical_exam.txt'
MEDICAL_EXAMINATION_DATA = 'medical_examination_data.txt'
MEDICAL_SERVICE = 'medical_service.txt'

BEIJING_HOSPITAL_NAME = 'beijing_hospital_name.txt'

KUNSHAN = "kunshan_bank.txt"
KUNSHAN_COMPANY = "kunshan_company.txt"

WXNSH_BUSINESS_TYPE = 'wxnsh_business_type.txt'
WXNSH_COMPANY_NAME = 'wxnsh_company_name.txt'
WXNSH_BANK_NAME = 'wxnsh_bank_name.txt'

# house_cert
HOUSE_CERT_COMMON_STATE = 'house_cert_common_state.txt'
HOUSE_CERT_HOUSE_PROPERTY = 'house_cert_house_property.txt'
HOUSE_CERT_PLAN_PURPOSE = 'house_cert_plan_purpose.txt'

# zhangjiagang
ZHANGJIAGANG_COMPANY = 'zhangjiagang_company.txt'
ZHANGJIAGANG_BANK = 'zhangjiagang_bank.txt'

# hangzhou bank
HANGZHOU_BANK = 'hangzhou_bank.txt'

# 内存中的BK-TREE
MEMORY = {
    SHIP_BG: None,
    SHIP_FG: None,
    SHANGHAI_HOSPITAL_NAME: None,
    BEIJING_HOSPITAL_CODE: None,
    IGNORE: None,
    SUMMARY_CHARGE_ITEM_NAME: None,
    MEDICAL_INSURANCE_TYPE: None,
    MEDICAL_INSTITUTION_TYPE: None,
    BANK: None,
    DEGREE: None,
    MAJOR: None,
    COLLEGE: None,
    CAR_MODEL: None,
    CITY: None,
    DISTRICT: None,
    PROVINCE: None,
    BUSINESS_LICENCE_TYPE: None,
    JING_YING_FAN_WEI: None,
    VEHICLE_TYPE: None,
    MEDICAL_DRUG: None,
    MEDICAL_EQUI: None,
    MEDICAL_EXAM: None,
    MEDICAL_EXAMINATION_DATA: None,
    MEDICAL_SERVICE: None,
    BEIJING_HOSPITAL_NAME: None,
    KUNSHAN: None,
    KUNSHAN_COMPANY: None,
    WXNSH_BUSINESS_TYPE: None,
    WXNSH_COMPANY_NAME: None,
    WXNSH_BANK_NAME: None,
    HOUSE_CERT_COMMON_STATE: None,
    HOUSE_CERT_HOUSE_PROPERTY: None,
    HOUSE_CERT_PLAN_PURPOSE: None,
    ZHANGJIAGANG_COMPANY: None,
    ZHANGJIAGANG_BANK: None,
    HANGZHOU_BANK: None,
}


def zhangjiagang_company_tree() -> BKTree:
    return __get_tree(ZHANGJIAGANG_COMPANY)

def hangzhou_bank_tree() -> BKTree:
    return __get_tree(HANGZHOU_BANK)

def zhangjiagang_bank_tree() -> BKTree:
    return __get_tree(ZHANGJIAGANG_BANK)


def kunshan_tree() -> BKTree:
    return __get_tree(KUNSHAN)


def kunshan_company_tree() -> BKTree:
    return __get_tree(KUNSHAN_COMPANY)


def wxnsh_business_type() -> BKTree:
    return __get_tree(WXNSH_BUSINESS_TYPE)


def wxns_company_name_tree() -> BKTree:
    return __get_tree(WXNSH_COMPANY_NAME)


def wxns_bank_name_tree() -> BKTree:
    return __get_tree(WXNSH_BANK_NAME)


def beijing_hospital_name() -> BKTree:
    return __get_tree(BEIJING_HOSPITAL_NAME)


def vehicle_type() -> BKTree:
    return __get_tree(VEHICLE_TYPE)


def city() -> BKTree:
    return __get_tree(CITY)


def province() -> BKTree:
    return __get_tree(PROVINCE)


def district() -> BKTree:
    return __get_tree(DISTRICT)


def ship_bg() -> BKTree:
    return __get_tree(SHIP_BG)


def ship_fg() -> BKTree:
    return __get_tree(SHIP_FG)


def bank() -> BKTree:
    return __get_tree(BANK)


def degree() -> BKTree:
    return __get_tree(DEGREE)


def major() -> BKTree:
    return __get_tree(MAJOR)


def colleges() -> BKTree:
    return __get_tree(COLLEGE)


def shanghai_hospital_name() -> BKTree:
    return __get_tree(SHANGHAI_HOSPITAL_NAME)


def beijing_hospital_code() -> BKTree:
    return __get_tree(BEIJING_HOSPITAL_CODE)


def ignore() -> BKTree:
    return __get_tree(IGNORE)


def summary_charge_item_name() -> BKTree:
    return __get_tree(SUMMARY_CHARGE_ITEM_NAME)


def medical_insurance_type() -> BKTree:
    return __get_tree(MEDICAL_INSURANCE_TYPE)


def medical_institution_type() -> BKTree:
    return __get_tree(MEDICAL_INSTITUTION_TYPE)


def car_model() -> BKTree:
    return __get_tree(CAR_MODEL)


def business_licence_type() -> BKTree:
    return __get_tree(BUSINESS_LICENCE_TYPE)


def jing_ying_fan_wei() -> BKTree:
    return __get_tree(JING_YING_FAN_WEI)


def medical_drug_tree() -> BKTree:
    return __get_tree(MEDICAL_DRUG)


def medical_equi_tree() -> BKTree:
    return __get_tree(MEDICAL_EQUI)


def medical_exam_tree() -> BKTree:
    return __get_tree(MEDICAL_EXAM)


def medical_examination_tree() -> BKTree:
    return __get_tree(MEDICAL_EXAMINATION_DATA)


def medical_service_tree() -> BKTree:
    return __get_tree(MEDICAL_SERVICE)


def house_cert_common_state() -> BKTree:
    return __get_tree(HOUSE_CERT_COMMON_STATE)


def house_cert_plan_purpose() -> BKTree:
    return __get_tree(HOUSE_CERT_PLAN_PURPOSE)


def house_cert_house_property() -> BKTree:
    return __get_tree(HOUSE_CERT_HOUSE_PROPERTY)


def get_tree(tree_name) -> BKTree:
    return __get_tree(tree_name)


def __get_tree(tree_name) -> BKTree:
    if tree_name not in MEMORY:
        raise NotImplementedError('BK-TREE: %s not implemented' % tree_name)
    if MEMORY[tree_name] is None:
        MEMORY[tree_name] = load_from_disk(CURRENT_DIR, tree_name)
    return MEMORY[tree_name]
