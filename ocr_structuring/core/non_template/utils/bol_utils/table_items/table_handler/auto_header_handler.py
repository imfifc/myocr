from ocr_structuring.core.non_template.utils.bg_item import BgItem
from ocr_structuring.core.non_template.utils.bol_utils.table_items.header.header_items import HeaderItem
from ocr_structuring.core.non_template.utils.multiline_bg_item import MultiHeaderAlign, MultiRowItem, RowBGItem
import re


class AutoHeadFinder():
    def __init__(self,cfg):
        self.cfg = cfg

    def recheck_header(self, header_group, node_items):
        possible_header_nodes = self.find_possible_header_nodes(header_group, node_items)
        possible_header_nodes = self.filter_possible_header_nodes(header_group, possible_header_nodes)
        header_items = self.create_new_header_items(header_group.header_types, possible_header_nodes)
        header_group.finded_header.extend(header_items)
        header_group.finded_header = sorted(header_group.finded_header, key=lambda x: x.key_node.bbox.cx)
        header_group.update_bbox()
        return header_group

    def create_new_header_items(self, header_types, possible_header_nodes):
        template_obj = {
            'header_name': '',
            'header_config': [],
            'header_type':
                header_types.OTHER,
            'multiheader_align':
                MultiHeaderAlign.NONE
        }
        configs = []
        for idx, node in enumerate(possible_header_nodes):
            obj = template_obj.copy()
            obj["header_name"] = node.text
            obj["header_config"] = [[[(node.text, -1)]]]
            configs.append(obj)

        possible_header_items = []
        for idx, header_config in enumerate(configs):
            name = header_config['header_name']
            config = header_config['header_config']
            type = header_config['header_type']
            align_method = header_config['multiheader_align']
            head_item = HeaderItem('header_{}_'.format(idx) + name, config, type, align_method,
                                   merge_mode=BgItem.MATCH_MODE_HORIZONTAL_SPLIT)
            row_bg_item = RowBGItem([possible_header_nodes[idx]])
            head_item.key_node = MultiRowItem([row_bg_item])
            head_item.is_find_by_config = False
            possible_header_items.append(head_item)
        return possible_header_items

    def find_possible_header_nodes(self, header_group, node_items):
        # 找到所有的header_group 处的节点
        header_target_bbox = header_group.finded_header[0].key_node.bbox
        header_nodes = []
        for node in node_items.values():
            # if self.max_intersection_rate(node.bbox.top, node.bbox.bottom, header_target_bbox.top,
            #                               header_target_bbox.bottom) > 0.3:

            # 计算node 和 header_group 的角度
            angle_2_left = header_group.calculate_angle(node.bbox, header_group.finded_header[0].bbox, 'bottom')
            angle_2_right = header_group.calculate_angle(node.bbox, header_group.finded_header[-1].bbox, 'bottom')
            # print('debug',angle_2_left,angle_2_right,node.text)
            if min(abs(angle_2_left - header_group.get_header_angle()),
                   abs(angle_2_right - header_group.get_header_angle())) < 2:
                header_nodes.append(node)

        return header_nodes



    def filter_possible_header_nodes(self, header_group, header_nodes):
        header_nodes = self.filter_by_content(header_nodes)
        header_nodes = self.filter_by_location(header_group, header_nodes)
        header_nodes = self.filter_by_content(header_nodes)
        return header_nodes

    def filter_by_content(self, header_nodes):

        useful_nodes = []
        for node in header_nodes:
            text = node.text
            # 进行文本过滤，如果text 当中***的数量较多，筛除出去
            redudant = re.sub('[^*]', '', node.text)
            if len(redudant) > 3 or re.match('^\*{1,}$', redudant):
                continue
            # 筛选出英文和数字，内容小于三个的过滤掉

            clean_content = re.sub('[^0-9a-zA-Z]', '', text)
            if len(clean_content) < 2 and text not in ['L', 'W', 'H']:
                continue
            if 'iee' in clean_content or 'tee' in clean_content:
                continue

            # 过滤amount数字
            match_regex = False
            for regex in self.cfg.AUTO_FIND_HEADER.filter_regex_list:
                if re.search(regex,clean_content,re.IGNORECASE):
                    match_regex = True
                    break
            if match_regex:
                continue

            useful_nodes.append(node)
        return useful_nodes

    def filter_by_location(self, header_group, header_nodes):

        # 从下往上排序
        header_nodes = sorted(header_nodes, key=lambda x: -x.bbox.bottom)
        for idx, header_node in enumerate(header_nodes):
            for idx_2 in range(len(header_nodes) - 1, -1, -1):
                header_node2 = header_nodes[idx_2]
                if idx_2 <= idx:
                    break
                # if self.max_intersection_rate(header_node.bbox.left, header_node.bbox.right, header_node2.bbox.left,
                #                               header_node2.bbox.right) >= 0.3:
                # 改成判断是否满足左对齐，右对齐，和居中对齐
                left_align = abs(header_node.bbox.left - header_node2.bbox.left)
                right_align = abs(header_node.bbox.right - header_node2.bbox.right)
                middel_align = abs(header_node.bbox.cx - header_node2.bbox.cx)
                if min(left_align, right_align, middel_align) < 0.3 * (
                        (header_node2.bbox.height + header_node.bbox.height) / 2):
                    header_node.bbox.merge_(header_node2.bbox)
                    header_node.text = header_node2.text + '\n' + header_node.text
                    del header_nodes[idx_2]

        # 如果新找到的header_nodes之前已经被找到
        for idx_2 in range(len(header_nodes) - 1, -1, -1):
            header_node2 = header_nodes[idx_2]
            for header_node in header_group.finded_header:
                if self.max_intersection_rate(header_node.bbox.left, header_node.bbox.right, header_node2.bbox.left,
                                              header_node2.bbox.right) >= 0.3:
                    del header_nodes[idx_2]
                    break
        return header_nodes

    def max_intersection_rate(self, start1, end1, start2, end2):
        if start1 >= end1 or start2 >= end2 or start2 >= end1 or start1 >= end2:
            return 0
        max_start = max(start1, start2)
        min_end = min(end1, end2)
        rate1 = (min_end - max_start) / (end1 - start1)
        rate2 = (min_end - max_start) / (end2 - start2)
        return max(rate1, rate2)
