from enum import Enum, auto
from typing import Union, Tuple, List

from ocr_structuring.utils.logging import logger
import re

class ElementTextType(Enum):
    ALL_NUM = auto()  # 如 4.23 ，1/02 , 20-21
    ALL_CHAR = auto()  # 如 ASPCS-HELLO ，这种有 字母，以及特殊符号，无数字
    ALL_SPEC = auto()  # 如果将数字，字母全部剔除，只有特殊符号
    NUM2CHAR = auto()  # 数字之后接字母和特殊符号 ， 如 4EA
    MIX_NUM_CHAR = auto()  # 各种混合类型的数据


class HeaderRequirement:
    def __init__(self, header_reguirement: Union[Enum, Tuple[Enum, List[str]]]):
        if isinstance(header_reguirement, Enum):
            # 对应正则表达式需要适应的header_type
            self.header_type = header_reguirement
            # 对应正则表达式需要适应的 header 需要满足的regex
            self.header_regexs = None
        else:
            self.header_type, self.header_regexs = header_reguirement

    def parse_header_requirement(self, fields):
        """
        :param header_group: 表头
        :param fields: 各个列信息
        :return: 返回header_group 是否包含header requirements 所要求的列，并返回 fields 当中的列id
        """
        fields_in_type_req = {fid: field for fid, field in fields.items() if field.header.head_type == self.header_type}

        if len(fields_in_type_req) == 0:
            return False, set()

        if self.header_regexs is None:
            logger.info(
                'check header {} by {}'.format([f.header.key_node.content for f in fields_in_type_req.values()], self.header_type))
            return True, set(fields_in_type_req.keys())

        try:
            regex_check = {fid: field for fid, field in fields_in_type_req.items() if
                       any([re.match(regex, field.header.key_node.content,re.IGNORECASE) for regex in self.header_regexs])}
        except:
            print('hello')

        if len(regex_check) > 0:
            logger.info('check header {} by {}'.format([ f.header.key_node.content for f in regex_check.values()],self.header_regexs))
            return True, set(regex_check.keys())
        return False, set()
