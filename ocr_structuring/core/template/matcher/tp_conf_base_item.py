import uuid

import editdistance

from ...utils import str_util
from ...utils.bbox import BBox


class TpConfBaseItem:
    def __init__(self, item_conf, is_tp_conf: bool = False):
        self.conf = item_conf
        self.is_tp_conf = is_tp_conf
        self.uid = uuid.uuid1().hex

        # Supported contents format:
        # 1. string
        # 2. List[string]
        # 3. List[Dict]. {'text': string, 'ed_thresh': 1}
        self.contents = item_conf["contents"]
        if isinstance(self.contents, str):
            self.contents = [self.contents]

        self.item_name = item_conf.get("item_name", self.uid)
        self.bbox_alternative = []  # 如果传入的bbox的个数不止一个，则将其他的记录在bbox_alternative中
        if isinstance(item_conf["area"][0], list):
            # 定义为一系列的区域
            self.bbox = BBox(item_conf["area"][0])
            self.bbox_alternative = [BBox(area) for area in item_conf["area"][1:]]
        else:
            self.bbox = BBox(item_conf["area"])

        self.matched_uid = None

    def __str__(self):
        return f"{self.contents} {self.bbox}"

    def check_content_similar(self, text, remove_symbols=False, remove_space=False):
        """
        检查目标 text 是否与背景元素中定义的 content 相似
            use_ed: 是否额外使用 edit_distance 来做判断
            ed_thresh: 当 edit_distance < ed_thresh 时则认为相似了
        :param text: pipeline 输出的识别结果
        :param remove_symbols: 是否在比较前移除 bg filter_contents 和 label_node 中的符号
        :param remove_space: 是否在比较前移除 bg filter_contents 和 label_node 中的和空格
        :return:
        """
        for item in self.contents:
            if type(item) == str:
                exp_text = item
                if remove_symbols:
                    exp_text = str_util.remove_symbols(exp_text)
                    text = str_util.remove_symbols(text)

                if remove_space:
                    exp_text = str_util.remove_space(exp_text)
                    text = str_util.remove_space(text)

                if text == "" or exp_text == "":
                    continue

                if text and len(text) < 2:
                    continue

                if exp_text and len(exp_text) < 2:
                    continue

                if exp_text == text:
                    return True

                if self.is_tp_conf:
                    ed_thresh = self.conf.get("ed_thresh", 0)
                    ed_match = editdistance.eval(exp_text, text) <= ed_thresh
                    if ed_match:
                        return True
            else:
                exp_text = item["text"]
                ed_thresh = item.get("ed_thresh", 0)

                if remove_symbols:
                    exp_text = str_util.remove_symbols(exp_text)
                    text = str_util.remove_symbols(text)

                if remove_space:
                    exp_text = str_util.remove_space(exp_text)
                    text = str_util.remove_space(text)

                if text == "" or exp_text == "":
                    continue

                ed_match = editdistance.eval(exp_text, text) <= ed_thresh
                if ed_match:
                    return ed_match

        return False
