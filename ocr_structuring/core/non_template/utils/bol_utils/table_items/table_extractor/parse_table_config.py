from collections import defaultdict, namedtuple

from yacs.config import CfgNode as CN

from ocr_structuring.core.non_template.utils.bol_utils.table_items.configs import config_parser

cfg = None

ContentConfig = namedtuple('ContentConfig',
                           ['start_key_words', 'end_key_words', 'start_exps', 'end_exps', 'start_filter_exps',
                            'filter_exps'])

Config = namedtuple('config', ['common_config', 'company_config'])

ContentConfig.__new__.__defaults__ = ([], [], [], [], [], [])
Config.__new__.__defaults__ = (ContentConfig(), [])

FieldConstraint = namedtuple('fieldConstraint', ['header_requirement', 'regex_list', 'fetch_fid'])
FieldConstraint.__new__.__defaults__ = (None, None, '')
FetchConstraint = namedtuple('fetchConstraint', ['fetch_field', 'fetch_regex'])
OTHERFieldConstraint = namedtuple('otherfieldConstraint', 'header_requirements')
FetchOnOtherConfig = namedtuple('fetch_on_other', ['field_constraints', 'fetch_constraint', 'other_fields_check'])
FetchOnOtherConfig.__new__.__defaults__ = (None, None, OTHERFieldConstraint(header_requirements=[]))


# 每一条配置应该需要支持：
# 1 field constraint ： 显示在每个列要找到的 行 ， 只有对那些在每个field 都符合了条件的行才会考虑抽取信息
# 2 fetch_constraint :  在满足了条件的情况下使用fetch 正则把内容拿出来


def load_cfg(cfg_path):
    with open(cfg_path, 'r', encoding='utf-8') as f:
        try:
            cfg = CN._load_cfg_from_file(f).clone()
        except:
            cfg = CN._load_cfg_from_file(f).clone()
    return cfg


def merge_company_cfg(cfg, company_name=None):
    common = cfg.common
    company_cfg = cfg.get('company_config', None)
    if company_name is not None and company_cfg is not None and company_name in company_cfg:
        common = config_parser.merge_two_cfg(common, company_cfg[company_name])
    return common


def get_common_config(cfg, company_name=None):
    def _convert_config(regex_config):
        regex_config_map = {}
        process_config_map = defaultdict(dict)
        for key, value in regex_config.items():
            if 'post_process_func' in value:
                process_config_map[key]['post_process_func'] = value.pop('post_process_func')

            regex_config_map[key] = ContentConfig(**value)
        return regex_config_map, process_config_map

    process_cfg = merge_company_cfg(cfg.PROCESS_CONFIG, company_name)
    return _convert_config(process_cfg)


def get_fetch_on_other_config(cfg, company_name):
    def _convert_fetch_config(cfg):
        fetch_config = defaultdict(list)
        for key, configs in cfg.items():
            for config in configs.values():
                field_c_list = []
                for field_c in config.field_constraints:
                    header_req = field_c['header_requirement']
                    if isinstance(header_req, dict):
                        fkey = list(header_req.keys())[0]
                        fvalues = header_req[fkey]
                        field_c['header_requirement'] = (fkey, fvalues)

                    field_c_list.append(FieldConstraint(**field_c))
                fetch_c = FetchConstraint(**config.fetch_constraint)
                if 'other_fields_check' in config:
                    other_check = config.other_fields_check
                    for idx, head_req in enumerate(other_check.header_requirements):
                        if isinstance(head_req, dict):
                            key = list(head_req.keys())[0]
                            values = head_req[key]
                            other_check.header_requirements[idx] = (key, values)

                    other_c = OTHERFieldConstraint(**config.other_fields_check)
                else:
                    other_c = OTHERFieldConstraint(header_requirements=[])
                fetch_config[key].append(FetchOnOtherConfig(
                    field_constraints=field_c_list,
                    fetch_constraint=fetch_c,
                    other_fields_check=other_c)
                )

        return fetch_config

    cfg = merge_company_cfg(cfg.FETCH_ON_OTHER_CONFIG, company_name)
    return _convert_fetch_config(cfg)


def load_table_cfg(cfg, company_name):
    regex_config, process_config_map = get_common_config(cfg, company_name)
    fetch_on_other_config = get_fetch_on_other_config(cfg, company_name)
    return regex_config, process_config_map, fetch_on_other_config
