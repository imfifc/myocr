from enum import Enum

from yacs.config import CfgNode as CN

from ocr_structuring.core.non_template.utils.multiline_bg_item import MultiHeaderAlign


def set_cfg_node_new_allowed_attr(cfg_node, new_allowed):
    """Set __new_allowed__ to new_allowed and recursively apply the setting
    to all nested CfgNodes.
    """
    cfg_node.__dict__[cfg_node.NEW_ALLOWED] = new_allowed
    # Recursively set new allowed state
    for v in cfg_node.values():
        if isinstance(v, CN):
            set_cfg_node_new_allowed_attr(v, new_allowed=new_allowed)


def merge_two_cfg(cfg1, cfg2):
    cfg1 = cfg1.clone()
    set_cfg_node_new_allowed_attr(cfg1, new_allowed=True)
    cfg1.merge_from_other_cfg(cfg2)
    return cfg1


def load_ymal_config(config_path):
    # config_path = os.path.join(os.path.dirname(__file__),'common_config.yaml')
    config = open(config_path, 'r', encoding='utf-8')
    config = CN._load_cfg_from_file(config)
    # config.freeze()
    return config


def parse_header_type(cfg):
    header_type = Enum('HeaderType', ' '.join(cfg.HeaderType), module=__name__)
    return header_type


def parse_header_config(cfg, header_type, company_name=None):
    def _parse_header_config(header_config):
        res_head_config = []
        header_config = sorted(header_config.items(), key=lambda x: x[0])
        for line_no, line_config in header_config:
            line_config = sorted(line_config.items(), key=lambda x: x[0])
            res_line_config = []
            for loc_no, loc_config in line_config:
                res_loc_config = [(list(config.keys())[0], list(config.values())[0]) for config in loc_config]
                res_line_config.append(res_loc_config)
            res_head_config.append(res_line_config)
        return res_head_config

    header_configs = []
    configs = cfg.HeaderConfigs

    for htype in configs:
        for config in configs[htype].values():
            header_support_company = config.get('header_support_company', None)
            if company_name is not None and header_support_company is not None and company_name not in header_support_company:
                # 如果传入了公司名，且某一个表头设置了支持的公司列表
                # 当公司名不在这个表头支持的公司列表当中时，可以直接跳过这个特定的表头config
                continue
            base_config = {
                'header_name': config.header_name,
                'header_config': _parse_header_config(config.header_config),
                'header_type': header_type[htype],
                'multiheader_align': MultiHeaderAlign.NONE
            }
            if config.get('header_merge_mode'):
                base_config.update({'header_merge_mode':config['header_merge_mode']})
            header_configs.append(base_config)

    return header_configs


def parse_keyrow_config(cfg, header_type):
    def _parse_fields_info(fields_info):
        finfo = []
        for info in fields_info:
            if isinstance(info, str):
                finfo.append(header_type[info])
            elif isinstance(info, dict):
                key = list(info.keys())[0]
                values = info[key]
                finfo.append((header_type[key], values))
        return finfo

    def _parse_rule(rule):
        content_req = rule['content_requirement']
        adaptive_fields = _parse_fields_info(rule['adaptive_fields'])
        unexpected_content = rule.get('unexpected_content', [])
        return {
            'content_requirement': content_req,
            'adaptive_fields': adaptive_fields,
            'unexpected_content': unexpected_content
        }

    def _parse_element_config(element_config):
        configs = []
        for config in element_config.values():

            res_config = {'rules': [_parse_rule(rule) for rule in config['rules']]}
            other_requirement = config.get('other_header_requirement', None)
            if other_requirement is not None:
                res_config.update(
                    {'other_header_requirement': _parse_fields_info(other_requirement)}
                )
            configs.append(res_config)
        return configs

    common_configs = _parse_element_config(cfg.ELEMENT_HANDLER.keyrow_config.common_config)

    special_configs = _parse_element_config(cfg.ELEMENT_HANDLER.keyrow_config.get('special_config', {}))

    keyrow_config = {
        'common_config': {
            'common': common_configs,
            'special': special_configs
        }
    }
    return keyrow_config


def parse_filter_config(cfg, header_type):
    filter_config = cfg.ELEMENT_HANDLER.filter_config
    filter_content = filter_config.get('filter_content', [])
    filter_content_in_line = filter_config.get('filter_content_in_line', [])
    filter_lines = filter_config.get('filter_lines', dict())
    filter_comb = filter_config.get('filter_comb', [])

    filter_lines = list(filter_lines.items())

    for filter_ in filter_content:
        filter_['adaptive_fields'] = [header_type[htype] for htype in filter_['adaptive_fields']]

    for idx, comb in enumerate(filter_comb):
        comb = list(comb.values())[0]
        comb = [list(c.items())[0] for c in comb]
        for cidx in range(len(comb)):
            comb[cidx] = (header_type[comb[cidx][0]], comb[cidx][1])
        filter_comb[idx] = comb

    return {
        'filter_lines': filter_lines,
        'filter_comb': filter_comb,
        'filter_content': filter_content,
        'filter_content_in_line': filter_content_in_line
    }


def parse_prime_key(cfg, header_type):
    return cfg.PrimeKey


def parse_debug_path(cfg):
    if cfg.DEBUG.DEBUG_ON:
        return cfg.DEBUG.DEBUG_PATH
    else:
        return None


def parse_block_update_config(cfg):
    return cfg.ELEMENT_HANDLER.get('block_update_config', [])
