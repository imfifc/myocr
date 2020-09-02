"""
定义 primary_class 和 secondary_class

每一个 Enum 的子类必须有 code 属性，作为 primary_class
其他属性为 secondary_class，属性名为具体的 class_name
"""
from enum import Enum


class ClassNamesBase:
    subclasses = {}
    _secondary_classes = None

    def __init_subclass__(cls, **kwargs):
        cls.subclasses[cls.__name__] = cls


class MedicalInvoice(ClassNamesBase, Enum):
    code = 1000
    beijing_menzhen = 1001
    beijing_menzhen_teshu = 1002
    beijing_zhuyuan = 1003
    shanghai_menzhen = 1004
    shanghai_zhuyuan = 1005


class IdCard(ClassNamesBase, Enum):
    code = 2000
    idcard = 2001
    idcard_bk = 2002


class WanLi(ClassNamesBase, Enum):
    code = 3000
    air_waybill = 3001
    invoice = 3002
    packing_list = 3003
    other = 3004


def check_class_names_duplicated():
    codes = {}
    names = {}
    for primary_class_enum in ClassNamesBase.subclasses.values():
        for it in primary_class_enum.__members__.values():
            if it.value in codes:
                raise ValueError(f"{it.value} of {primary_class_enum} already exists in {codes[it.value]}")
            if it.name in names:
                raise ValueError(f"{it.name} of {primary_class_enum} already exists in {names[it.name]}")

            codes[it.value] = primary_class_enum
            if it.name != 'code':
                names[it.name] = primary_class_enum
