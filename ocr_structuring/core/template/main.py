import os
import pkgutil
import numpy as np
from pathlib import Path
from typing import Dict, List
from importlib import import_module

from ocr_structuring.debugger import variables
from ocr_structuring.utils.logging import logger
from .loader import PARSER_DIR
from .parser_base import ParseBase
from .loader import load_tmpl_conf
from .tp_node_item import TpNodeItem
from .matcher import TemplateMatcher
from ..utils.debug_data import DebugData
from .matcher.above_offset import ABOVE_OFFSET_METHOD_IOU

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_DIR = Path(os.path.join(CURRENT_DIR, "config"))


class TemplateStructuring:
    def __init__(self, class_name=None):
        # 动态加载
        for (_, name, _) in pkgutil.iter_modules([PARSER_DIR]):
            import_module("ocr_structuring.core.template.parser." + name)

        self.confs = {}
        self.parsers = {}
        self.matchers = {}

        if class_name is None:  # 生产逻辑，加载所有模板
            subclasses = ParseBase.subclasses
        else:  # 调试逻辑，只加载class_name对应模板
            subclasses = {class_name: ParseBase.subclasses[class_name]}

        for name, parse_class in subclasses.items():
            conf = self.load_conf(CONFIG_DIR, name)
            conf['is_tp_conf'] = self.is_tp_conf(conf)
            self.confs[name] = conf
            self.parsers[name] = parse_class(name, conf)
            self.matchers[name] = TemplateMatcher(conf)

    @staticmethod
    def is_tp_conf(conf) -> bool:
        version = conf.get('version', 1)
        if version >= 2:
            return True
        return False

    @staticmethod
    def supported_class_names() -> List[str]:
        return sorted(list(ParseBase.subclasses.keys()))

    def process(
        self,
        node_items: Dict[str, TpNodeItem],
        img: np.ndarray,
        class_name: str,
        debug_data: DebugData = None,
    ):
        """
        :param node_items:
        :param img: numpy BGR image
        :param class_name: 模板名称
        :return:
            dict.
            key: item_name
            value: StructureItem.to_dict 的结果
        """
        # 背景缩放和前景偏移
        before_count = len(node_items)
        # if class_name in ['shanghai_menzhen', 'shanghai_zhuyuan']:
        #     above_offset_method = above_offset.ABOVE_OFFSET_METHOD_ANCHOR
        # else:
        #     above_offset_method = above_offset.ABOVE_OFFSET_METHOD_IOU
        self.matchers[class_name].process(node_items, img, debug_data=debug_data)

        after_count = len(node_items)
        if before_count != after_count:
            logger.debug(
                f"node_items count change after matcher.process(): {before_count} -> {after_count}"
            )

        # 模板匹配，跑 filter_area 和 filter_regex 等 filter

        # raw_data = []
        # for node in node_items.values():
        #     if getattr(node, 'been_merged', False):
        #         continue
        #     raw_data.append(node.raw_node[0:9])
        # variables.add_group('detection', 'detection', raw_data)

        result = self.parsers[class_name].parse_template(
            node_items, img, debug_data=debug_data
        )
        return result

    def load_conf(self, config_dir, name):
        """
        :param config_dir: 存放配置文件的目录
        :param name: 模板的名称
        :return:
        """
        conf_path = config_dir / (name + ".yml")
        if not conf_path.exists():
            raise FileNotFoundError(f"Template yml config file not exist: {conf_path}")

        return load_tmpl_conf(conf_path)
