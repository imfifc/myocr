# 这里根据配置，创建表头对象，每个表头为一个header item
import copy
import re
from collections import defaultdict
from enum import Enum
from itertools import chain
from itertools import combinations
from itertools import product
from typing import List, Dict, Callable

import numpy as np

import ocr_structuring.core.non_template.utils.line_utils  as line_utils
from ocr_structuring.core.non_template.utils.bg_item import BgItem
from ocr_structuring.core.non_template.utils.bol_utils.utils.time_counter import record_time
from ocr_structuring.core.non_template.utils.multiline_bg_item import \
    MultiLineBGItem, MultiRowItem
from ocr_structuring.core.utils.bbox import BBox
from ocr_structuring.core.utils.node_item import NodeItem
from ocr_structuring.utils.logging import logger


class HeaderItem:
    def __init__(self, name, config, head_type, align_method, merge_mode=BgItem.MATCH_MODE_COMMON,
                 user_clean_method: Callable = None):
        assert merge_mode in [BgItem.MATCH_MODE_HORIZONTAL_MERGE, BgItem.MATCH_MODE_HORIZONTAL_SPLIT,
                              BgItem.MATCH_MODE_COMMON]

        self.name = name
        self.head_type = head_type  # 这个header ，对应的是什么含义，在同系列的表单当中，虽然表头不同，但可能实际是描述同一个东西
        self.align_method = align_method
        self.user_clean_method = user_clean_method
        self.multiline_bg_items = self.build_bg_items(config, align_method, merge_mode)
        self.key_node_list: List[MultiRowItem] = []
        self.key_node: MultiRowItem = None
        self.is_find_by_config = True

    @record_time
    def search_key_node_list(self, node_items: Dict[str, NodeItem]):
        # 输入所有的node_items，判断是否能够找到这个HeaderItem 对应的key node
        self.key_node_list = self.multiline_bg_items.match(node_items)

    def assign_key_node(self):
        assert self.has_key_node is True, 'header for assign must has key node list'

        copy_hit = [copy.deepcopy(self) for _ in range(len(self.key_node_list))]
        for hi, key_node in zip(copy_hit, self.key_node_list):
            hi.key_node = key_node
            del hi.key_node_list
        return copy_hit

    @property
    def has_key_node(self):
        return len(self.key_node_list) > 0

    @staticmethod
    def clean_text(text):
        if text == '':
            return ''
        text = re.sub('[^\. 0-9A-Za-z]*', '', text).lower()
        return text

    def build_bg_items(self, config, align_method, merge_mode):
        if self.user_clean_method is not None:
            clean_func = self.user_clean_method
        else:
            clean_func = self.clean_text
        return MultiLineBGItem(config, clean_text_func=clean_func, align_method=align_method,
                               merge_mode=merge_mode)

    @property
    def bbox(self):
        assert self.key_node is not None, 'assign key_node before use this method'
        return self.key_node.bbox

    def merge_(self, other_head):
        # 扩展自己的bbox 和 keyrow
        self.key_node.merge_(other_head.key_node)


class HeaderGroup(object):
    def __init__(self, header_list, pr_headers=None, angle_thresh=10):
        """

        :param header_list: 所有可能的header
        :param pr_headers:  如果设置了pr headers ， 则pr headers 一定需要留在最后返回的结果内
        :param angle_thresh: 选择的基准header 的角度不能大于 angle_thresh
        """
        self.header_list = header_list
        assert len(self.header_list) >= 2
        self.pr_headers = pr_headers
        self.angle_thresh = angle_thresh
        self.search_most_possible_result()
        self._bbox = None
        self._angle_mean = None
        # 为避免错误调用，这里删掉 header_list
        del self.header_list

    def search_most_possible_result(self):
        # 基本的搜索思路是
        # 首先选择两个作为基准，然后把其他的逐个尝试加入，如果能够和这两个共线，则认为是合理的
        # 最后选择共线个数最多的组合
        finded_header = []
        for comb in combinations(self.header_list, 2):
            if self.pr_headers is not None and not self.judge_comb_valid(comb):
                continue

            angle_of_comb = self.cal_angle(comb)
            large_angle_status = False
            if abs(angle_of_comb) > self.angle_thresh:
                # 说明这个组合是一个大角度组合
                large_angle_status = True
            rest_heads = self.get_rest(comb)
            result_comb = self.merge_rest_heads(comb, rest_heads)

            # 对大角度组合，只有当所有的内容都在一条直线上的时候，才会使用
            if large_angle_status and len(result_comb) != len(self.header_list):
                continue
            finded_header.append(result_comb)

        finded_header = sorted(finded_header, key=lambda x: len(x), reverse=True)
        if finded_header:
            self.finded_header = finded_header[0]
            self.finded_header = sorted(self.finded_header, key=lambda x: x.key_node.bbox.cx)
        else:
            self.finded_header = []

    def merge_same_column_header(self, finded_header):
        """
        对于某些多行的表头，存在other 和某一个类型的表头处于同一列，然后导致找表头和找列的时候出现问题
        如下图，两个表头被分别找了，这时候采取合并表头
        目前只支持两行上重复的，三行上重复的就GG了
        ---------
        N.W.(KGS)
        org_country
        ----------
        """
        # 从左到右排序
        finded_header = copy.deepcopy(finded_header)

        sorted_header = sorted(finded_header, key=lambda x: x.key_node.bbox.cx)
        header_name_map = {head.name: head for head in sorted_header}

        # 计算header 的cy 的高度差
        center_list = [header.key_node.bbox.cy for header in sorted_header]
        header_avg_height = np.mean([header.key_node.avg_height for header in sorted_header])

        if max(center_list) - min(center_list) < 0.5 * header_avg_height:
            return finded_header

        # 如果有高度差，则尝试合并上下左对齐的表头

        # 检查是否存在两个位置是上下紧挨的表头
        merged_header_name = dict()  # 记录需要移除的node，想办法把他们合并到 其他表头当中
        for header_comb in combinations(sorted_header, 2):
            first = header_comb[0]
            second = header_comb[1]

            # 判断 上下对齐
            # 判断 是否包含
            if first.key_node.bbox.top > second.key_node.bbox.top:
                first, second = second, first

            if abs(second.key_node.bbox.top - first.key_node.bbox.bottom) / header_avg_height < 0.1:
                # 认为这俩个内容紧挨着
                # 检查是否中心对齐或者左对齐
                center_diff = abs(first.key_node.bbox.cx - second.key_node.bbox.cx)
                left_diff = abs(first.key_node.bbox.left - second.key_node.bbox.left)
                if min(center_diff, left_diff) / header_avg_height < 0.3:
                    merged_header_name[second.name] = first.name

            if second.key_node.bbox.cal_ioo(first.key_node.bbox) > 0.8:
                # second 位于first
                merged_header_name[second.name] = first.name

        # 把需要合并的按照从下往上的方向，逐步的合并到对应的node 当中
        sorted_need_merge = sorted(
            {need_merge: header_name_map[need_merge] for need_merge in merged_header_name}.items(),
            key=lambda x: x[1].key_node.bbox.top, reverse=True
        )

        # 遍历要合并的内容
        for name, node_need_merge in sorted_need_merge:
            target_node_name = merged_header_name[name]
            target_node = header_name_map[target_node_name]
            target_node.merge_(node_need_merge)
            # logger.info('merged {} into {}'.format(name, target_node_name))

        for name, node_need_merge in sorted_need_merge:
            del header_name_map[name]

        return list(header_name_map.values())

    @property
    def has_finded_header(self):
        return len(self.finded_header) > 0

    @property
    def bbox(self):
        assert len(self.finded_header) > 0, 'only group has possible combination cat get bbox info'
        if self._bbox is None:
            for idx, header in enumerate(self.finded_header):
                if idx == 0:
                    bbox = header.key_node.bbox
                else:
                    bbox = bbox.merge(header.key_node.bbox)
            self._bbox = bbox
        return self._bbox

    def update_bbox(self):
        for idx, header in enumerate(self.finded_header):
            if idx == 0:
                bbox = header.key_node.bbox
            else:
                bbox = bbox.merge(header.key_node.bbox)
        self._bbox = bbox
        self._angle_mean = None
        self._angle_mean = self.get_header_angle()

    @property
    def mean_header_width(self):
        """
        大概计算一下，每个表头的宽度的均值
        :return: 估计的宽度
        """
        header_width_mean = np.mean([row.bbox.width for row in self.finded_header])
        return header_width_mean

    @property
    def mean_header_interval(self):
        interval = 0
        interval_count = 0
        for i in range(1, len(self.finded_header)):
            left = self.finded_header[i - 1]
            right = self.finded_header[i]
            if right.bbox.left - left.bbox.right > - 0.2 * ((right.bbox.height + left.bbox.height) / 2):
                interval += (right.bbox.left - left.bbox.right)
                interval_count += 1
        if interval_count == 0:
            return 0
        else:
            return interval / interval_count

    def merge_rest_heads(self, comb, rest_heads):
        result_comb = []
        for head in rest_heads:
            if self.can_merge_head(comb, head):
                result_comb.append(head)
        result_comb.extend(comb)
        return result_comb

    def can_merge_head(self, comb, head):
        # 计算和 comb 内元素的angle
        angle_list = []
        for base in ['cy', 'bottom', 'top']:
            a1 = self.cal_angle([comb[0], head], base=base)
            a2 = self.cal_angle([comb[1], head], base=base)
            a3 = self.cal_angle(comb, base=base)
            mean_angle = (abs(a1 - a2) + abs(a2 - a3) + abs(a3 - a1)) / 3
            angle_list.append(mean_angle)
        if min(angle_list) <= 2:
            return True
        return False

    def judge_comb_valid(self, comb):
        valid_comb = True
        for pr in self.pr_headers:
            if pr not in comb:
                valid_comb = False
        return valid_comb

    def get_rest(self, selected_comb):
        return [header for header in self.header_list if header not in selected_comb]

    @staticmethod
    def cal_angle(comb, base='cy'):
        assert base in ['cy', 'top', 'bottom']

        header1_box = comb[0].key_node.bbox
        header2_box = comb[1].key_node.bbox

        return HeaderGroup.calculate_angle(header1_box, header2_box, base)

    @staticmethod
    def calculate_angle(header1_box, header2_box, base):
        header1_cx = header1_box.cx
        header1_cy = getattr(header1_box, base)

        header2_cx = header2_box.cx
        header2_cy = getattr(header2_box, base)

        if header1_cx > header2_cx:
            header1_cx, header1_cy, header2_cx, header2_cy = header2_cx, header2_cy, header1_cx, header1_cy
        angle = np.arctan2([header2_cy - header1_cy], [header2_cx - header1_cx]) / np.pi * 180

        return angle

    @property
    def item_num_score(self):
        # 首先，应该包含尽量多的headerItem
        item_num_score = len(self.finded_header)
        return item_num_score

    @property
    def node_number_score(self):
        # 尽量选择复杂的
        return sum([header.key_node.count_nodes for header in self.finded_header])

    @property
    def node_quality_score(self):
        # 再其次，遍历所有的内容，应该使得cut node 的内容尽量少
        node_quality_score = -1 * sum([header.key_node.cut_nodes_count for header in self.finded_header])
        # cut node 应该越少越好
        return node_quality_score

    @property
    def angle_score(self):
        # 其次，组内的angle 差距应该不大
        angle_mean = 0
        for pair_comb in combinations(self.finded_header, 2):
            angle_mean += self.cal_angle(pair_comb)
        angle_mean /= len(self.finded_header)

        return angle_mean

    def get_all_nodes(self):
        # 返回finded_header 上的
        reference_node = list(
            chain(*[list(chain(*[row.node_items for row in header.key_node.rows])) for header in self.finded_header]))
        return reference_node

    @property
    def evaluation_score(self):
        return self.item_num_score * 1e4 + self.node_number_score * 1e2 + self.node_quality_score

    def get_header_angle(self):
        # 其次，组内的angle 差距应该不大
        if self._angle_mean is not None:
            return self._angle_mean

        # 如果存在rbox 的相关信息，直接取出所有的rbox ，然后求均值
        reference_node = self.get_all_nodes()
        if getattr(reference_node[0], 'rbox', None) is not None:
            if all([abs(node.rbox.meaningful_angle) < 2 for node in reference_node]):
                # 当水平处理
                return 0
            # 让node的字数个数大于2，保证node 是一个长方形
            reference_node = [node for node in reference_node if
                              len(node.text) > 2 and abs(node.rbox.meaningful_angle) >= 2]
            if len(reference_node) > 0:
                angle_mean = np.mean([node.rbox.meaningful_angle for node in reference_node])
                return angle_mean

        # 要算出一下，到底是 bottom 对齐还是 top 对齐
        angle_mean_min = 999
        for base in ['bottom', 'top']:
            angle_mean = []
            useful_header = [header for header in self.finded_header if getattr(header, 'is_find_by_config', True)]
            for pair_comb in combinations(useful_header, 2):
                angle_mean.append(self.cal_angle(pair_comb, base))
            angle_mean = np.median(angle_mean)
            # angle_mean /= len(self.finded_header)

            if abs(angle_mean) < abs(angle_mean_min):
                angle_mean_min = angle_mean
        self._angle_mean = angle_mean_min
        return self._angle_mean

    def get_header_region(self):
        # interval 设置为左开右闭
        search_interval = []
        for idx, header in enumerate(self.finded_header):
            if idx == 0:
                search_interval.append([0, (header.bbox.right + self.finded_header[idx + 1].bbox.left) / 2])
            elif idx == len(self.finded_header) - 1:
                # 末尾:
                search_interval.append([(self.finded_header[idx - 1].bbox.right + header.bbox.left) / 2, 1e4])
            else:
                search_interval.append([(self.finded_header[idx - 1].bbox.right + header.bbox.left) / 2,
                                        (self.finded_header[idx + 1].bbox.left + header.bbox.right) / 2])
        return search_interval

    @property
    def judege_point_to_header(self, bbox: BBox):
        """

        :param bbox: 判断一个点是否在表头的下方
        :return:
        """
        # 从左到右排列
        sorted([header.key_node.bbox for header in self.finded_header], )

    @record_time
    def filter_nodes_below_headers(self, node_items: Dict[str, NodeItem]):
        # 返回在表头下方一个区域内的node_items
        # 如果存在 rbox 信息， 则可以做更多的处理
        has_rbox = False
        for _, value in node_items.items():
            if getattr(value, 'rbox'):
                has_rbox = True

        if has_rbox:
            # 获取所有的node_item 的下边界
            nodes = self.get_all_nodes()
            # 找到nodes 的最下方
            lowest_head_node = sorted(nodes, key=lambda x: x.rbox.cy, reverse=True)[0]
            # 获取角度的平均值
            # 获取node_items 的角度的均值
            # 对长文本统计有效角度
            node_item_list = [node for node in node_items.values() if len(node.text) > 4]
            if len(node_item_list) > 0:
                meaningfule_angle_list = np.array([node.rbox.meaningful_angle for node in node_item_list])
                # 去除角度为0的部分
                median_angle = np.median(meaningfule_angle_list)
                angle_mark_node = node_item_list[np.argmin(np.abs(meaningfule_angle_list - median_angle))].rbox
                header_line = line_utils.gen_parallel_line(angle_mark_node.up_left[0], angle_mark_node.up_left[1],
                                                           angle_mark_node.up_right[0], angle_mark_node.up_right[1],
                                                           lowest_head_node.rbox.down_left[0],
                                                           lowest_head_node.rbox.down_left[1]
                                                           )
                filtered_nodes = dict()
                for node in node_items.values():

                    if header_line.is_under(line_utils.Point(node.rbox.cx, node.rbox.cy)):
                        filtered_nodes[node.uid] = node

                return filtered_nodes

        mean_interval = self.mean_header_interval
        mean_width = self.mean_header_width

        xmin_limit = self.bbox.left - (mean_interval + mean_width)
        xmax_limit = self.bbox.right + (mean_interval + mean_width)

        head_nodes = [set(node.uid for node in header.key_node.node_items) for header in self.finded_header]
        head_nodes = set.union(*head_nodes)

        min_bottom = min([header.key_node.bbox.bottom for header in self.finded_header])
        ymin_limit = min_bottom - 0.2 * np.mean([header.key_node.avg_height for header in self.finded_header])

        filtered_nodes = dict()
        for uid, node in node_items.items():
            if uid in head_nodes:
                continue

            if node.bbox.top <= ymin_limit:
                continue

            if node.bbox.left <= xmin_limit:
                continue
            if node.bbox.right >= xmax_limit:
                continue

            filtered_nodes[uid] = node
        logger.info('filtered {} node on the top of header'.format(len(node_items) - len(filtered_nodes)))
        return filtered_nodes


class HeaderItemList():
    def __init__(self, header_type: Enum, header_configs: List, prime_key: List[str] = None, text_clean_func=None):
        """

        :param header_type: Enum 类型，标记着总共有哪些内容
        :param header_configs: config ， 用于初始化headers
        :param prime_key: 主键名称，用于寻找共行,可以理解为希望一定出现在一行内的一个标识，
                            如果不设置，则对于找到的行不要求一定包含主键
                            如果设置，则返回的header 必须包含主键信息
        """

        self.header_type = header_type  # 记录总共有哪些类别
        if prime_key is not None:
            assert [pk in self.header_type._member_map_ for pk in prime_key], 'prime key must exitst in header_type'
            self.prime_key = [self.header_type[pk] for pk in prime_key]
        else:
            self.prime_key = None
        self.header_item_list = self.build_header_item(header_configs, text_clean_func)

    def build_header_item(self, header_configs, text_clean_func=None):
        header_item_list = []
        # 注意，应该对每个header 设置一个完全不同的name,作为header 的唯一标识
        for idx, header_config in enumerate(header_configs):
            name, config, type, align_method, merge_mode = self.load_basic_config(header_config)

            header_item = HeaderItem('header_{}_'.format(idx) + name, config, type, align_method, merge_mode=merge_mode,
                                     user_clean_method=text_clean_func
                                     )
            header_item_list.append(header_item)

        return header_item_list

    def load_basic_config(self, header_config: Dict):

        """
        :param header_config: 输入的对行的配置
        :return: 在这里解析配置，并对一些没有设置的内容，配置默认值，避免所有的内容都需要配置
        """
        # 以下是必填
        name = header_config['header_name']
        config = header_config['header_config']
        type = header_config['header_type']
        align_method = header_config['multiheader_align']

        # 以下是选填
        merge_mode = header_config.get('header_merge_mode', BgItem.MATCH_MODE_HORIZONTAL_SPLIT)
        return name, config, type, align_method, merge_mode

    def search_headers(self, node_items: List[NodeItem], img):
        # 返回类型为一个list ，找到返回非空数组，没有找到返回空数组
        header_in_this_page = self.get_header_in_this_page(node_items)
        filtered_heads = self.filter_headers(header_in_this_page)  # 可能会有多个对象都在这张图中匹配到内容，在这里过滤
        for filtered in filtered_heads:
            filtered.finded_header = filtered.merge_same_column_header(filtered.finded_header)
            filtered.header_types = self.header_type
        self.clean_node_items(node_items, filtered_heads)
        return filtered_heads

    def clean_node_items(self, node_items, filtered_heads):
        """
        对于在找head 过程中cut 出来的node ，最后没有在head 中应用的cut 出来的节点全部去除
        :param node_items:
        :param filtered_head:
        :return:
        """
        cut_node_list = set()
        for uid, node in node_items.items():
            if getattr(node, 'is_cuted_node', False) == True:
                cut_node_list.add(uid)

        cut_node_in_head = set()
        for filtered_head in filtered_heads:
            for header in filtered_head.finded_header:
                cut_node_in_head = cut_node_in_head | header.key_node.cut_nodes_set

        cut_not_use = cut_node_list - cut_node_in_head
        for uid in cut_not_use:
            del node_items[uid]

    @record_time
    def filter_headers(self, header_in_this_page: List[HeaderItem]):
        # 这里选取表头的原则
        # 返回的内容是一个List , 每个元素为 "一组表头" , 默认定义在header_type,当中的内容，除了OTHER 之外，其他每个内容只能出现一次

        # 遍历所有的表头可能，选择 ： 1 水平上cy 差距最小的，2 当存在多组候选，比如前两组，在水平diff 上差距不大，选择那个 裁剪出来的node 最少的
        # TODO 现在默认只取第一组，即目前不支持一张图上有多个表结构，后期考虑怎么处理
        assert self.header_type._member_map_.get('OTHER', None) is not None, 'you must set an OTHER in headertype'

        appear_type_dict = defaultdict(list)
        max_header_type_num = 10

        for idx, header in enumerate(header_in_this_page):
            if header.head_type != self.header_type.OTHER:
                appear_type_dict[header.head_type].append(header)

        for idx, header in enumerate(header_in_this_page):
            if header.head_type == self.header_type.OTHER and len(appear_type_dict.keys()) < max_header_type_num:
                appear_type_dict['OTHER' + header.name].append(header)

        header_groups = []
        for header_comb in product(*appear_type_dict.values()):
            # 每次取一组comb 进行分析
            has_valid_line, header_group = self.analyzed_header_comb(header_comb)
            if has_valid_line:
                header_groups.append(header_group)

        if header_groups == []:
            return []
        useful_header_comb = self.select_useful_headers(header_groups)
        return useful_header_comb

    def analyzed_header_comb(self, header_comb):
        """
        在这一步会选择出合理的header
        这里有一点需要注意，每次都会送进来很多的可能的部分，比如可能找到了非核心字段


        :param header_comb:
        :return:
        """
        # assert len(set([header.head_type for header in header_comb])) == len(
        #     header_comb), 'header must have different type'
        if self.prime_key is None:
            # TODO : 思考自适应寻找共行的方法
            raise NotImplementedError

        # TODO: 目前只处理至少有两列的情况
        if len(header_comb) <= 1:
            return False, None

        align_target = [header for header in header_comb if header.head_type in self.prime_key]
        # align_target 必须有值才可以继续
        if len(align_target) == 0:
            return False, None
        header_group = HeaderGroup(header_comb, align_target)
        if header_group.has_finded_header:
            return True, header_group
        else:
            return False, None

    def select_useful_headers(self, header_groups):
        # 目前返回一个list ，避免以后希望输出多行
        # 根据最后返回的bbox ，对header_groups 去重
        bbox_header_group_map = {}
        for header_group in header_groups:
            bbox_info = '_'.join([str(_) for _ in header_group.bbox.rect])
            content_info = '_'.join([_.key_node.content for _ in header_group.finded_header])
            bbox_header_group_map.update({bbox_info + '_' + content_info: header_group})
        # logger
        for header_group in bbox_header_group_map.values():
            content_info = '_|_'.join([_.key_node.content for _ in header_group.finded_header])
            logger.info('find possible header with content {}'.format(content_info))
        filtered_group: List[HeaderGroup] = list(bbox_header_group_map.values())

        # TODO: 如果希望返回多个表头
        # clean_group = self.remove_overlap(filtered_group)
        # return clean_group

        # 筛选原则1，应该保留尽量多的内容？
        filtered_group = sorted(filtered_group, key=lambda x: x.evaluation_score, reverse=True)

        filtered_group = [header_group for header_group in filtered_group if
                          header_group.evaluation_score == filtered_group[0].evaluation_score]

        if len(filtered_group) == 1:
            return [filtered_group[0]]
        else:
            # 如果这几个的高度差不多，选择最长的那一个
            filtered_group = sorted(filtered_group, key=lambda x: x.bbox.width, reverse=True)
            if (filtered_group[0].bbox.cy - np.mean(
                    [header_group.bbox.cy for header_group in filtered_group[1:]])) < 10:
                return [filtered_group[0]]
            else:
                # 去角度变动最小的
                filtered_group = sorted(filtered_group, key=lambda x: x.angle_score)
                return [filtered_group[0]]

    def remove_overlap(self, filtered_group):
        filtered_group = sorted(filtered_group, key=lambda x: x.bbox.area, reverse=True)
        clean_list = []
        for header_group in filtered_group:
            overlap_idx = -1
            for idx, target_group in enumerate(clean_list):
                if target_group.bbox.cal_ioo(header_group.bbox) > 0.1 or header_group.bbox.cal_ioo(
                        target_group.bbox) > 0.1:
                    overlap_idx = idx
                    break
            if overlap_idx >= 0:
                if header_group.evaluation_score > clean_list[overlap_idx].evaluation_score:
                    clean_list[overlap_idx] = header_group
            else:
                clean_list.append(header_group)

        clean_list = sorted(clean_list, key=lambda x: x.bbox.top)

        return clean_list

    @record_time
    def get_header_in_this_page(self, node_items: Dict[str, NodeItem]):
        """
        对于我们所有的配置，我都可以建立一个对应的"headers"
        对每个header ，我都会在图中寻找这个headers 是否存在其特殊的背景字
        并且最后，我会对每个 headers 赋予一个 key_node_list ，表明这个header 在图中找到的背景字

        但是这里注意到，按照以上的逻辑，一个header 和 背景字的对应关系就不是一对一的了
        所以，这里我们采用的方式为 "我全都要！"
        即，比如一个内容找到了多个背景字，则可以对其进行复制多份，每份对应一个key_node

        通过 assign key node ,实现了一个header 和一个key_node 的对应
        :param node_items: 输入一张图片上的raw data
        :return:  返回一张图上可能出现的header_item
        """
        header_in_this_page = []
        # 如果设置了pk ，将pk 放在最后设置，因为pk 的内容可能是被cut 出来的
        header_for_pk = []

        # 对非pk 的head 先搜索
        for header_item in self.header_item_list:
            if self.prime_key is not None and header_item.head_type in self.prime_key:
                header_for_pk.append(header_item)
                continue

            header_item.search_key_node_list(node_items)
            if header_item.has_key_node:
                header_in_this_page.extend(header_item.assign_key_node())

        # 再对pk 搜索
        for header_item in header_for_pk:
            header_item.search_key_node_list(node_items)
            if header_item.has_key_node:
                header_in_this_page.extend(header_item.assign_key_node())
        return header_in_this_page
