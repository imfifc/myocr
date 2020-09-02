from typing import List

from ocr_structuring.core.models.structure_item import StructureItem
from .class_names import ClassNamesBase, check_class_names_duplicated
from ..core.structuring import Structuring
from ..core.utils.debug_data import DebugData
from ..tfidf_classifier import TfidfClassifier


class Session:
    def __init__(self, should_init_tp_structure: bool = True, class_name=None):
        """
        :param should_init_tp_structure: 设为 False 可以跳过配置文件的加载，目前只是为了调试非机构化模板时提高效率
        """
        check_class_names_duplicated()
        self.classifier = TfidfClassifier()
        self.structuring = Structuring(should_init_tp_structure, class_name)

    def process(self, raw_data,
                image=None,
                class_name: str = None,
                primary_class: int = None,
                secondary_class: int = None,
                ltrb=True,
                debug_data: DebugData = None, **kwargs):
        """
        :param raw_data:
                ltrb==False [text, x1, y1, x2, y2, x3, y3, x4, y4, angle, label, probability]
                ltrb==True [text, left, top, right, bottom, label, probability]
        :param image: numpy BGR image
        :param class_name: 具体的结构化类型名称，优先级最高
        :param primary_class: 如果没有指定 class_name，则通过一级分类（二级分类）对所有 tfidf 支持的分类进行过滤，再使用 tfidf 分类
        :param secondary_class: 二级分类只有在指定了一级分类的情况下才有意义
        :param ltrb: raw_data 的格式

        :return:
            dict.
            key: item_name
            value: v3 StructureItem.to_dict 的结果
        """
        if class_name is not None:
            # class_name 优先级最高
            pred_class_score = 1
        elif primary_class is not None:
            # 根据一二级分类信息筛类别
            candidate_class_names = self._pre_classify(primary_class, secondary_class)

            if len(candidate_class_names) > 1:
                res = self.classifier.eval(raw_data, candidate_class_names)
                if res is not None:
                    class_name, pred_class_score = res
                    print(f"TFIDF classifier result: {class_name}({pred_class_score})")
                else:
                    raise RuntimeError('tfidf classifier failed')
            elif len(candidate_class_names) == 1:
                class_name = candidate_class_names[0]
                pred_class_score = 1
            else:
                raise RuntimeError('pre_classify failed')
        else:
            # 任何类型信息都没指定，直接用在全部分类中分类
            res = self.classifier.eval(raw_data)
            if res is not None:
                class_name, pred_class_score = res
            else:
                raise RuntimeError('tfidf classifier failed')

        if class_name not in self.structuring.supported_class_names():
            raise NotImplementedError(f'class_name [{class_name}] not supported')

        result = self.structuring.process(raw_data, image, class_name, ltrb, debug_data=debug_data, **kwargs)

        if isinstance(result, dict):
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
            result = _result

        return self._make_response_result(result, class_name, pred_class_score)

    def process_multi(self, raw_datas, images, class_name):
        result = self.structuring.process_multi(raw_datas, images, class_name)
        if hasattr(result, "to_dict"):
            return self._make_response_result(result.to_dict(), class_name, 1)
        elif isinstance(result, dict):
            return self._make_response_result(result, class_name, 1)
        else:
            raise RuntimeError('process_multi result format error')
            return

    def _pre_classify(self, primary_class: int, secondary_class: int = None) -> List[str]:
        """
        根据一级、二级分类 code 获得所有候选的 class_name

        从 code 到 class_name 的映射，模板和非模板的定义方式不同：
        - 模板结构化：配置文件中定义 primary_class 和 secondary_class 两个字段
        - 非模板结构化：每种非模板类型返回 primary_class 和 secondary_class
        """
        names = []
        for primary_class_name, primary_class_enum in ClassNamesBase.subclasses.items():
            if primary_class_enum.code.value == primary_class:
                for secondary_class_enum in primary_class_enum.__members__.values():
                    class_name = secondary_class_enum.name
                    if class_name == 'code':
                        continue

                    if secondary_class is None:
                        names.append(class_name)
                    else:
                        if secondary_class_enum.value == secondary_class:
                            names.append(class_name)

        return names

    def _make_response_result(self, result,
                              class_name: str,
                              class_classify_score: float):
        """
        :param result: dict. key: item_name.  value: StructureItem 内容
        :param class_name:
        :param class_classify_score:
        :return:
        """

        return {
            'data': result,
            'metadata': {
                'class_name': class_name,
                'class_classify_score': class_classify_score,
            }
        }
