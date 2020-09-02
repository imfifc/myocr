import os
import re
import time

import cv2
import numpy as np
import pandas as pd

from ocr_structuring.core.non_template.utils.bol_utils.table_items.table_handler.auto_header_handler import \
    AutoHeadFinder
from ocr_structuring.debugger import variables
from .element_handler import ElementGroup
from .field_handler import FieldGroup
from .line_handler import LineGroup
from ..configs import config_parser
from ...table_items import HeaderItemList


class TableHandler():
    def __init__(self, common_table_config, company_name_config, company_table_config_list):
        # 加载通用配置和公司配置
        self.common_table_config = self.load_cfg(common_table_config)
        self.company_name_config = self.load_cfg(company_name_config)

        # 这里 把company 的cfg 也一次性加载进来，避免每次都需要加载，用来节省读取yaml 使用的时间
        self.company_table_config_list = self.load_company_table_config_list(company_table_config_list)

        self.debug_path = config_parser.parse_debug_path(self.common_table_config)

    @staticmethod
    def load_company_table_config_list(company_table_config_list):
        special_cfg_list = dict()
        for table_config in company_table_config_list:
            key = os.path.basename(table_config)
            if 'yaml' not in key:
                continue
            value = TableHandler.load_cfg(table_config)
            special_cfg_list[key.replace('.yaml', '')] = value
        return special_cfg_list

    @staticmethod
    def load_cfg(cfg_path):
        cfg = config_parser.load_ymal_config(cfg_path)
        return cfg

    def load_header_type(self):
        self.header_type = config_parser.parse_header_type(self.common_table_config)

    def viz_header(self, headers_group, img):
        if self.debug_path is None:
            return
        from tvcore.data.viz import viz_boxes
        boxes = []
        texts = []
        raw_data = []
        for header in headers_group.finded_header:
            content = header.key_node.content
            name = header.name
            type = header.head_type
            boxes.append(header.key_node.bbox.rect)
            texts.append(content + '_' + str(type))
            raw_data.append([str(name) + '_' + str(type), *[int(i) for i in header.key_node.bbox.rect]])
        boxes = np.array(boxes)

        viz_boxes(boxes, img, texts=texts,
                  save_path=os.path.join(self.debug_path, 'viz_header.jpg'),
                  text_color=(0, 0, 255))
        variables.add_group('header', 'header', raw_data)

    def viz_group(self, node_info, node_items, img, key, save_name):
        if self.debug_path is None:
            return
        from tvcore.data.viz import viz_boxes
        color_list = [
            (0, 255, 0),
            (255, 0, 0),
            (0, 0, 255),
            (0, 0, 0),
            (255, 255, 0),
            (255, 0, 255)

        ]
        # img = np.zeros_like(img)
        node_info = pd.DataFrame({'node_id': list(node_info.keys()), key: list(node_info.values())})
        i = 0
        raw_data = []
        for idx, (group_key, data) in enumerate(node_info.groupby(key)):
            i += 1
            bbox = []
            for node_id in data.node_id:
                node = node_items[node_id]
                bbox.append(node.bbox.rect)
                raw_data.append([save_name + str(idx), *[int(i) for i in node.bbox.rect]])
            bbox = np.array(bbox)
            img = viz_boxes(bbox, img, color=color_list[i % len(color_list)], show_detail=False)
        cv2.imwrite(os.path.join(self.debug_path, 'viz_{}.jpg'.format(save_name)), img)
        variables.add_group(save_name, save_name, raw_data)

    def viz_blocks_in_row(self, blocks, img):
        if self.debug_path is None:
            return
        from tvcore.data.viz import viz_boxes
        color_list = [
            (0, 255, 0),
            (255, 0, 0),
            (0, 0, 255),
            (0, 0, 0),
            (255, 255, 0),
            (255, 0, 255)

        ]
        raw_data = []
        count = 1
        for row in blocks:
            for header_type, field_info in row.items():
                count += 1
                bbox = np.array(field_info.bbox.rect).reshape(-1, 4)
                text = [header_type]
                img = viz_boxes(bbox, img, texts=text, color=color_list[count % len(color_list)], show_detail=False)
                raw_data.append([text, *field_info.bbox])

        variables.add_group('block', 'block', raw_data)
        cv2.imwrite(os.path.join(self.debug_path, 'viz_block.jpg'), img)

    def filter_nodes_by_content(self, node_items):
        filtered_nodes = dict()
        for uid, node in node_items.items():
            if re.match('^\*{2,}$', node.text):
                continue
            filtered_nodes[uid] = node
        return filtered_nodes

    def remove_redundant_config(self, common_cfg, spec_company_cfg):
        # 对于 company 在 common cfg 这边如果设置成 空 或者 'ignore' 的情形，
        # 对于 common_cfg 和 spec  company 的相应字段都进行删除
        spec_element_cfg = spec_company_cfg.get('ELEMENT_HANDLER', None)
        common_element_cfg = common_cfg.get('ELEMENT_HANDLER', None)
        if spec_element_cfg is None:
            return common_cfg
        if spec_element_cfg.get('keyrow_config', None) is None:
            return common_cfg

        spec_keyrow_config = spec_element_cfg.keyrow_config
        comm_keyrow_config = common_element_cfg.keyrow_config

        for config_name in ['common_config', 'special_config']:
            if spec_keyrow_config.get(config_name, None) is None:
                continue
            for key in spec_keyrow_config[config_name].copy():
                if isinstance(spec_keyrow_config[config_name][key], str):
                    # 只要是 str ，就同时把两个配置都删掉
                    if comm_keyrow_config[config_name].get(key, None) is not None:
                        del comm_keyrow_config[config_name][key]
                        del spec_keyrow_config[config_name][key]
                    else:
                        del spec_keyrow_config[config_name][key]

        return common_cfg

    def gen_cfg_for_data(self, company_name=None):
        """

        :param company_name: 公司名
        :return:  将公司配置和标准配置进行合并
        """
        if company_name is not None:
            company_rule = self.company_name_config.COMPANY_RULE
            if company_name in company_rule and company_rule[company_name].get('company_config', None) is not None:
                # 有为这个公司设置特殊的操作
                common_cfg = self.common_table_config.clone()

                spec_company_config = company_rule[company_name]['company_config']
                spec_company_config = self.company_table_config_list.get(spec_company_config, None)
                if spec_company_config is None:
                    return common_cfg

                common_cfg = self.remove_redundant_config(common_cfg, spec_company_config)
                common_cfg = config_parser.merge_two_cfg(common_cfg, spec_company_config)
                return common_cfg

        return self.common_table_config.clone()

    def parse_config(self, special_cfg, company_name: str, text_clean_func=None):
        """

        :param special_cfg:
        :param company_name: 传入公司名，是因为很多的表头配置是紧密的和公司相关的，属于公司特殊表头配置
                                则在解析的时候，如果传入了公司信息，则设置了特殊公司的特殊表头就可以被移除掉
        :return:
        """
        header_cfg = config_parser.parse_header_config(special_cfg, self.header_type, company_name)
        pr = config_parser.parse_prime_key(special_cfg, self.header_type)
        header_list = HeaderItemList(self.header_type, header_cfg, pr , text_clean_func)
        keyrow_config = config_parser.parse_keyrow_config(special_cfg, self.header_type)
        filter_config = config_parser.parse_filter_config(special_cfg, self.header_type)
        block_update_config = config_parser.parse_block_update_config(special_cfg)

        return header_list, keyrow_config, filter_config, block_update_config

    def parse_data(self, node_items, img, company_name=None, text_clean_func=None):

        start = time.time()

        self.load_header_type()

        # TODO : 如果company name 是一个enum 类型，则需要将转换成字符串
        # 或者考虑一下以后如果是enum 的情况下，yaml 要怎么配置
        special_cfg = self.gen_cfg_for_data(company_name)
        header_list, keyrow_config, filterrow_config, block_update_config = self.parse_config(special_cfg, company_name,
                                                                                              text_clean_func)

        # TODO 目前只能返回一组表头
        # step 1 ，寻找表头

        header_groups = header_list.search_headers(node_items, img)

        if len(header_groups) == 0:
            return False, None, None, None, None

        for header_group in header_groups:
            if special_cfg.AUTO_FIND_HEADER:
                # 考虑到以后可能会一张图存在多个表头，放在每个表头这里单独做
                header_group = AutoHeadFinder(special_cfg).recheck_header(header_group, node_items)

            self.viz_header(header_group, img)

            # step1 , 过滤表头以下的节点：
            filtered_nodes = header_group.filter_nodes_below_headers(node_items)
            filtered_nodes = self.filter_nodes_by_content(filtered_nodes)

            # step2 对表头往下的部分，分配列信息,获取每个节点属于那个列
            field_group = FieldGroup(special_cfg, header_group)
            fields_info, fields = field_group.assign_fields(filtered_nodes)
            self.viz_group(fields_info, node_items, img, 'field_idx', 'fields')

            # step3 , 对所有的node，分配行信息
            line_group = LineGroup(special_cfg, header_group)
            row_info, rows = line_group.assign_rows(filtered_nodes)

            self.viz_group(row_info, node_items, img, 'row_idx', 'row')
            # step4 , 抽取关于node_items 的各种特征，对行列信息进行合并，整理成Element
            element_group = ElementGroup(special_cfg, self.header_type, header_group, fields, rows, keyrow_config,
                                         filterrow_config,
                                         block_update_config,
                                         node_items)
            # 这里，我对于每个条目称为不同的block
            status, possible_key_row, blocks = element_group.assign_block(row_info, fields_info)
            if not status:
                return False, None, None, None, None
            row_info = {k: v for k, v in row_info.items() if rows[v].order in possible_key_row}
            self.viz_group(row_info, node_items, img, 'row_idx', 'key_row')
            self.viz_blocks_in_row(blocks, img)
            # 第一个True 表示找到了表结构
            return True, fields, rows, blocks, header_group
