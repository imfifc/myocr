import copy
import re
from itertools import product
from typing import List, Tuple

from ocr_structuring.core.non_template.utils.bol_utils.table_items.table_extractor.parse_table_config import load_cfg
from ocr_structuring.core.non_template.utils.bol_utils.text_extraction.multiline_text_extraction import \
    extract_text_from_multiline_text
from ocr_structuring.core.non_template.utils.bol_utils.utils.structures import HeaderRequirement
from ocr_structuring.utils.logging import logger
from . import table_process_utils
from .parse_table_config import ContentConfig
from .parse_table_config import load_table_cfg


class TableExtractor:
    def __init__(self, cfg_path):
        self.cfg = load_cfg(cfg_path)

    def __init_for_spec_company(self, header_type, fields, rows, row_of_blocks, img, company_name):

        self.company_name = company_name
        self.header_type = header_type
        self.fields = fields
        self.rows = rows
        self.row_of_blocks = row_of_blocks
        self.img = img
        regex_config, process_config_map, fetch_on_other_config = load_table_cfg(self.cfg, company_name)

        self.header_config_map = self.build_header_config_map(copy.deepcopy(regex_config))
        self.fetch_on_other_field_map = self.filter_fetch_on_other_field_map(copy.deepcopy(fetch_on_other_config))
        self.process_config_map = process_config_map

    def build_header_config_map(self, header_config_map):
        new_header_config_map = {}
        for key, value in header_config_map.items():
            new_header_config_map.update({self.header_type[key]: value})
        return new_header_config_map

    def build_fetch_on_other_field_map(self, fetch_on_other_field_map):
        def _parse_header_req(headreq):
            headreq = field_contraint.header_requirement
            if isinstance(headreq, str) or (isinstance(headreq, (list, tuple)) and len(headreq) == 1):
                headreq = self.header_type[headreq]
            else:
                headreq = (self.header_type[headreq[0]], headreq[1])
            headreq = HeaderRequirement(headreq)
            return headreq

        new_map = {}
        for key, value in fetch_on_other_field_map.items():
            new_key = self.header_type[key]
            for idx, config in enumerate(value):

                htype = self.header_type[config.fetch_constraint.fetch_field]

                config = config._replace(fetch_constraint=config.fetch_constraint._replace(fetch_field=htype))
                for fidx, field_contraint in enumerate(config.field_constraints):
                    headreq = _parse_header_req(field_contraint.header_requirement)
                    config.field_constraints[fidx] = field_contraint._replace(header_requirement=headreq)
                if config.other_fields_check.header_requirements:
                    for hidx, headreq in enumerate(config.other_fields_check.header_requirements):
                        config.other_fields_check.header_requirements[hidx] = _parse_header_req(headreq)
                value[idx] = config

            new_map.update({new_key: value})

        return new_map

    def filter_fetch_on_other_field_map(self, fetch_on_other_field_map):
        fetch_on_other_field_map = self.build_fetch_on_other_field_map(fetch_on_other_field_map)
        keys = list(fetch_on_other_field_map.keys())
        for header_type in keys:
            header_configs = fetch_on_other_field_map[header_type]
            useful_cfg = []
            for header_config in header_configs:
                all_satisfy = []
                for idx, header_req in enumerate(header_config.field_constraints):
                    status, fid = header_req.header_requirement.parse_header_requirement(self.fields)
                    if status:
                        header_config.field_constraints[idx] = header_req._replace(fetch_fid=list(fid)[0])
                    all_satisfy.append(status)
                for idx, header_req in enumerate(header_config.other_fields_check.header_requirements):
                    status, fid = header_req.parse_header_requirement(self.fields)
                    all_satisfy.append(status)
                if all(all_satisfy):
                    useful_cfg.append(header_config)
            if len(useful_cfg) == 0:
                del fetch_on_other_field_map[header_type]
            else:
                fetch_on_other_field_map[header_type] = useful_cfg

        return fetch_on_other_field_map

    def extract_lines(self, header_type, fields, rows, row_of_blocks, img, header_need_extract, company_name=None):
        """
        逐步遍历每个row_of_block ， 获得信息
        :param : header_need_extract 期望抽取的信息
        :return:
        """
        self.__init_for_spec_company(header_type, fields, rows, row_of_blocks, img, company_name)

        header_need_extract = {self.header_type[htype] for htype in header_need_extract}
        rows = []
        for row in self.row_of_blocks:
            useful_info = self.extract_row_info(row, header_need_extract)

            if len(useful_info) > 0:
                rows.append(useful_info)
        return rows

    def extract_row_info(self, row, header_need_extract):
        type_content_map = {field.header_type: field for fid, field in row.items() if
                            field.header_type != self.header_type.OTHER}
        useful_info, type_content_map, header_need_find_in_other_field = self.extract_row_info_in_field(
            type_content_map, header_need_extract)

        useful_info_in_other_field = self.extract_row_info_in_other_field(row, header_need_find_in_other_field)
        useful_info.update(useful_info_in_other_field)
        return useful_info

    def extract_row_info_in_field(self, type_content_map, header_need_extact):
        """
        对每个字段，从这个字段内部提取相应的信息
        :param row: Dict[str,Block] 对应一行的信息
        :param header_need_extact: 需要提取的字段
        :return:
        """

        extract_map = {}

        header_need_find_in_other_field = []
        for header_type in header_need_extact:
            header_config = self.get_header_config(header_type)
            block = type_content_map.get(header_type, None)
            if block is None:
                # 没有找到和自己的表头相关的信息
                header_need_find_in_other_field.append(header_type)
                continue
            block = self.pre_process(block, header_type)
            status, content = self.extract_info(block, header_config)
            if not status:
                # 在自己的表头范围内没有找到相应的内容
                header_need_find_in_other_field.append(header_type)
            else:
                content = self.post_process(content, header_type)
                if not content:
                    # 如果清理后为空，不加入最后的结果当中
                    continue
                extract_map[header_type] = content
        return extract_map, type_content_map, header_need_find_in_other_field

    def extract_row_info_in_other_field(self, row, header_need_find_in_other_field):
        # 遍历useful_info ，如果要提取的信息都已经有了，则直接返回

        usefulinfo_in_other_field = {}
        for header_type in header_need_find_in_other_field:
            if header_type not in self.fetch_on_other_field_map:
                # 说明没有 相关的配置，直接放过
                continue
            # 根绝表头设置和内容要求捞一下
            header_configs = self.fetch_on_other_field_map[header_type]
            for header_config in header_configs:
                # 拿到对应的config
                status, content = self.fetch_on_other_field(header_type, row, header_config)
                if status:
                    content = self.post_process(content, header_type)
                    usefulinfo_in_other_field.update({header_type: content})
                    break

        return usefulinfo_in_other_field

    def fetch_on_other_field(self, header_type, row, header_config):
        """

        :param header_type: 需要提取的类型
        :param type_content_map:
        :param header_config:
        :return:
        """
        # 对row里面的每个block 获取其fid 信息

        # 根据field_req 找到fid
        # 需要把每个fid ， rid 信息记录到node和block 当中，block 需要记录fid 信息

        # 首先检查header_req 是否是满足对，如果不满足，直接跳过
        possible_info = []
        for header_req in header_config.field_constraints:
            fid = header_req.fetch_fid
            if not fid:
                return False, ''
            reference_block = row.get(fid, None)  # 获取对应的block 数据
            if reference_block is None:
                return False, ''
            possible_info.append((self.fields[fid].header.head_type, header_req.regex_list, reference_block))

        # 说明header_config 要求的表头都
        block_comb_nodes = []  # 存放所有满足条件的组合
        block_comb_types = []
        for block_header_type, block_regex_req, block in possible_info:
            possible_nodes = []
            for node in block.node_items:
                for regex in block_regex_req:
                    if re.search(regex, node.text, re.IGNORECASE):
                        possible_nodes.append(node)
                        break
            # if not possible_nodes:
            #     # 只要有一个条件没有找到对应的内容，直接返回没找到
            #     return False , ''
            block_comb_types.append(block_header_type)
            block_comb_nodes.append(possible_nodes)

        possible_result = []
        for nodes_comb in product(*block_comb_nodes):
            if len(set([node.row_order for node in nodes_comb])) != 1:
                continue
            possible_result.append(dict(zip(block_comb_types, nodes_comb)))

        if not possible_result:
            return False, ''

        # 目前只取第一组
        possible_result = possible_result[0]
        fetch_field = header_config.fetch_constraint.fetch_field
        fetch_regex = header_config.fetch_constraint.fetch_regex
        org_text = possible_result[fetch_field].text
        for regex in fetch_regex:
            search_res = re.search(regex, org_text, re.IGNORECASE)
            if search_res:
                return True, org_text[search_res.start():search_res.end()]

        return False, ''

    def pre_process(self, block, header_type):
        """
        可能会需要做一些内容的重新识别一类的事情
        :param block:
        :param header_type:
        :return:
        """
        pre_process_func = getattr(self, 'pre_process_' + header_type.name.lower(), None)
        if pre_process_func is not None:
            block = pre_process_func(block, header_type)
        return block

    def post_process(self, content, header_type):
        # 统一对所有内容进行一部分处理
        content = self.post_process_common(content)
        post_process_func = getattr(self, 'post_process_' + header_type.name.lower(), None)
        if post_process_func is not None:
            content = post_process_func(content, header_type)

        # 在这里做一些清理工作
        content = re.sub('\n_{1,}', '', content)
        if self.process_config_map.get(header_type.name, None) is not None:
            post_process_func_for_special = self.process_config_map[header_type.name]['post_process_func']
            if isinstance(post_process_func_for_special, str):
                func = getattr(table_process_utils, post_process_func_for_special, None)
                if func is not None:
                    content = func(content)
            if isinstance(post_process_func_for_special, list):
                for special_func in post_process_func_for_special:
                    func = getattr(table_process_utils, special_func, None)
                    if func is not None:
                        content = func(content)
        return content

    def post_process_common(self, content):
        # 对dimension 信息进行剔除
        content = re.sub("[0-9]{2,}[\*~_][0-9]{2,}[\*~_][0-9]{2,}", '_', content)
        return content

    def extract_info(self, block, header_config: ContentConfig):
        block_content = '\n'.join(block.content)

        extract_result = extract_text_from_multiline_text(
            block_content,
            start_key_words=header_config.start_key_words,
            end_key_words=header_config.end_key_words,
            start_exps=header_config.start_exps,
            end_exps=header_config.end_exps,
            start_filter_exps=header_config.start_filter_exps,
            filter_exps=header_config.filter_exps
        )

        if not extract_result[0]:
            # 如果过滤条件设置的有问题导致所有内容都被过滤，就直接输出原始结果
            logger.info('block content {} is filtered to empty !!'.format(block_content))
            if extract_result[1]:
                return True, block_content
            return False, ''
        return True, extract_result[0]

    def get_header_config(self, header_type):
        header_config = self.header_config_map.get(header_type, ContentConfig())
        return header_config

    @staticmethod
    def remove_prefix(content, prefix_rule):
        for idx, line in enumerate(content):
            for prefix in prefix_rule:
                prefix_loc = re.search(prefix, line)
                if not prefix_loc:
                    continue
                content[idx] = line[prefix_loc.end():].strip('_')
                break
        return content

    @staticmethod
    def remove_suffix(content, suffix_rule):
        for idx, line in enumerate(content):
            for suffix in suffix_rule:
                suffix_loc = re.search(suffix, line)
                if not suffix_loc:
                    continue
                content[idx] = line[:suffix_loc.start()].strip('_')
                break
        return content

    @staticmethod
    def replace_substring(content: List[str], replace_map: List[Tuple[str, str]], recover_text=False):
        # 常用错误替换
        for idx, text in enumerate(content):
            for regex, target_text in replace_map:
                # print('debug quantity', regex, content)
                content[idx] = re.sub(regex, target_text, content[idx])
        if not recover_text:
            return content
        else:
            return '\n'.join(content)

    @staticmethod
    def get_first_format_string(content: str, format_regex):
        # 截取第一个正常的表达式
        # 一次只支持一种表达式

        search_format = re.search(format_regex, content)
        if search_format:
            content = content[search_format.start():search_format.end()]
            content = re.sub('_{2,}', '_', content)
        return content
