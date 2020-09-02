import os

import yaml
from ocr_structuring.core.template.matcher.tp_conf_bg_item import TpConfBgItem
from ocr_structuring.core.template.matcher.tp_conf_above_item import TpConfAboveItem
from ocr_structuring.core.template.tp_node_item import TpNodeItem

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
TPL_PATH = os.path.join(CURRENT_DIR, "tpl.yml")


def test_bg_item():
    yaml_str = """
        area:
          - 164.40366972477062
          - 161.46788990825686
          - 309.7247706422018
          - 228.9908256880734
        contents: 姓名
        fold: true
        mode: common
        ed_thresh: 0
    """
    bg = TpConfBgItem(yaml.safe_load(yaml_str), True)

    node_item = TpNodeItem(["姓名", 0, 0, 50, 50, 0, 0.1])

    matched_node = bg.match_node({node_item.uid: node_item})[0]
    assert matched_node.text == "姓名"


def test_bg_item_ed_thresh():
    yaml_str = """
        area:
          - 164.40366972477062
          - 161.46788990825686
          - 309.7247706422018
          - 228.9908256880734
        contents: 姓名
        fold: true
        mode: common
        ed_thresh: 1
    """
    bg = TpConfBgItem(yaml.safe_load(yaml_str), True)

    node_item = TpNodeItem(["姓民", 0, 0, 50, 50, 0, 0.1])

    matched_node = bg.match_node({node_item.uid: node_item})[0]
    assert matched_node.text == "姓民"


def test_above_item():
    yaml_str = """
      area:
          - 1186.0550458715595
          - 91.0091743119266
          - 1460.5504587155963
          - 157.06422018348624
      item_name: xingming
      contents: 姓名
      fold: false
      ed_thresh: 0
      ban_offset: ''
      regex: \S
      ioo_thresh: 0.1
      can_not_miss: ''
    """
    above = TpConfAboveItem(yaml.safe_load(yaml_str), True)

    node_item = TpNodeItem(["姓名", 0, 0, 50, 50, 0, 0.1])
    matched_node = above.match_node({node_item.uid: node_item})
    assert matched_node.text == "姓名"


def test_above_item_ed_thresh():
    yaml_str = """
      area:
          - 1186.0550458715595
          - 91.0091743119266
          - 1460.5504587155963
          - 157.06422018348624
      item_name: xingming
      contents: 姓名
      fold: false
      ed_thresh: 1
      ban_offset: ''
      regex: \S
      ioo_thresh: 0.1
      can_not_miss: ''
    """
    above = TpConfAboveItem(yaml.safe_load(yaml_str), True)

    node_item = TpNodeItem(["姓民", 0, 0, 50, 50, 0, 0.1])
    matched_node = above.match_node({node_item.uid: node_item})
    assert matched_node.text == "姓民"
