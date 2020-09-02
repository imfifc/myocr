from ocr_structuring.core.non_template.utils.target_item import TargetItem, BgItem
import re
import uuid
import copy


class ClassificationProcessor:
    def __init__(self, config, categories):
        self.categories = categories
        self.config = config

    def get_category(self, node_items):
        result_config = copy.deepcopy(self.config)
        for cat_name, rules in self.config.items():
            satisfied = False
            for rule_name, rule in rules.items():
                must_find_key_words = rule["must_find"]["key_words"]
                must_find_regexs = rule["must_find"]["regexs"]
                must_not_find_key_words = rule["must_not_find"]["key_words"]
                must_not_find_regexs = rule["must_not_find"]["regexs"]
                tk_flags = self.find_key_words(must_find_key_words, node_items)
                tr_flags = self.find_regexs(must_find_regexs, node_items)
                fk_flags = self.find_key_words(must_not_find_key_words, node_items)
                fr_flags = self.find_regexs(must_not_find_regexs, node_items)
                if (False not in tk_flags) and (False not in tr_flags) and (True not in fk_flags) and (
                        True not in fr_flags):
                    result_config[cat_name][rule_name]["must_find"]["key_words"] = tk_flags
                    result_config[cat_name][rule_name]["must_find"]["regexs"] = tr_flags
                    result_config[cat_name][rule_name]["must_not_find"]["key_words"] = fk_flags
                    result_config[cat_name][rule_name]["must_not_find"]["regexs"] = fr_flags
                    satisfied = True
                    break
            if satisfied:
                return cat_name, rule_name, result_config
        return None, None, None

    def find_key_words(self, key_words, node_items):
        flags = []
        for key_word in key_words:
            flag = self.match_key_word(node_items, key_word)
            flags.append(flag)
        return flags

    def find_regexs(self, regexs, node_items):
        flags = []
        for regex in regexs:
            flag = self.match_regex(node_items, regex)
            flags.append(flag)
        return flags

    def match_key_word(self, node_items, key_word):
        bg_texts = [key_word]
        # 根据bg_texts生成bg_items
        bg_items = []
        for bg_text in bg_texts:
            if isinstance(bg_text, tuple):
                ed_thresh = bg_text[1]
                bg_text = bg_text[0]
            else:
                ed_thresh = -1

            max_interval = 1 if len(bg_text) <= 3 else 2
            bi = BgItem(bg_text, BgItem.MATCH_MODE_HORIZONTAL_SPLIT, ed_thresh,
                        h_split_pre_func=clean,
                        h_split_max_interval=max_interval)
            bg_items.append(bi)

        # 根据bg_items找到matched_nodes
        matched_nodes = []
        matched_ed_dist = []
        rest_nodes = []

        for bg_item in bg_items:
            if bg_item.mode == BgItem.MATCH_MODE_HORIZONTAL_SPLIT:
                _matched_nodes, _matched_ed_dist, _rest_nodes = bg_item.match(node_items)
                matched_nodes.extend(_matched_nodes)

                for rest_node in _rest_nodes:
                    rest_nodes.append(rest_node)

            else:
                _matched_nodes, _matched_ed_dist = bg_item.match(node_items)
                matched_nodes.extend(_matched_nodes)

            matched_ed_dist.extend(_matched_ed_dist)

        if len(matched_nodes):
            return True
        return False

    def match_regex(self, node_items, regex):
        for node in node_items.values():
            if re.search(regex, node.text, re.IGNORECASE):
                return True
        return False

    def get_node_items_list(self, node_items):
        node_list = []
        for node in node_items.values():
            node_list.append(node)
        return node_list

    def get_node_items_dict(self, node_items):
        node_dict = {}
        for node in node_items:
            node_dict[uuid.uuid1().hex] = node
        return node_dict

    def find_larger_nodes(self, node_items):
        larger_nodes = []
        avg_height = 0
        node_num = 0
        for node in node_items.values():
            avg_height = node_num / (node_num + 1) * avg_height + 1 / (node_num + 1) * node.bbox.height
        for node in node_items.values():
            if node.bbox.height > avg_height:
                larger_nodes.append(node)
        return self.get_node_items_dict(larger_nodes)


# def simple_to_complex_for_config(self, simple_config):
#     complex_config = {}
#     return complex_config


def clean(text):
    return text.lower()
