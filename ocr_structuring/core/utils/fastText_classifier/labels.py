from enum import Enum


class ShippingBill(Enum):
    AIR_WAYBILL = "__label__air-waybill"
    AIR_INVOICE = "__label__air-invoice"
    AIR_PACKING_LIST = "__label__air-packing-list"
    AIR_OTHER = "__label__other"

class ZyhyInovice(Enum):
    INVOICE = "__label__invoice"
    OTHER = "__label__other"
