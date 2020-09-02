import math
import re
from typing import Dict

import numpy as np
from distance_metrics import lcs

from ocr_structuring.core.utils.crnn import crnn_util
from ocr_structuring.core.utils.table.table_handle import TableStructured
from ...models.structure_item import StructureItem
from ...template.tp_node_item import TpNodeItem
from ...utils import bk_tree
from ...utils import date_util
from ...utils import str_util
from ...utils.guess_gender import guess_gender
from ...utils.node_item_group import NodeItemGroup, Match
from ocr_structuring.utils.logging import logger


# noinspection PyMethodMayBeStatic
class MedicalInvoiceMixin:
    def _pre_func_institution_type(self,
                                   item_name: str,
                                   passed_nodes: Dict[str, TpNodeItem],
                                   node_items: Dict[str, TpNodeItem],
                                   img: np.ndarray):
        for node in passed_nodes.values():
            text = node.text
            redundant_words = ['^医疗机构类型:', '^医疗.*构类型', '^医疗机构类', '^.{2,}机构类型', '^医疗机构类', '^医疗机']
            for rule in redundant_words:
                if re.search(rule, text):
                    text = re.sub(rule, '', text)
            text = str_util.remove_symbols(text)
            if node.text != text:
                logger.debug('institution {} is subtracted from {}'.format(re.sub(rule, '', text), text))
                node.text = text

    def _pre_func_beijing_menzhen_medical_insurance_type(self,
                                                         item_name: str,
                                                         passed_nodes: Dict[str, TpNodeItem],
                                                         node_items: Dict[str, TpNodeItem],
                                                         img: np.ndarray):
        ignore_texts = ['医疗机构类型', '金额', '医保类型', '性别', '等级', '项目', '规格', '数量/单位', '社会保障卡号']
        NodeItemGroup.clear_ignore(passed_nodes,
                                   ignore_texts,
                                   flag=Match.COMPLETE)

    def _bk_tree_shanghai_medical_institution_type(self, structure_items, fg_items):
        medical_institution_type_item = structure_items.get('medical_institution_type')
        if medical_institution_type_item is None:
            return

        text = medical_institution_type_item.content

        length = len(text)
        if length >= 5:
            search_dist = 2
        else:
            search_dist = 1

        bk_res = bk_tree.medical_institution_type().search_one(text,
                                                               search_dist=search_dist,
                                                               min_len=2)

        if bk_res != medical_institution_type_item.content:
            logger.debug('medical_institution_type bk_tree:')
            logger.debug('\tOrigin: {}'.format(text))
            logger.debug('\tItem in tree: {}'.format(bk_res))

            medical_institution_type_item.content = bk_res

    def _bk_tree_beijing_medical_institution_type(self, structure_items, fg_items):
        medical_institution_type_item = structure_items.get('medical_institution_type', None)

        if "专科医院" in medical_institution_type_item.content:
            structure_items['medical_institution_type'].content = "专科医院"
            return

        if medical_institution_type_item.content.startswith('专科') or \
                medical_institution_type_item.content.startswith('专利'):
            structure_items['medical_institution_type'].content = "专科医院"
            return

        if not medical_institution_type_item.content:

            # 说明现在拿不到medical_insurance_type ， 考虑可能是结构化过程中的问题
            # ，尝试非结构化方法
            node_items = fg_items['medical_institution_type'].node_items_backup
            bg_node_regex = ['^医疗结构类型$', '^医疗.*构类型', "疗机构类型"]

            bg_node = None
            for node in node_items.values():
                is_bg_node = False
                for rl in bg_node_regex:
                    if re.search(rl, node.text):
                        is_bg_node = True
                if is_bg_node:
                    bg_node = node
                    break
            # 遍历所有的node，如果这个node在medical周围而且能够在bk_tree中找到类似的结果，则把这个结果搞进去
            # fg 为 bg_rect 的右侧的一个区域
            if bg_node:

                bg_xmin, bg_ymin, bg_xmax, bg_ymax = bg_node.bbox.rect
                bg_height = (bg_ymax - bg_ymin)
                bg_width = (bg_xmax - bg_xmin)
                fg_xmin = bg_xmax
                fg_xmax = fg_xmin + bg_width * 3
                fg_ymin = bg_ymin - bg_height
                fg_ymax = bg_ymax + bg_height
                fg_rect = [int(fg_xmin), int(fg_ymin), int(fg_xmax), int(fg_ymax)]
                prob_res = []
                for node in node_items.values():
                    if node.bbox.is_center_in(fg_rect):
                        if len(node.text) <= 1:
                            continue
                        if str_util.keep_num_char(node.text) == node.text and len(node.text) <= 4:
                            continue
                        if node.text == '年' or node.text == '日':
                            continue
                        prob_res.append(node.text)

                for idx, res in enumerate(prob_res):
                    bk_res = bk_tree.medical_institution_type().search_one(res,
                                                                           search_dist=2,
                                                                           min_len=2)
                    prob_res[idx] = bk_res
                filter_prob_res = list(filter(lambda x: x is not None, prob_res))
                if not filter_prob_res:
                    return
                if len(filter_prob_res) == 1:
                    medical_institution_type_item.content = filter_prob_res[0]
                    return
                else:
                    medical_institution_type_item.content = max(filter_prob_res, key=lambda x: len(x))
                    return
            else:
                # 顺便尝试搜索一下常见的医疗机构类型，避免bg没有被找到的情况
                fg_node_regex = {
                    "综合医院": ["^综合医院$", "类综合医院", "类型综合医院"],
                    "中医医院": ["医疗.{1,2}中医医院", "类中医医院"],
                    "社区卫生服务中心": ["社区卫生服务中心"],
                    "中西医结合医院": ["中西医结合医院"],
                    "非营利综合医院": ["非营利综合医院"],
                    "对外中医": ['对外中医$']
                }
                for node in node_items.values():
                    for institution_type in fg_node_regex:
                        for rl in fg_node_regex[institution_type]:
                            if re.search(rl, node.text):
                                medical_institution_type_item.content = institution_type
                                return
            return

        if medical_institution_type_item.content:

            text = medical_institution_type_item.content

            if text.startswith('型'):
                medical_institution_type_item.content = medical_institution_type_item.content[1:]
                return
            redundant_words = ['^医疗机构类型:', '^医疗.*构类型', '^医疗机构类', '^.{2,}机构类型', ]
            for rule in redundant_words:
                if re.search(rule, text):
                    logger.debug('institution {} is subtracted from {}'.format(re.sub(rule, '', text), text))
                    text = re.sub(rule, '', text)

            text = str_util.remove_redundant_patthern(text, redundant_words)
            res = bk_tree.medical_institution_type().search_one(text,
                                                                search_dist=1,
                                                                min_len=2)
            res_2 = None
            if res is None:
                # 尝试救一下:
                # 做一些特殊的对应，因为有的字样只有可能出现在某些特殊的内容中，比如 '外中'
                special_map = {'外中': '对外中医', '外综': '对外综合', '利中': '非营利中医医院',
                               '性医院': '综合性医院', '性医疗': '非营利性医疗机构'
                               }
                text_copy = text
                for sp in special_map:
                    if sp in text_copy:
                        text_copy = special_map[sp]
                        break
                if text_copy != text:
                    res_2 = bk_tree.medical_institution_type().search_one(text_copy, search_dist=1, min_len=2)

            if res is None and res_2 is None:
                medical_institution_type_item.content = text
                medical_institution_type_item.scores = [0]
            else:
                if res is not None:
                    medical_institution_type_item.content = res
                elif res_2 is not None:
                    medical_institution_type_item.content = res_2

                medical_institution_type_item.scores = [1]
                if text != res:
                    logger.debug('medical_institution_type bk_tree:')
                    logger.debug('\tOrigin: {}'.format(text))
                    logger.debug('\tItem in tree: {}'.format(res))

    def _bk_tree_medical_insurance_type(self, structure_items, fg_items):
        medical_insurance_type_item = structure_items.get('medical_insurance_type', None)
        if medical_insurance_type_item is None:
            return

        if medical_insurance_type_item.content:
            text = medical_insurance_type_item.content.replace('医保类型:', '')
            text = text.replace('医保类型', '')
            text = text.replace('医保类', '')
            text = text.replace('医疗机构', '')
            res = bk_tree.medical_insurance_type().search_one(text,
                                                              search_dist=1,
                                                              min_len=2)
            # 对长文本，使用 搜索距离为1有时候难以获得好的搜索结果:
            if res is None and len(text) > 8:
                # 再捞一下
                res = bk_tree.medical_insurance_type().search_one(text,
                                                                  search_dist=2,
                                                                  min_len=2)
            if res is None:
                # 尝试使用非结构化的方法进行搜寻
                node_items = fg_items['medical_insurance_type'].node_items_backup
                config = {'left': ['医保类型', '医疗机构类型'],
                          'right': ['社会保障卡号'],
                          'up': None,
                          'down': None
                          }
                search_res = NodeItemGroup.get_possible_node(node_items, config, thresh_x=8, thresh_y=4, match_count=2)
                if search_res:
                    search_res = [res[0] for res in search_res]
                    bk_tree_search_res = []
                    for idx in range(len(search_res)):
                        new_res = bk_tree.medical_insurance_type().search_one(search_res[idx], search_dist=2, min_len=2)
                        if new_res:
                            bk_tree_search_res.append(new_res)

                    if bk_tree_search_res:
                        search_res = max(bk_tree_search_res, key=lambda x: len(x))
                        medical_insurance_type_item.content = search_res
                        medical_insurance_type_item.scores = [1]
                else:
                    return

            else:
                medical_insurance_type_item.content = res
                medical_insurance_type_item.scores = [1]
                if text != res:
                    logger.debug('medical_insurance_type bk_tree:')
                    logger.debug('\tOrigin: {}'.format(text))
                    logger.debug('\tItem in tree: {}'.format(res))
                    logger.debug('\tItem in tree: {}'.format(res))

    def _get_receiptmoney_from_amountinwords(self, structure_items, fg_items):
        """
        在大多数发票上 receiptmoney 和 amountinwords 的值应该是一样的
        :param structure_items:
        """
        receiptmoney_item = structure_items.get('receiptmoney', None)
        amountinwords_item = structure_items.get('amountinwords', None)

        if receiptmoney_item is None or amountinwords_item is None:
            return

        if amountinwords_item.content:
            receiptmoney_item.content = amountinwords_item.content
            receiptmoney_item.scores = amountinwords_item.scores
        else:
            amountinwords_item.content = receiptmoney_item.content
            amountinwords_item.scores = receiptmoney_item.scores

    def _bk_tree_summary_charges(self, structure_items):
        summary_charges = structure_items.get('summary_charges', None)
        if summary_charges is not None:
            for item_content in summary_charges.content:
                res = bk_tree.summary_charge_item_name().search_one(item_content.name.val,
                                                                    min_len=1,
                                                                    search_dist=2)
                if res is not None:
                    item_content.name.val = res

    def _medical_tmpl_post_proc(self, structure_items, fg_items):
        """
        :param structure_items: dict[StructureItem]
        :return:
        """
        self._bk_tree_summary_charges(structure_items)

        self._get_receiptmoney_from_amountinwords(structure_items, fg_items)

        self._bk_tree_medical_insurance_type(structure_items, fg_items)

        self._tmpl_post_guess_gender_from_name(structure_items)

        return structure_items

    def search_start_day_by_serial_number(self, fg_items, img):
        serial_numbers_pos_node = fg_items['business_serial_no'].get_passed_nodes()

        if not serial_numbers_pos_node:
            return None

        most_possible_nodes = max(list(serial_numbers_pos_node.values()),
                                  key=lambda x: len(str_util.only_keep_continue_money_char(x.text, return_first=False)))

        most_possible_nodes.text = str_util.only_keep_continue_money_char(most_possible_nodes.text, return_first=False)
        if not most_possible_nodes.text:
            return None
        serial_numbers_pos = most_possible_nodes.bbox

        # 将其下移一格
        if len(most_possible_nodes.text) > 20:
            width_pad = 1
        elif len(most_possible_nodes.text) > 15:
            width_pad = 1.5
        elif len(most_possible_nodes.text) > 10:
            width_pad = 2
        else:
            width_pad = 2.5
        possible_rect = serial_numbers_pos.get_offset_box(row_offset=1, height_ratio=1.3, width_ratio=width_pad)
        xmin, ymin, xmax, ymax = possible_rect.rect
        roi_img = img[ymin:ymax, xmin:xmax]
        crnn_res, crnn_scores = crnn_util.run_number_space(img, [xmin, ymin, xmax, ymax])

        import cv2
        cv2.imwrite('/Users/xuan/Documents/project/structuring/tmp/viz_res/test_img/{}.jpg'.format(
            most_possible_nodes.text + '_' + str(crnn_res)), roi_img)

    def _tmpl_post_guess_date_from_start_end_stay(self, structure_items, fg_items, img):
        start = structure_items['hospitalstartdate']
        end = structure_items['hospitalenddate']
        stay = structure_items['hospitalstay']
        ad = structure_items['admissiondate']

        # assert and rerecognization
        # 如果start ， end ， stay 不能很好地校验，就再尝试一下:
        # 调试中，暂时不考虑
        # start_day_res = self.search_start_day_by_serial_number(fg_items, img)

        # 首先，根据start ， end ，ad 进行合理的推断
        # convert all them to datetime

        if start.content and end.content and ad.content:
            date_list = [start.content, end.content, ad.content]
            date_format_list = date_util.convert_list_of_date_to_datetime(date_list)
            # 检查是否要做年份修正
            max_year_diff, max_month_diff = date_util.get_max_diff_of_year_month(date_format_list)
            if max_year_diff > 1:  # or not date_util.judge_date_order(date_format_list):
                date_format_list = date_util.recover_info_by_year(date_format_list, stay.content)

            # 月份修正，比如要同时拥有那几个字段
            if max_month_diff > 2:  # or not date_util.judge_date_order(date_format_list):
                try:
                    date_format_list = date_util.recover_info_by_month(date_format_list, stay.content)
                except:
                    pass

            # 对于这三个都有的情形，还可以做一个start ，end ，ad 的共同调整
            # 首先，对 end < start 的情形
            date_format_list = date_util.predict_date_by_relation(date_format_list, stay.content)
            start.content, end.content, ad.content = date_util.convert_datetime_2_list_of_str(date_format_list)

        date_info = [start, end, stay]

        count_none = 0
        loc_of_none = 0
        count_probability = 0

        for idx, value in enumerate(date_info):
            if value.content is None or value.content == '':
                count_none += 1
                loc_of_none = idx
            if value.to_dict().get('probability', None) is not None:
                count_probability += 1

        # 首先，如果三个信息是匹配的，就不做后面的所有处理，直接返回

        if count_none == 1:
            #  恰好有一个是空的
            if loc_of_none == 2:
                # 说明这个位置是第三个位置
                logger.debug(f'recover stay info from {start.content} and {end.content}')
                stay_days = date_util.get_format_date_diff(start.content, end.content)
                if stay_days >= 0 and stay_days < 400:
                    # 说明剩下的两个字段结构化结果没有问题，做处理
                    stay.content = str(stay_days)
            elif loc_of_none == 1:
                # 说明是没有结尾：
                end_days = date_util.get_shift_date(start.content, int(stay.content))
                end.content = end_days
            else:
                # 说明没有开始时间：
                start_days = date_util.get_shift_date(end.content, -int(stay.content))
                start.content = start_days
            return structure_items

        return structure_items

    def _area_func_medical_charges(self,
                                   item_name: str,
                                   passed_nodes: Dict[str, TpNodeItem],
                                   node_items: Dict[str, TpNodeItem],
                                   img: np.ndarray,
                                   structure_items: Dict[str, StructureItem], *args, **kwargs):
        keys = [
            {"item_name": "summary_charges", "show_name": "大体收费项"},
            {"item_name": "detail_charges", "show_name": "细分收费项"},
        ]
        has_receiptmoney = 'receiptmoney' in structure_items and structure_items['receiptmoney'].content != '' and structure_items['receiptmoney'].content != 0
        kwargs['total_summary_money'] = structure_items['receiptmoney'] if has_receiptmoney else structure_items['amountinwords']

        table_structured = TableStructured(passed_nodes, *args, **kwargs)
        table_structured.structuring()

        summary_charges = table_structured.summary_labels
        detail_charges = table_structured.detailed_labels

        for charges in summary_charges:
            if type(charges.charge.val) == float:
                charges.charge.val = str(charges.charge.val)
        for charges in detail_charges:
            if type(charges.unit_price.val) == float:
                charges.unit_price.val = str(charges.unit_price.val)
            if type(charges.total_price.val) == float:
                charges.total_price.val = str(charges.total_price.val)

        for k in keys:
            item_name = k['item_name']

            if item_name == "summary_charges":
                charges = summary_charges
            elif item_name == "detail_charges":
                charges = detail_charges

            scores = [it.probability for it in charges]
            if item_name not in structure_items:
                si = StructureItem(item_name=item_name,
                                   show_name=k['show_name'],
                                   content=charges,
                                   scores=scores)
                structure_items[item_name] = si
            else:
                structure_items[item_name].content.extend(charges)
                structure_items[item_name].scores.extend(scores)

    def _pre_func_medical_record_no(self,
                                    item_name: str,
                                    passed_nodes: Dict[str, TpNodeItem],
                                    node_items: Dict[str, TpNodeItem],
                                    img: np.ndarray):
        for data in passed_nodes.values():
            text = data.text
            text = str_util.remove_last_dot(text)
            text = str_util.remove_extra_dot(text)
            text = str_util.get_clean_eng(text)
            text = text.upper()
            data.text = text

    def _pre_func_invoice_receipt_no(self,
                                     item_name: str,
                                     passed_nodes: Dict[str, TpNodeItem],
                                     node_items: Dict[str, TpNodeItem],
                                     img: np.ndarray):
        for node in passed_nodes.values():
            roi = node.bbox
            crnn_res, crnn_score = crnn_util.run_number_capital_eng(img, roi)
            node.text = crnn_res
            node.scores = crnn_score
            node.text = str_util.remove_space(node.text)
            node.text = re.sub('[\.,]', '', node.text)
            if node.text.startswith('O') and len(node.text) > 2:
                node.text = '0' + node.text[1:]

    def _pre_func_medical_institution_type(self,
                                           item_name: str,
                                           passed_nodes: Dict[str, TpNodeItem],
                                           node_items: Dict[str, TpNodeItem],
                                           img: np.ndarray
                                           ):

        for data in passed_nodes.values():
            text = data.text
            text = str_util.remove_symbols_except_parentheses(text)
            text = str_util.replace_chinese_parentheses_to_eng(text)
            text = str_util.clean_eng_num_text_to_num(text)
            data.text = text

    def _pre_func_medical_insurance_type(self,
                                         item_name: str,
                                         passed_nodes: Dict[str, TpNodeItem],
                                         node_items: Dict[str, TpNodeItem],
                                         img: np.ndarray
                                         ):
        for data in passed_nodes.values():
            text = data.text
            text = str_util.remove_symbols_except_parentheses(text)
            text = str_util.replace_chinese_parentheses_to_eng(text)
            text = str_util.remove_number_if_body_isnot_num(text)
            data.text = text

    def _pre_func_sex(self,
                      item_name: str,
                      passed_nodes: Dict[str, TpNodeItem],
                      node_items: Dict[str, TpNodeItem],
                      img: np.ndarray
                      ):
        replace_map = {
            '男': ['号', '野'],
            '女': ['车', '备', '轿']
        }

        for node in passed_nodes.values():
            for sex in replace_map:
                if node.text in replace_map[sex]:
                    node.text = sex

    def _pre_func_medical_money(self, item_name: str,
                                passed_nodes: Dict[str, TpNodeItem],
                                node_items: Dict[str, TpNodeItem],
                                img: np.ndarray):
        def has3number(text):
            """
            检查一个text是否有三个连续的text
            :param text:
            :return:
            """
            if not text:
                return False
            res = re.search('[0-9,,,\.]{3,}', text)
            if res:
                return True
            else:
                return False

        # TODO 对 那种退现金...退支票...的数据要做特殊处理0001648365
        for node in passed_nodes.values():
            if has3number(node.text):
                roi = node.bbox
                crnn_res, crnn_scores = crnn_util.run_number_amount(img, roi)
                dis = lcs.llcs(crnn_res, node.text)
                if dis / len(crnn_res) > 0.6:
                    # 认为crnn_res是有效的
                    if str_util.only_keep_money_char(crnn_res.replace(',', '')) != \
                            str_util.only_keep_money_char(node.text.replace(',', '')):
                        logger.debug('re recog {} to crnn , from {} to {}'.format(item_name, node.text, crnn_res))
                    node.text = crnn_res
                    node.scores = crnn_scores

        return self._pre_func_money(item_name, passed_nodes, node_items, img)

    def search_pay_info(self, structure_items, node_items, img):
        def search_and_fill(pair, structure_items, node_items):
            match_bg_regex, key = pair
            medical_bg = None
            for node in node_items.values():
                for rl in match_bg_regex:
                    if re.search(rl, node.text):
                        medical_bg = node
                        break
            # 找到其右侧的一块区域

            if medical_bg:

                filter_rule = lambda x: len(str_util.only_keep_money_char(x)) > 0
                node_in_region = NodeItemGroup.find_node_in_region(medical_bg.bbox,
                                                                   node_items,
                                                                   filter_rule=filter_rule,
                                                                   xoffset=(-1, 3),
                                                                   yoffset=(-2, 2))
                if not node_in_region:
                    structure_items[key].content = ''
                    return
                elif len(node_in_region) == 1:
                    structure_items[key].content = str_util.money_char_clean(node_in_region[0].text)
                else:
                    fg_node = min(node_in_region, key=lambda x: abs(x.bbox.cy - medical_bg.bbox.cy))
                    structure_items[key].content = str_util.money_char_clean(fg_node.text)
                logger.debug('find payinfo {} , value is {}'.format(key, structure_items[key]))
            else:
                structure_items[key].content = '0.00'

        fill_pair = [
            (['^基金支付'], 'medicalpaymoney'),
            (['^个人账户支付'], 'personal_account_pay_money'),
            # (['个人支付金额'], 'personpaymoney'),

        ]

        for pair in fill_pair:
            search_and_fill(pair, structure_items, node_items)
        # 这里加一个特殊的处理逻辑，如果 medicalpaymoney 和 personal_account_pay_money 为0，就直接把personipaymoney 和 大写金额的内容等同出来
        if structure_items['medicalpaymoney'].content and structure_items['personal_account_pay_money'].content:
            if math.isclose(float(structure_items['medicalpaymoney'].content), 0) and math.isclose(
                    float(structure_items['personal_account_pay_money'].content), 0):
                structure_items['personpaymoney'].content = structure_items['amountinwords'].content
                logger.debug(
                    'infer payinfo {} , value is {}'.format('personpaymoney',
                                                            structure_items['personpaymoney'].content))
        else:
            search_and_fill(
                (['个人支付金额'], 'personpaymoney'), structure_items, node_items
            )

    def clear_pay_info(self, structure_items):
        """
        有些北京医疗发票不会打印这些信息
        :param structure_items:
        :return:
        """
        key = [
            'men_zhen_da_e_zhi_fu',
            'tui_xiu_bu_chong_zhi_fu',
            'can_jun_bu_zhu_zhi_fu',
            'dan_wei_bu_chong_xian_zhi_fu',
            'ben_ci_yi_bao_fan_wei_nei_jin_e',
            'lei_ji_yi_bao_fan_wei_nei_jin_e',
            'nian_du_men_zhen_da_e_lei_ji_zhi_fu',
            'personal_account_balance',
            'selfpayone',
            'qi_fu_jin_e',
            'chao_feng_ding_jin_e',
            'selfpaytwo',
            'selfpaymoney',
        ]
        for k in key:
            if k in structure_items:
                del structure_items[k]
