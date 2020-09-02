from typing import Dict, List

from ocr_structuring.core.models.structure_item import StructureItem


def to_dict(result: Dict[str, StructureItem]):
    """
    把 result 中的对象转换成 dict 格式
    :param result:
    :return:
    """
    _result = {}
    for k, v in result.items():
        if isinstance(v, StructureItem):
            _result[k] = v.to_dict()
        elif isinstance(v, List):
            tmp = []
            for item in v:
                tmp.append({_k: _v.to_dict() for _k, _v in item.items()})
            _result[k] = tmp
        else:
            _result[k] = v
    return _result
