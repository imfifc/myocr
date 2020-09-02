import os
import yaml
import copy

TEMPLATE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(TEMPLATE_DIR, "config")
PARSER_DIR = os.path.join(TEMPLATE_DIR, "parser")

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def load_yaml_conf(path):
    with open(path, encoding="utf-8", mode="r") as f:
        content = yaml.load(f, Loader)
    return content


def load_tmpl_conf(path):
    conf = load_yaml_conf(path)

    default_path = os.path.join(CONFIG_DIR, "default_conf.yml")

    if os.path.exists(default_path):
        default_conf = load_yaml_conf(default_path)
        merge_yml_conf(conf, default_conf)

    return conf


def merge_yml_conf(conf, default_conf):
    """
    根据 conf 里的 item_name 从 default_conf 中提取 item 对应的默认配置，
    再使用 conf 里的配置覆盖提取出来的 item 配置
    如果 conf 里面 item 有 default_conf 中没有的选项，也会复制过去
    """
    fg_items = conf["fg_items"]
    default_fg_items = default_conf["fg_items"]

    default_fg_items_dict = {}
    default_fg_item_names = set()
    for v in default_fg_items:
        item_name = v["item_name"]
        default_fg_items_dict[item_name] = v
        default_fg_item_names.add(item_name)

    merged_fg_items = []
    for fg_item in fg_items:
        item_name = fg_item["item_name"]

        if item_name in default_fg_item_names:
            merged_fg_item_conf = copy.deepcopy(default_fg_items_dict[item_name])
            for k, v in fg_item.items():
                merged_fg_item_conf[k] = v
            merged_fg_items.append(merged_fg_item_conf)
        else:
            merged_fg_items.append(fg_item)

    conf["fg_items"] = merged_fg_items
    return conf
