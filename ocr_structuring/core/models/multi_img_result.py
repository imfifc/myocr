from abc import abstractmethod
from typing import List, Dict

from .structure_item import StructureItem
from .structure_result import StructureResult
from .utils import to_dict


class MultiImgResult(StructureResult):
    """
    用于返回从多张图片上获得的结构化数据，例如空运单中，一份发票可能由多张图片组成，最终返回的
    结构化结构是由多张的结果组成的
    """

    def __init__(self, doc_type: str):
        # 文档类型
        self.doc_type: str = doc_type
        # 文档在原始 PDF 中的页码，从 0 开始
        self.pages: List[int] = []
        # 多张文档图片合并后的结果
        self.doc_result: Dict[str, StructureItem] = {}
        # 每张文档图片的结果
        self.per_page_result: Dict[int, Dict[str, StructureItem]] = {}

    def add_single_result(self, page: int, result: Dict[str, StructureItem]):
        self.pages.append(page)
        self.per_page_result[page] = result

    def merge_per_page_result(self):
        """
        合并 self.per_page_result，并设置 self.doc_result。默认的结果和并行为：
        1. 所有单张结果上的 key-value 结果通过 dict.update 合并，不考虑先后顺序，后面的会覆盖前面的
        2. 如果某个字段是表格(通过判断 table 是否在该字段的名称中)，则把所有表格的信息 append 到一起
        """
        for single in self.per_page_result.values():
            for k, v in single.items():
                if "table" in k:
                    # 假设 table 一定是数组
                    if k in self.doc_result:
                        self.doc_result[k].content.extend(v.content)
                    else:
                        self.doc_result[k] = v
                else:
                    self.doc_result.update({k: v})

    def to_dict(self):
        """
        和 task-flow 约定，doc_type 的值会加在 doc_result 后面
        :return:
            {
                "doc_type": "",
                "pages": [1,2,3],
                "doc_result_{doc_type}": Dict[str, StructureItem]
                "per_page_result": [
                    {
                      "page": 1,
                      "doc_result_{doc_type}": Dict[str, StructureItem]
                    }
                ]
            }
        """

        per_page_result = []
        for p, v in self.per_page_result.items():
            per_page_result.append(
                {"page": p, f"doc_result_{self.doc_type}": to_dict(v)}
            )

        out = {
            "doc_type": self.doc_type,
            "pages": self.pages,
            f"doc_result_{self.doc_type}": to_dict(self.doc_result),
            "per_page_result": per_page_result,
        }
        return out
