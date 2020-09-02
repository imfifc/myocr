import re
from typing import List, Union

from ocr_structuring.core.non_template.utils.bol_utils.utils.structures import ElementTextType, HeaderRequirement
from ocr_structuring.utils.logging import logger


class RegexRule:
    def __init__(self, regexs: List[Union[ElementTextType, str]],
                 adaptive_fields: List[HeaderRequirement],
                 unexpected_content: List[List[str]] = []
                 ):
        self.regexs = regexs  # 表明需要的正则表达式
        self.adaptive_fields = adaptive_fields  # 表明正则表达表达式需要适应的field
        self.unexpected_content = unexpected_content

    def find_valid_keyrow(self, node_info, fields, rows, header_group):
        # 在这里寻找合理的keyrow
        # 完成header_group 的筛选

        # 筛选出regex 涉及到的列
        used_fid_set = []
        for field in self.adaptive_fields:
            satisfy_status, fid_set = field.parse_header_requirement(fields)
            if not satisfy_status:
                continue
            used_fid_set.append(fid_set)
        # 获取有效的fid
        if not used_fid_set:
            return False, {}
        selected_fid = set.union(*used_fid_set)

        if len(selected_fid) == 0:
            # 说明对于这次的数据，不存在一个列满足这条规则对表头的要求
            return False, {}

        # 首先，去除掉哪些列数不满足条件的行
        filtered = node_info
        # filtered = node_info[node_info.num_fid_in_row >= len(self.adaptive_fields)]
        # if self.check_empty(filtered):
        #     return False, {}
        # 选出规则所需要考虑的列的内容
        filtered = filtered[filtered.fid.isin(selected_fid)]
        if self.check_empty(filtered):
            return False, {}

        # 对这些列判断字符和字符类型是否满足要求
        filtered = filtered[filtered.apply(self.map_func, axis=1)]
        if self.check_empty(filtered):
            return False, {}

        key_row = set(filtered.row_order.unique())

        for _, data in filtered.groupby('row_order'):
            content = '--'.join(data.text.to_list())
            logger.info('check row {} by {}'.format(content, self.regexs))

        # 利用unexpected 设置的内容，对key_row 进行过滤
        after_filter_key_row = []
        for krow in key_row:
            node_in_this_row = node_info[node_info.row_order == krow]
            matched_unexpected = False
            for regexes in self.unexpected_content:
                matched_all = True if len(regexes) > 0 else False
                for regex in regexes:
                    matched_filter_rule = node_in_this_row[
                        node_in_this_row.text.map(lambda x: re.search(regex, x, re.IGNORECASE) is not None)]
                    if matched_filter_rule.shape[0] == 0:
                        # 说明没有元素符合这个正则
                        matched_all = False
                if matched_all:
                    matched_unexpected = True
            if matched_unexpected:
                continue
            else:
                after_filter_key_row.append(krow)
        key_row = set(after_filter_key_row)

        return True, key_row

    def map_func(self, record):
        text_type = record.text_type
        text = record.text

        check_satisfy = False
        for regex in self.regexs:
            if isinstance(regex, str) and re.search(regex, text, re.IGNORECASE):
                check_satisfy = True
            if isinstance(regex, ElementTextType) and text_type == regex:
                check_satisfy = True
        return check_satisfy

    def check_empty(self, dataframe):
        if dataframe.shape[0] == 0:
            return True
        return False


class KeyRowConfig:
    def __init__(self, regex_rules: List[RegexRule], header_requirements: List):
        self.regex_rules = regex_rules
        self.header_requirements = header_requirements

    @staticmethod
    def parse_config(config):
        rule_list = []
        for rule in config['rules']:
            header_requirements = [HeaderRequirement(header_req) for header_req in rule['adaptive_fields']]
            regex_rule = RegexRule(rule['content_requirement'], header_requirements, rule.get('unexpected_content', []))
            rule_list.append(regex_rule)
        other_header_requirements = [HeaderRequirement(header_req) for header_req in
                                     config.get('other_header_requirement', [])]

        keyrow_config = KeyRowConfig(rule_list, other_header_requirements)
        return keyrow_config

    def parse_key_row(self, node_info, fields, rows, header_group):
        # 首先检查 header_group 当中是否存在符合条件的结果
        if self.header_requirements is not []:
            # 如果设置了表头检查，则必须所有在 requirment 当中的要求都需要被满足
            if not all([header_req.parse_header_requirement(fields)[0] for header_req in
                        self.header_requirements]):
                return False, None

        valid_key_row_set = []
        for regex_rule in self.regex_rules:
            # 遍历所有设计的规则，然后取交集
            finded, keyrow = regex_rule.find_valid_keyrow(node_info, fields, rows, header_group)
            if finded:
                valid_key_row_set.append(keyrow)

        # 取出来的keyrow 应该是满足条件的
        if not valid_key_row_set:
            return False, None
        valid_key_row = set.intersection(*valid_key_row_set)

        if len(valid_key_row) > 0:
            return True, valid_key_row
        return False, valid_key_row


class KeyrowGroup():
    def __init__(self, keyrow_config, company_name=None):
        self.common_config_list, self.special_config_list = self.build_configs(keyrow_config, company_name)

    def build_configs(self, keyrow_config, company_name):
        # 获取正确的config
        useful_config = self.extract_configs(keyrow_config, company_name)
        common_config_list = []
        for common_rule in useful_config['common']:
            common_config_list.append(KeyRowConfig.parse_config(common_rule))
        special_config_list = []
        for special_rule in useful_config.get('special'):
            special_config_list.append(KeyRowConfig.parse_config(special_rule))

        return common_config_list, special_config_list

    def extract_configs(self, keyrow_config, company_name=None):
        # 检查现在的company_name 是否在keyrow_config 当中出现过
        if company_name is not None and keyrow_config['company_config'].get(company_name) is not None:
            config = keyrow_config['company_config'][company_name]
        else:
            config = keyrow_config['common_config']
        return config

    def assign_key_row(self, node_info, fields, rows, header_group):
        """
        # 原则： 遍历所有的config
        # 每条config 包含：
        # rules: 一系列的规律，每个规律包含：
            content_requirement：需要满足的正则表达式
            adaptive_fields ： 要求rule 作用的列： 可能是 headertype ， 可能是内容满足一定正则表达式的header_type
            只要在 adaptive-fields 当中有一个列满足正则，则就认为这一列是关键列
        # other_header_requirement: 要求header_group 当中存在满足所有的 other_header_requirement 的内容

        # common rule 的每一个都要遍历
        # 遍历keyrow 原则：
        # 设置的common_rule 都要在nodeinfo 当中尝试遍历
        # common_rule 当中设置比较通用的 rule ，可能会找到多个关键行
        # 随后，会尝试special rule ，special rule 一般是针对一些特殊情况设置的，
        # 所以 special rule 会设置的比较严格，让表头特别严格的符合情形之后才开始进行内容检查
        :param node_info:
        :param fields:
        :param rows:
        :param header_group:
        :return:
        """
        finded_keyrow = []
        for common_rule in self.common_config_list:
            finded, keyrow_set = common_rule.parse_key_row(node_info, fields, rows, header_group)
            if finded:
                finded_keyrow.append(keyrow_set)
        if len(finded_keyrow) == 0:
            # 一个都没有找到
            return False, None

        keyrow_set = set.union(*finded_keyrow)

        # special rule 只对一部分的行进行处理
        filtered_result = []
        keyrow_info = node_info[node_info.row_order.isin(keyrow_set)]
        for special_rule in self.special_config_list:
            finded, prob_keyrow_set = special_rule.parse_key_row(keyrow_info, fields, rows, header_group)
            if finded:
                filtered_result.append(prob_keyrow_set)
        if not filtered_result:
            # 说明没有一个特殊的规则负责它，可以直接返回
            return True, keyrow_set

        filtered_result = set.union(*filtered_result)
        if self.check_valid_filter_result(filtered_result):
            return True, filtered_result

        else:
            return True, keyrow_set

    def check_valid_filter_result(self, x):
        return True
