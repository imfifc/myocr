import os

import pytest
import yaml

from ocr_structuring.core.template.main import TemplateStructuring
from ocr_structuring.core.template.tests.dummy_test_parser import DummyTestParser
import numpy as np
from ocr_structuring.core.template.tp_node_item import TpNodeItem
from ocr_structuring.core.utils.exception import ConfigException

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
TPL_PATH = os.path.join(CURRENT_DIR, "tpl.yml")
TPL2_PATH = os.path.join(CURRENT_DIR, "tpl2.yml")


def test_parse_base(capsys):
    with open(TPL_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.load(f)
    cfg["is_tp_conf"] = True
    parser = DummyTestParser("dummy", cfg)
    with capsys.disabled():
        print(parser)
    node = TpNodeItem(["text", 0, 0, 50, 50, 1, 1])
    parser.parse_template({node.uid: node}, np.zeros((100, 100)).astype(np.uint8))
    assert parser.fg_items["name"].post_func.__name__ == "_post_func_name"
    assert parser.fg_items["sex"].post_func.__name__ == "_post_func_max_w_regex"
    assert parser.fg_items["address"].post_func.__name__ == "_post_func_max_w_regex"
    assert parser.fg_items["address"].pre_func is None


def test_parse_base_exeption(capsys):
    with open(TPL2_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.load(f)
    cfg["is_tp_conf"] = True
    with pytest.raises(ConfigException) as err:
        DummyTestParser("dummy", cfg)


def test_is_tp_conf():
    with open(TPL_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.load(f)
    assert TemplateStructuring.is_tp_conf(cfg) is True
