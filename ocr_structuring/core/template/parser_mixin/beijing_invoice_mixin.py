import re
from typing import Dict

import numpy as np

from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.non_template.processor.zeng_zhi_shui import text_classifier
from ...template.tp_node_item import TpNodeItem
from ...utils import bk_tree
from ...utils import str_util
from ...utils.beijing_hospital import beijing_hospital_code_name_map
from ocr_structuring.utils.logging import logger


# noinspection PyMethodMayBeStatic
class BeijingInvoiceMixin:
    def _bk_tree_beijing_hospital_code_in_serialnumber(self, structure_items):
        serialnumber_item = structure_items.get('serialnumber', None)
        if serialnumber_item is None:
            return

        serialnumber = serialnumber_item.content

        if serialnumber is None:
            return

        old_hospital_code = serialnumber[:8]

        correct_word = bk_tree.beijing_hospital_code().search_one(old_hospital_code,
                                                                  search_dist=1,
                                                                  min_len=7)

        if correct_word is None:
            return

        if old_hospital_code != correct_word:
            logger.debug('Serial number hospital code bk tree look up:')
            logger.debug('\tOrigin: {}'.format(old_hospital_code))
            logger.debug('\tItem in tree: {}'.format(correct_word))

        new_serial_num = correct_word + serialnumber[8:]
        serialnumber_item.content = new_serial_num

    def _get_beijing_hospital_name_by_hospital_code(self, structure_items, fg_items):
        serialnumber_fg_item = fg_items.get('serialnumber', None)
        if serialnumber_fg_item is None:
            return

        serialnumber_item = structure_items.get('serialnumber', None)
        hospital_name_item = structure_items.get('hospital_name', None)
        if serialnumber_item is None or hospital_name_item is None:
            return

        serialnumber_labels = []

        regex_failed_serialnumbers_tp_rects = serialnumber_fg_item.regex_failed_tp_rects
        for rect_data in regex_failed_serialnumbers_tp_rects:
            serialnumber_labels.append((rect_data.text, rect_data.scores))

        serialnumber = serialnumber_item.content
        if serialnumber is not None:
            serialnumber_labels.insert(0, (serialnumber, serialnumber_item.scores))

        for serial_num, scores in serialnumber_labels:
            serial_num = str_util.filter_num(serial_num)
            if len(serial_num) < 8:
                continue
            hospital_code = serial_num[:8]

            hospital_name = beijing_hospital_code_name_map.get(hospital_code, None)

            if hospital_name is None:
                continue

            logger.debug('Look up beijing hospital name:')
            logger.debug('\tCode: {}'.format(hospital_code))
            logger.debug('\tName: {}'.format(hospital_name))

            hospital_name_item.content = hospital_name
            hospital_name_item.scores = serialnumber_item.scores[:8]
            break

    def _add_paytype(self, structure_items):
        """
        根据 paytype1 和 paytype2 字段决定 paytype 字段，用于 beijing menzhen 和 beijing menzhen teshu
        :param structure_items:
        :return:
        """
        pred1 = structure_items['paytype1'].content
        pred2 = structure_items['paytype2'].content

        if pred1 and int(pred1) == 1 or pred2 and int(pred2) == 1:
            paytype = '医保'
        else:
            paytype = '普通'

        structure_items['paytype'] = StructureItem(item_name='paytype',
                                                   show_name='结算类型',
                                                   content=paytype,
                                                   scores=1
                                                   )

    # this is in org
    def _post_func_beijing_city(self,
                                item_name: str,
                                passed_nodes: Dict[str, TpNodeItem],
                                node_items: Dict[str, TpNodeItem],
                                img: np.ndarray):

        for uid in passed_nodes:
            node = passed_nodes[uid]
            if '北京' in node.text:
                return '北京', [1, 1]

            for match_str in node.regex_match_results:
                if match_str.text in ['中', '央']:
                    return '中央', [1, 1]
                if match_str.text in ['北', '京']:
                    return '北京', [1, 1]
        return '北京', [1, 1]

    def _get_receiptno_from_barcode(self, structure_items, receipt_no_len=10, mode=0):
        """
        有些发票（如北京）条形码的末尾 10 位是发票号
        :param structure_items:
        :param receipt_no_len: 用于从 barcode 末尾截取发票号的长度
        :param mode
            0: 当 receiptno content 为空时才从 barcode 中取
            1: 当从 barcode 中取得的 receipt_no 平均 score 大于 receiptno 的平均 score 时，才用 barcode 中的结果
            2: 如果 barcode 的值有效，则使用从 barcode 中提取的 receipt_no

            如果发票号区域的质量较差（如beijing_menzhen_teshu）可以考虑用 mode=2，一般用 mode=0
        :return:
        """
        barcode_item = structure_items.get('barcode', None)
        if barcode_item is None:
            return

        barcode = barcode_item.content
        if not barcode:
            return

        receiptno_item = structure_items.get('receiptno', None)
        if receiptno_item is None:
            return

        receiptno_from_barcode = barcode[-receipt_no_len:]
        barcode_scores = barcode_item.scores[-receipt_no_len:]
        if len(receiptno_from_barcode) != receipt_no_len:
            return

        origin_receiptno = receiptno_item.content
        origin_scores = receiptno_item.scores

        def print_info():
            logger.debug('Get receiptno from barcode:')
            logger.debug('\torigin receiptno: {}'.format(origin_receiptno))
            logger.debug('\tbarcode: {}'.format(barcode))
            logger.debug('\treceiptno from barcode: {}'.format(receiptno_from_barcode))

        if mode == 1:
            if np.mean(barcode_scores) > np.mean(origin_scores) and \
                    receiptno_from_barcode != origin_receiptno:
                print_info()
                receiptno_item.content = receiptno_from_barcode
        elif mode == 0:
            if not origin_receiptno:
                print_info()
                receiptno_item.content = receiptno_from_barcode
        elif mode == 2:
            if receiptno_from_barcode != origin_receiptno:
                print_info()
                receiptno_item.content = receiptno_from_barcode

    def _pre_func_hospital_name(self,
                                item_name: str,
                                passed_nodes: Dict[str, TpNodeItem],
                                node_items: Dict[str, TpNodeItem],
                                img: np.ndarray
                                ):
        invalid_pattern = ['^(\(?|（?)章(\)?|）?):?$',
                           '^收款单位$',
                           '收款单.$',
                           '^收款单.(\(?|（?)章(\)?|）?):?$',
                           '^单位$',
                           '￥',
                           ".{,2}单位$",
                           ]

        replace_map = {
            "普都": "首都",
            "首部": "首都",
            # "友.医院": "友谊医院", # 可能是友好医院，注释掉
            "医料": "医科",
            "阴属": "附属",
            "附居": "附居",
            "^.部": "首都",
            "^.都医科": "首都医科",
        }

        sub_map = [".{,2}单位", "^(\(?|（?)章(\)?|）?):?", "^收款单.(\(?|（?)章(\)?|）?):?", "^款", "收人$", "收款人$", '^.{,3}款单.{,3}章']
        for node in passed_nodes.values():
            if text_classifier.is_amount_in_words(node.text):
                node.clear()
                continue

            for rl in invalid_pattern:
                if re.search(rl, node.text):
                    node.clear()
                    break
            for sub in sub_map:
                node.text = re.sub(sub, '', node.text)
            for error_text in replace_map.keys():
                node.text = re.sub(error_text, replace_map[error_text], node.text)
            if '首都医科大学' in node.text and '中医医院' in node.text:
                node.text = '首都医科大学附属北京中医医院'

    def _tmpl_post_hospital_name_bktree_correction(self, structure_items, fg_items, img):

        hospital_name = structure_items['hospital_name'].content

        if not hospital_name:
            return
        res = bk_tree.beijing_hospital_name().search_one(hospital_name, search_dist=2, min_len=4)
        if res:
            structure_items['hospital_name'].content = res
        else:
            replace_bracket = ['（', '）', '(', ')', '_']
            for bracket in replace_bracket:
                hospital_name = hospital_name.replace(bracket, '')
            res = bk_tree.beijing_hospital_name().search_one(hospital_name, search_dist=2,
                                                             min_len=4)
            if res:
                structure_items['hospital_name'].content = res
