import re
from typing import Dict
from datetime import datetime

import numpy as np

from ...utils import bk_tree
from ...template.tp_node_item import TpNodeItem
from ...utils.crnn import crnn_util
from ...utils import str_util, date_util
from ocr_structuring.utils.logging import logger
from ...utils.node_item_group import NodeItemGroup
from ..post_funcs import max_w_regex

pay_money_item_names = {
    'xian_jin_zhi_fu',
    'personal_account_pay_money',
    'medical_insurance_overall_pay_money',
    'fu_jia_zhi_fu',
    'fen_lei_zi_fu',
    'zi_fu',
    'selfpaymoney',
    'dang_nian_zhang_hu_yu_e',
    'li_nian_zhang_hu_yu_e',
}


def get_label_split_number_text(label_text):
    """
        以其他字符为分隔符，将数字部分分别提取出来
    """
    now_text = ''
    split_text = []
    # div_flag = False
    for c in label_text:
        if str.isnumeric(c):
            now_text += c
        elif len(now_text) > 0:
            split_text.append(now_text)
            now_text = ''
    if len(now_text) > 0:
        split_text.append(now_text)
    return split_text


def get_pay_money_probability(structure_items):
    out = []
    for item_name, si in structure_items.items():
        if item_name not in pay_money_item_names:
            continue
        out.extend(si.scores)

    if len(out) == 0:
        return 1.0

    return float(np.mean(out))


def set_default_value(structure_items, structure_item_name, default_value):
    """
    如果 structure_item 的 content 不会 0.0 或者 None，则设为默认值
    """
    si = structure_items.get(structure_item_name, None)
    if si and si.content:
        si.content = default_value
        si.scores = [get_pay_money_probability(structure_items)]


def get_date_from_text_list(text_list):
    max_year_day = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    max_leapyear_day = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # 是否为闰年
    def is_leapyear(year):
        center_year = (year % 100 == 0)
        return (year % 4 == 0 and (not center_year)) and (center_year and (year % 400 != 0))

    # 从某一位开始的连续四个数字是否是年份
    def get_year(text):
        n = len(text)
        for i in range(n - 3):
            if not text[i:i + 4].isdigit():
                continue
            value = int(text[i:i + 4])
            if 1987 < value < 2088:
                return value, i + 4
        return None, None

    # 文本的开头一位或者两位是否为月份
    def get_month(text):
        n = len(text)
        if n == 0:
            return None, None
        if n == 1:
            candidate_value = text
        else:
            candidate_value = text[:2]
        number = int(candidate_value)
        if 1 <= number <= 12:
            return number, len(candidate_value)
        return None, None

    # 文本的开头一位或两位是否为日期（判断合法性）
    def get_day(text, year, month):
        n = len(text)
        if n == 0:
            return None, None
        if n == 1:
            candidate_value = text
        else:
            candidate_value = text[:2]
        if is_leapyear(year):
            max_day = max_leapyear_day[month]
        else:
            max_day = max_year_day[month]
        number = int(candidate_value)
        if 1 <= number <= max_day:
            return number, len(candidate_value)
        return None, None

    # 从文本列表的某一位开始，是否能够组成一个日期， 返回所有可能结果
    result = []
    total = len(text_list)
    for i in range(total):
        year, month, day = None, None, None
        now_pos = i
        text = text_list[i]
        temp_text_pos = 0
        n = len(text)
        while temp_text_pos < n:
            year, p = get_year(text[temp_text_pos:])
            if year:
                temp_text_pos = p
                break
            else:
                temp_text_pos += 1
        if not year:
            continue
        # print year, temp_text_pos

        if (temp_text_pos >= n) and (now_pos + 1 < total):
            now_pos += 1
            temp_text_pos = 0
            text = text_list[now_pos]
            n = len(text)
        month, p = get_month(text[temp_text_pos:])
        if not month:
            continue
        temp_text_pos += p
        # print month, temp_text_pos

        if (temp_text_pos >= n) and (now_pos + 1 < total):
            now_pos += 1
            temp_text_pos = 0
            text = text_list[now_pos]
            n = len(text)
        day, p = get_day(text[temp_text_pos:], year, month)
        # print text[temp_text_pos:]
        if not day:
            continue
        result.append(datetime(year=year, month=month, day=day))
    return result


def get_best_date(date_list, map_key=None):
    # 从可能的时间中选一个最靠晚的时间
    now = datetime.now()
    res = None
    min_value = None
    for date in date_list:
        if map_key and (not date[map_key]):
            continue
        if (not map_key) and (not date):
            continue
        if map_key:
            real_date = date[map_key]
        else:
            real_date = date
        if min_value is None or now - real_date < min_value:
            min_value = (now - real_date)
            res = date
    return res


def get_valid_date(date_list):
    # V1_2_V3: 判断是否有时间超过当前时间，这个逻辑可以添加到 v3 的日期有效性判断中
    # 获取本地时间（判断是否有时间超过当前时间）
    now = datetime.now()
    res = []
    for date in date_list:
        if not date['date']:
            continue
        if now <= date['date']:
            continue
        res.append(date)
    return res


def date_label_cmp_func(a, b):
    y1 = a['label'][2]
    y2 = b['label'][2]
    return y2 - y1


# noinspection PyMethodMayBeStatic
class ShanghaiInvoiceMixin:
    def _pre_func_shanghai_zhuyuan_hospital_stay_no(self,
                                                    item_name: str,
                                                    passed_nodes: Dict[str, TpNodeItem],
                                                    node_items: Dict[str, TpNodeItem],
                                                    img: np.ndarray):
        for it in passed_nodes.values():
            if it.text.startswith('1700') or it.text.startswith('1600') or it.text.startswith('1400'):
                # 经过区域过滤后，社保号容易和发票号弄混，这里把发票的节点 clear 掉
                it.clear()
                continue
            it.text = re.sub('[oO]', '0', it.text)
            it.text = re.sub('[IT]', '1', it.text)
            if not it.text.startswith('B'):
                it.text = re.sub('[B]', '8', it.text)

    def _pre_func_shanghai_social_security_no(self,
                                              item_name: str,
                                              passed_nodes: Dict[str, TpNodeItem],
                                              node_items: Dict[str, TpNodeItem],
                                              img: np.ndarray):
        for it in passed_nodes.values():
            if it.text.startswith('1700') or it.text.startswith('1600') or it.text.startswith('140'):
                # 经过区域过滤后，社保号容易和发票号弄混，这里把发票的节点 clear 掉
                it.clear()
                continue
            it.text = re.sub('[oO]', '0', it.text)
            it.text = re.sub('[I]', '1', it.text)
            if not it.text.startswith('B'):
                it.text = re.sub('[B]', '8', it.text)

    def _pre_func_shanghai_paymoney_crnn(self,
                                         item_name: str,
                                         passed_nodes: Dict[str, TpNodeItem],
                                         node_items: Dict[str, TpNodeItem],
                                         img: np.ndarray):
        for node in passed_nodes.values():
            if not str_util.contain_continue_nums(node.text, 1):
                continue

            if node.bbox.height > node.bbox.width:
                continue

            crnn_res, scores = crnn_util.run_shanghai_paymoney(img, node.bbox)

            if crnn_res != node.text:
                logger.debug('item_name: {}:'.format(item_name))
                logger.debug('\tOrigin: {}'.format(node.text))
                logger.debug('\tCRNN: {}'.format(crnn_res))

            if crnn_res is not None:
                node.text = crnn_res
                node.scores = scores

    def _post_func_shanghai_zhuyuan_hospitalstartdate(self,
                                                      item_name: str,
                                                      passed_nodes: Dict[str, TpNodeItem],
                                                      node_items: Dict[str, TpNodeItem],
                                                      img: np.ndarray):
        return self._shanghai_zhuyuan_start_end_date(item_name, passed_nodes, node_items, img, split_idx=0)

    def _post_func_shanghai_zhuyuan_hospitalenddate(self,
                                                    item_name: str,
                                                    passed_nodes: Dict[str, TpNodeItem],
                                                    node_items: Dict[str, TpNodeItem],
                                                    img: np.ndarray):
        return self._shanghai_zhuyuan_start_end_date(item_name, passed_nodes, node_items, img, split_idx=1)

    def _shanghai_zhuyuan_start_end_date(self,
                                         item_name: str,
                                         passed_nodes: Dict[str, TpNodeItem],
                                         node_items: Dict[str, TpNodeItem],
                                         img: np.ndarray,
                                         split_idx=0):
        """
        住院日期的结果中可能包含的输入情况：
        - 2017.0933上午到201_09.16上午：
            - split_idx==0 表示仅保留'到'之前的字符
            - split_idx==1 表示仅保留'到'之值的字符
        """
        for it in passed_nodes.values():
            if not str_util.contain_continue_nums(it.text, num_count=1):
                it.text = ''

            if str_util.count_max_continue_nums(it.text) > 6:
                it.text = ''

        passed_nodes, _ = NodeItemGroup.remove_overlap(passed_nodes, ioo_thresh=0.8)

        split_texts = ['至', '到']
        for it in passed_nodes.values():
            for st in split_texts:
                if st in it.text:
                    it.text = it.text.split(st)[split_idx]
                    break

        nodes = NodeItemGroup.sort_by_x(passed_nodes)

        res = ''
        for it in nodes:
            if str_util.contain_continue_nums(it.text, num_count=15):
                it.text = ''
            res += it.text
            it.text = ''

        nodes[0].text = res

        return self._post_func_shanghai_admissiondate(item_name, passed_nodes, node_items, img)

    def _post_func_shanghai_admissiondate(self,
                                          item_name: str,
                                          passed_nodes: Dict[str, TpNodeItem],
                                          node_items: Dict[str, TpNodeItem],
                                          img: np.ndarray):
        # TODO: 这里的代码从结构化 v1 date_spliter 中获得，需要 review 和改进
        # TODO: 参考 https://github.com/scrapinghub/dateparser 写一个 dateparser
        candidate_date_list = []
        for node in passed_nodes.values():
            number_texts = get_label_split_number_text(node.text)
            text = ''.join(number_texts)
            if len(text) >= 6:
                candidate_date_list.append({'label': node.text,
                                            'text': text,
                                            'split_text': number_texts})

        date_res_list = []
        for item in candidate_date_list:
            date_list = get_date_from_text_list(item['split_text'])
            date = get_best_date(date_list)
            date_res_list.append({'label': item['label'], 'date': date})

        date_res_list = get_valid_date(date_res_list)
        result = get_best_date(date_res_list[:1], 'date')

        if result:
            result_label = [item for item in result['label']]
            result_label[0] = result['date'].strftime('%Y-%m-%d')
        else:
            result_label = None

        if result_label and len(result_label) != 0:
            # TODO: 获得更准确的 scores
            return result_label[0], NodeItemGroup.cal_mean_score(passed_nodes)
        else:
            for it in candidate_date_list:
                res = date_util.get_format_data_from_crnn_num_model_res(it['text'])
                if res and date_util.is_legal_format_date_str(res):
                    return res, NodeItemGroup.cal_mean_score(passed_nodes)

    def _post_func_shanghai_hospital_name(self,
                                          item_name: str,
                                          passed_nodes: Dict[str, TpNodeItem],
                                          node_items: Dict[str, TpNodeItem],
                                          img: np.ndarray):
        """
        上海发票的医院名可能出现在左上角和右上角，这里要保证如果 bk tree 没有查到医院名称时返回的 None
        如果返回的是 None, 在 fg_item 中会使用第二个 area 重新找一遍
        """
        nodes = sorted(passed_nodes.values(), key=lambda x: x.bbox.cy)

        def _pre_proces(text: str) -> str:
            # 特判：医院名文字的间距可能比较大，导致中间有空格，这里将空格移除
            text = text.replace('_', '')

            # 特判：如果医院名在左上角，很可能最后会跟着发票标题（上海市）的`上`字，这一把 `上` 字排除
            if text and text[-1] == '上':
                text = text[:-1]
            return text

        ignores_texts = {'市', '诊', '收', '费', '票', '据'}

        # 先 join 校正
        # 示例：
        # GT：第十人民医院同济大学附属第十人民医院。
        # GT 在发票上分为两行，第一行为 第十人民医院，第二行为 同济大学附属第十人民医院
        # 这两行都在在 bktree list 中，所以先要 join 校正再单行校正
        ret = ''
        scores = []
        for it in nodes:
            # 上海门诊的医院名如果在右上角可能会把某些其他字也包含进来，这里不进行 join
            if it.text in ignores_texts:
                continue
            if '流水号' in it.text:
                continue

            ret += it.text
            scores.extend(it.scores)
        ret = _pre_proces(ret)

        search_res = self._hospital_name_search_one(ret)

        if search_res is not None:
            return search_res, [1]

        # 单个检测框 bk_tree 查找医院名
        for it in nodes:
            s = _pre_proces(it.text)
            search_res = self._hospital_name_search_one(s)
            if search_res:
                return search_res, [1]

        # 如果前面都没有 return，说明基于模板的方式没有找到医院名，这里再通过非模板的方式做
        key_words = [
            '口腔',
            '医院',
            '附属',
            '福利会',
            '保健院',
            '妇幼',
            '儿科医院',
            '中医医院',
            '人民医院',
            '卫生服务中心',
            '社区服务中心',
            '医学院',
            '中西医',
            '中西医结合',
            '牙病防治所',
            '医药大学',
            '人民医',
            '浦东新区',
            '中医',
            '同仁',
            '同济',
            '中心医院',
            '中心医',
            '眼牙病防治',
            '牙病防治',
            '妇婴',
            '卫生临床中心',
            '传染病',
            '卫生中心',
            '咨询中心',
            '上海市'
        ]
        candidate_nodes = {}
        for node in node_items.values():
            for key_word in key_words:
                if key_word in node.cn_text:
                    if '机构' in node.cn_text:
                        continue

                    # 过滤掉医疗机构类型
                    bk_ret = bk_tree.medical_institution_type().search_one(node.cn_text, 2, min_len=3)
                    if bk_ret is not None:
                        continue
                    candidate_nodes[node.uid] = node
        candidate_nodes = NodeItemGroup.sort_by_y(candidate_nodes)
        hospital_name = ''.join([it.cn_text for it in candidate_nodes])
        search_res = self._hospital_name_search_one(hospital_name)
        if search_res:
            return search_res, [1]

    def _hospital_name_search_one(self, text):
        """
        根据输入长度的不同取不同的 search_dist
        """
        if len(text) < 4:
            return None

        if 4 <= len(text) < 6:
            search_dist = 2
        elif 6 <= len(text) < 10:
            search_dist = 3
        else:
            search_dist = 4

        return bk_tree.shanghai_hospital_name().search_one(text, search_dist=search_dist, min_len=4)

    def _bk_tree_shanghai_hospital_name(self, structure_items):
        hospital_name_item = structure_items.get('hospital_name', None)
        if hospital_name_item is None:
            return

        if not hospital_name_item.content:
            return

        search_res = bk_tree.shanghai_hospital_name().search_one(hospital_name_item.content, search_dist=4)

        # 平安业务要求，如果医院名没有在库中查到，内容和置信度设置为空
        # TODO: 拆分到结构化后一个模块中
        if search_res is None:
            hospital_name_item.set_none()
        else:
            hospital_name_item.content = search_res

    def _tp_post_check_shanghai_social_no_with_receiptno(self, structure_items):
        """
        社会保障号码在发票号的下方，出的结果中可能为发票号的结果，检查社会保障号码是否和发票号一致，如果一样则设为空
        该方法可以提高社会保障号码的 keep acc
        TODO: 可能的问题，receiptno 和 social_security_no 都给了 social_security_no 的结果，其实是 receiptno 错了，这一步会降低 acc，在有了上海的标注数据以后测试一下
        """
        receiptno = structure_items.get('receiptno', None)
        social_security_no = structure_items.get('social_security_no', None)

        if receiptno is None or social_security_no is None:
            return

        if receiptno.content == social_security_no.content:
            social_security_no.set_none()

    def _tp_post_check_paymoney_by_medical_insurance_type(self, structure_items):
        """
        特判：如果医保类型是自费，则上海门诊左下角的金额有如下特性：
        - 个人账户支付、医保统筹支付、附加支付、当年账户余额、历年账户余额都应该为 空 或 0.00
        """
        medical_insurance_type_item = structure_items.get('medical_insurance_type', None)
        if medical_insurance_type_item is None:
            return

        if not medical_insurance_type_item.content:
            return

        if '自费' in medical_insurance_type_item.content:
            # 这里设为 空 或者 0.0 的依据是根据在测试集上跑出来的结果
            # TODO: 确认最后是否要添加这个逻辑
            set_default_value(structure_items, 'personal_account_pay_money', '0.00')
            set_default_value(structure_items, 'medical_insurance_overall_pay_money', '0.00')
            set_default_value(structure_items, 'fu_jia_zhi_fu', '0.00')

            set_default_value(structure_items, 'dang_nian_zhang_hu_yu_e', '0.00')
            set_default_value(structure_items, 'li_nian_zhang_hu_yu_e', '0.00')
