import copy
import sys
from typing import Optional, Dict, Tuple

import cv2

from .body import BodyCell, BodyRow
from .footer_cell_matcher import footer_cell_match, FooterCellMatchContext
from ...utils import str_util
from ...utils.bbox import BBox
from ...utils.node_item import NodeItem
from ...utils.table import Table
from ...utils.table.body_cell_filter import body_cell_filter, BodyCellFilterContext as BodyCellFilterContext
from ...utils.table.body_cell_matcher import BodyCellMatchContext, body_cell_match
from ...utils.table.col import Col
from ...utils.table.footer import Footer
from ...utils.table.header import HeaderRow, HeaderCell
from ...utils.table.header_cell_matcher import HeaderMatchContext, header_cell_match
from ...utils.table.row import body_row_filter, filter_body_row


class ColCfg:
    # TODO: 改造为真正的builder模式
    def __init__(self, name: str, gt_text: str, header_cell_filters: [callable], body_cell_filters: [body_cell_filter],
                 need_structure: bool = True) -> None:
        self.name = name
        self.gt_text = gt_text
        self.header_cell_filters = header_cell_filters
        self.body_cell_filters = body_cell_filters
        self.need_structure = need_structure


class VirtualBodyCell(BodyCell):

    def __init__(self, bbox):
        super().__init__(None)
        self._bbox = bbox

    @property
    def bbox(self):
        return self._bbox

    @property
    def text(self):
        return None

    @property
    def scores(self):
        return []

    def __str__(self):
        return '虚拟cell[{}]'.format(self._bbox)


class TableBuilder:
    def __init__(self):
        self.cols: [Col] = []
        self.node_items: Dict[str, NodeItem] = {}
        self.body_row_filters = []
        self.footer_cell_matchers: [footer_cell_match] = []
        self.img = None
        self.above_offset = (0, 0)

    def add_col(self, col: Col) -> 'TableBuilder':
        self.cols.append(col)
        return self

    def add_cols(self, cols: [Col]) -> 'TableBuilder':
        self.cols += cols
        return self

    def set_node_items(self, node_items: Dict[str, NodeItem]) -> 'TableBuilder':
        self.node_items = node_items
        return self

    def add_body_row_filter(self, f: body_row_filter) -> 'TableBuilder':
        self.body_row_filters.append(f)
        return self

    def add_body_row_filters(self, fs: [body_row_filter]) -> 'TableBuilder':
        self.body_row_filters += fs
        return self

    def add_footer_cell_matcher(self, matcher: footer_cell_match) -> 'TableBuilder':
        self.footer_cell_matchers.append(matcher)
        return self

    def add_footer_cell_matchers(self, matchers: [footer_cell_match]) -> 'TableBuilder':
        self.footer_cell_matchers += matchers
        return self

    def set_img(self, img) -> 'TableBuilder':
        self.img = img
        return self

    def set_above_offset(self, offset: Tuple[float or str, float or str]) -> 'TableBuilder':
        """
        设置前景偏移
        :param offset: (x偏移，y偏移)，可以是数字或百分比字符串，如(10, -20)或('10%', '-20%')
        :return:
        """
        self.above_offset = offset
        return self

    def build(self) -> Table:
        if len(self.cols) == 0:
            raise AssertionError('表头未配置')
        if len(self.node_items) == 0:
            raise AssertionError('未设置node_items')

        header_row = self._find_tab_header_row(self.cols, self.node_items)
        footer = self._find_tab_footer(self.node_items, self.footer_cell_matchers, header_row)
        if all([cell.node_item is None for cell in header_row.cells]):
            return Table(header_row, [])
        # TODO: 确认表头时还应传入表尾，使用头、尾中间左侧表头右边的body_cells定位
        TableBuilder._confirm_headers(self.node_items, header_row)
        # self._imshow_header(header_row)
        # 查找列的时候，把node_items进行偏移
        self._build_above_offset_node_items(header_row.node_items)
        self._find_tab_cols(self.node_items, header_row)
        # self._imshow_cols(self.cols)
        self._filter_col_cells(footer)
        # self._imshow_cols(self.cols)
        # 构造rows
        rows = self._build_rows()
        # 过滤行
        rows = self._filter_rows(rows, header_row, footer)
        return Table(header_row, rows)

    def _imshow_header(self, header_row: HeaderRow):
        self._imshow([c.bbox for c in header_row.cells])

    def _imshow_cols(self, cols: [Col]):
        bboxes = []
        for col in cols:
            bboxes.append(col.header.bbox)
            for cell in col.cells:
                bboxes.append(cell.bbox)
        self._imshow(bboxes)

    def _imshow(self, bboxes: [BBox]):
        img = self.img.copy()
        for bbox in bboxes:
            cv2.rectangle(img, bbox.left_top_pnt, bbox.right_bottom_pnt, (0, 0, 255), 4)
        from tempfile import NamedTemporaryFile
        img_path = NamedTemporaryFile().name + '.jpg'
        cv2.imwrite(img_path, img)
        import os
        os.popen('python3 /Users/ctc/python/src/ocr-structuring/scripts/drawing.py {}'.format(img_path))

    def _filter_col_cells(self, footer: Footer):
        for index, col in enumerate(self.cols):
            new_cells = []
            above_cell = None
            for cell in col.cells:
                if self.body_cell_matches(cell, above_cell, col.header, footer, col.body_matchers):
                    new_cells.append(cell)
                    above_cell = cell
            col.cells = new_cells

    @staticmethod
    def body_cell_matches(cell: BodyCell, above_cell, header: HeaderCell, footer: Footer,
                          matchers: [body_cell_match]) -> bool:
        """
        判断body_cell是否与所有的匹配器匹配
        :param cell:
        :param header:
        :param matchers:
        :return:
        """
        for m in matchers:
            if not m(BodyCellMatchContext(cell, above_cell, header, footer)):
                return False
        return True

    def _filter_rows(self, rows: [BodyRow], header_row: HeaderRow, footer_row: Footer) -> [BodyRow]:
        """
        :param header_row:
        :param footer_row:
        :return:
        """

        # 过滤掉无效的行
        body_row_filters = self.body_row_filters
        filtered_rows = []
        for row_idx, row in enumerate(rows):
            filtered_row = filter_body_row(body_row_filters, rows, filtered_rows, row_idx, header_row, footer_row)
            if filtered_row:
                filtered_rows.append(filtered_row)
        return filtered_rows

    def _build_rows(self) -> [BodyRow]:
        cols = self.cols
        rows = []
        # cell最多的列，TODO：可能有多个最多的列，添加虚拟cell时总数需要++
        cell_max_col = max(cols, key=lambda x: len(x.cells))
        cell_max_col_idx = cols.index(cell_max_col)
        max_row_count = len(cell_max_col.cells)
        if max_row_count == 0:
            return rows

        # 先找出每一行的锚点列
        row_idx = 0
        while True:
            if row_idx >= max_row_count:
                break
            min_y_cell_idx = TableBuilder._find_min_y_cell_idx(cols, row_idx)

            # 向左遍历
            for col_idx in range(min_y_cell_idx - 1, -1, -1):
                col = cols[col_idx]
                if len(col.cells) <= row_idx:
                    # 这一列已经没有cell的时候，追加一个虚拟的
                    virtual_cell = TableBuilder._create_virtual_body_cell(col, row_idx, cols[col_idx + 1])
                    col.cells.append(virtual_cell)
                    # 如果增加的列正好是行数最多的列，则最大行号加1
                    if col_idx == cell_max_col_idx:
                        max_row_count += 1
                    continue

                cell = col.cells[row_idx]
                if not TableBuilder._is_same_line(cell, col, row_idx, cols[col_idx + 1]):
                    # 这一列有，但不是同一行，则插入一个
                    virtual_cell = TableBuilder._create_virtual_body_cell(col, row_idx, cols[col_idx + 1])
                    col.cells.insert(row_idx, virtual_cell)
                    if col_idx == cell_max_col_idx:
                        max_row_count += 1
                    continue
            # 向右遍历
            for col_idx in range(min_y_cell_idx + 1, len(cols)):
                col = cols[col_idx]
                if len(col.cells) <= row_idx:
                    # 这一列已经没有cell的时候，追加一个虚拟的
                    virtual_cell = TableBuilder._create_virtual_body_cell(col, row_idx, cols[col_idx - 1])
                    col.cells.append(virtual_cell)
                    # 如果增加的列正好是行数最多的列，则最大行号加1
                    if col_idx == cell_max_col_idx:
                        max_row_count += 1
                    continue

                cell = col.cells[row_idx]
                if not TableBuilder._is_same_line(cell, col, row_idx, cols[col_idx - 1]):
                    # 这一列有，但不是同一行，则插入一个
                    virtual_cell = TableBuilder._create_virtual_body_cell(col, row_idx, cols[col_idx - 1])
                    col.cells.insert(row_idx, virtual_cell)
                    if col_idx == cell_max_col_idx:
                        max_row_count += 1
                    continue

            row_idx += 1

        rows = []
        for i in range(max_row_count):
            cells = []
            for col in cols:
                cell = col.cells[i]
                if cell.node_item is None:
                    cells.append(None)
                else:
                    cells.append(cell)
            rows.append(BodyRow(cells))
        return rows

    @staticmethod
    def _is_same_line(cell: BodyCell, col: Col, row_idx: int, reference_col: Col) -> bool:
        # 判断cell是否和参考列的row_idx对应的cell共线，只需要判断距离其header的距离是否在一定阈值内
        reference_header_distance = reference_col.cells[row_idx].bbox.center[1] - reference_col.header.bbox.center[1]
        this_header_distance = cell.bbox.center[1] - col.header.bbox.center[1]
        # TODO: 目前是判断cell顶端到header顶端的距离 - 参考cell到参考header顶端的距离 < cell的高度的三分之一，这里可以加入配置
        return this_header_distance - reference_header_distance <= cell.bbox.height * 0.3

    @staticmethod
    def _create_virtual_body_cell(col: Col, row_idx, reference_col: Col) -> BodyCell:
        above_cell = TableBuilder._find_first_not_virtual_cell_above(col, row_idx)
        reference_cell = reference_col.cells[row_idx]
        if above_cell is None:
            # 上方没有cell，则距离header的距离 = 参照点距离上侧的距离
            top = reference_cell.bbox.top - reference_col.header.bbox.bottom + col.header.bbox.bottom
            left = col.header.bbox.left
            right = col.header.bbox.right
            bottom = reference_cell.bbox.bottom - reference_cell.bbox.top + top
        else:
            # 上方有cell，则距离left, right = 上方的left, right
            top = reference_cell.bbox.top - reference_col.header.bbox.bottom + col.header.bbox.bottom
            left = above_cell.bbox.left
            right = above_cell.bbox.right
            bottom = above_cell.bbox.bottom - above_cell.bbox.top + top
        return VirtualBodyCell(BBox([left, top, right, bottom]))

    @staticmethod
    def _find_first_not_virtual_cell_above(col, row_idx) -> BodyCell or None:
        for i in range(row_idx - 1, -1, -1):
            if col.cells[i].node_item is not None:
                return col.cells[i]
        return None

    @staticmethod
    def _find_min_y_cell_idx(cols: [Col], row_idx: int) -> int:
        idx = -1
        min_y_cell = None
        for i, col in enumerate(cols):
            if len(col.cells) <= row_idx:
                continue
            cell = col.cells[row_idx]
            if min_y_cell is None or cell.bbox.is_above(min_y_cell.bbox):
                min_y_cell = cell
                idx = i
        return idx

    @staticmethod
    def _find_same_line_cell(col, anchor_cell):
        nearest_cell = None
        if len(col.cells) > 0:
            nearest_cell = sorted(col.cells, key=lambda c: c.bbox.center_dis(anchor_cell.bbox))[0]
        if anchor_cell.bbox.is_same_line(nearest_cell.bbox):
            return nearest_cell
        else:
            return None

    @staticmethod
    def _find_tab_footer(node_items: Dict[str, NodeItem], footer_cell_matchers: [footer_cell_match],
                         header_row: HeaderRow) -> Footer:
        footer_items = []
        for _, node_item in node_items.items():
            if node_item.bbox.is_below(header_row.bbox) and TableBuilder.is_match_footer(node_item,
                                                                                         footer_cell_matchers,
                                                                                         header_row):
                footer_items.append(node_item)
        return Footer(footer_items)

    @staticmethod
    def is_match_footer(node_item: NodeItem, footer_cell_matchers: [footer_cell_match], header_row: HeaderRow):
        for matcher in footer_cell_matchers:
            if matcher(FooterCellMatchContext(node_item, header_row)):
                return True
        return False

    @staticmethod
    def _find_match_header_indexes(cols: [Col], node_items: Dict[str, NodeItem], node_item: NodeItem):
        result = []
        for index, col in enumerate(cols):
            ctx = HeaderMatchContext(node_items, node_item, col.header)
            if TableBuilder._is_match_header(ctx, col.header_matchers):
                result.append(index)
        return result

    @staticmethod
    def _is_match_header(ctx: HeaderMatchContext, matchers: [header_cell_match]) -> bool:
        for hm in matchers:
            if hm(ctx):
                # TODO: 只要有一个能匹配上就返回True?
                return True
        return False

    @staticmethod
    def _find_tab_header_row(cols: [Col], node_items: Dict[str, NodeItem],
                             exclude_node_items: [NodeItem] = []) -> HeaderRow:
        """查找表头节点s"""
        header_texts = [col.header.gt_text for col in cols]
        header_names = [col.header.name for col in cols]
        possible_nodes = [[] for _ in header_names]
        for _, node_item in node_items.items():
            indexes = TableBuilder._find_match_header_indexes(cols, node_items, node_item)
            for index in indexes:
                possible_nodes[index].append(node_item)

        header_row = HeaderRow(header_names, header_texts)
        for i in range(len(header_texts)):
            cell = header_row.cells[i]
            if len(possible_nodes[i]) == 1:
                node_item = possible_nodes[i][0]
                node_text_no_symbols = str_util.remove_symbols_and_space(node_item.text)
                cell.confirmed = node_item.text and node_text_no_symbols == header_row.cells[i].gt_text
                cell.node_item = node_item
        for i in range(len(header_texts)):
            cell = header_row.cells[i]
            if len(possible_nodes[i]) > 1:
                node_item = TableBuilder._find_possible_node_item(possible_nodes, i)
                if not node_item:
                    continue
                cell.node_item = node_item
                node_text_no_symbols = str_util.remove_symbols_and_space(node_item.text)
                cell.confirmed = node_item.text and node_text_no_symbols == header_row.cells[i].gt_text
        return header_row

    @staticmethod
    def _find_possible_node_item(possible_nodes: [], index) -> ():
        left_confirmed = None
        right_confirmed = None
        for i in range(index - 1, -1, -1):
            if len(possible_nodes[i]) == 1:
                left_confirmed = possible_nodes[i][0]
                break
        for i in range(index + 1, len(possible_nodes)):
            if len(possible_nodes[i]) == 1:
                right_confirmed = possible_nodes[i][0]

        results = []
        for node in possible_nodes[index]:
            if left_confirmed and left_confirmed.bbox.center[0] >= node.bbox.center[0]:
                continue
            if right_confirmed and right_confirmed.bbox.center[0] <= node.bbox.center[0]:
                continue
            results.append(node)
        if len(results) > 0:
            return results[0]
        return None

    def _find_tab_cols(self, node_items: Dict[str, NodeItem], header_row: HeaderRow) -> None:
        """找出所有的表头列"""
        body_cells = [[] for _ in range(len(header_row.cells))]
        for _, node_item in node_items.items():
            index = TableBuilder._find_nearest_node_item(node_item, header_row.node_items)
            header_cell = header_row.cells[index]
            if node_item.bbox.left > header_cell.bbox.right + header_cell.bbox.width * 2 \
                    or node_item.bbox.right < header_cell.bbox.left - header_cell.bbox.width * 2 \
                    or node_item.bbox.bottom < header_cell.bbox.top - header_cell.bbox.height * 2:
                # 去除离header左、右、上太远的item
                continue
            body_cells[index].append(BodyCell(node_item))
        for index, cells in enumerate(body_cells):
            self.cols[index].cells = sorted(cells, key=lambda c: c.bbox.top)
            self.cols[index].header = header_row.cells[index]

    @staticmethod
    def _filter_body_cell(ctx: BodyCellFilterContext, filters: [body_cell_filter]) -> Optional[NodeItem]:
        for f in filters:
            item = f(ctx)
            ctx.node_item = item
            if item is None:
                break
        return ctx.node_item

    @staticmethod
    def _find_nearest_node_item(node_item, node_items: [NodeItem]) -> int:
        """从目标item中查找最近的一个，返回其索引。默认策略是中心点，可通过默认参数扩展"""
        distance = sys.maxsize
        index = -1
        for i, ni in enumerate(node_items):
            the_distance = ni.bbox.center_dis(node_item.bbox)
            if the_distance < distance:
                distance = the_distance
                index = i
        return index

    @staticmethod
    def _confirm_headers(node_items: Dict[str, NodeItem], header_row: HeaderRow) -> None:
        # 分割过长的
        for cell in header_row.cells:
            if cell.confirmed or cell.node_item is None:
                continue
            gt_text_len = len(cell.gt_text)
            node_text_len = len(cell.node_item.text)
            if gt_text_len < node_text_len:
                node_item_split = TableBuilder._split_header_node(cell.node_item, cell.gt_text)
                if node_item_split is not None:
                    cell.node_item = node_item_split
                    cell.confirmed = True

        # TODO: 至少要有一个header cell已经confirmed，这里需要考虑
        confirmed_index = -1
        for i, cell in enumerate(header_row.cells):
            if header_row.cells[i].confirmed:
                confirmed_index = i
                break

        for i in range(confirmed_index - 1, -1, -1):
            # TODO: if header_row.cells[i].confirmed
            if header_row.cells[i].node_item is None:
                TableBuilder._confirm_header_by_right_header(node_items, header_row, i)

        for i in range(confirmed_index + 1, len(header_row.cells)):
            # TODO: if header_row.cells[i].confirmed
            if header_row.cells[i].node_item is None:
                TableBuilder._confirm_header_by_left_header(node_items, header_row, i)

    @staticmethod
    def _split_header_node(to_split_header_node: NodeItem, gt_text) -> NodeItem or None:
        if gt_text not in to_split_header_node.text:
            return None
        start_index = to_split_header_node.text.index(gt_text)
        gt_text_len = len(gt_text)
        return to_split_header_node.split(start_index, start_index + gt_text_len)

    @staticmethod
    def _confirm_header_by_right_header(node_items: Dict[str, NodeItem], header_row: HeaderRow, to_confirm_index):
        right_header = header_row.cells[to_confirm_index + 1]
        # todo confirm为false的，和cell为空的，这里暂时先填充cell为空的
        header = header_row.cells[to_confirm_index]
        left = right_header.bbox.left - right_header.bbox.width * 1.5
        top = right_header.bbox.top
        right = left + right_header.bbox.width
        bottom = right_header.bbox.bottom
        header.node_item = NodeItem([
            header.gt_text,
            int(left),
            int(top),
            int(right),
            int(bottom),
            0,
            [1 for _ in header.gt_text],
        ], ltrb=True)
        header.confirmed = True

    @staticmethod
    def _confirm_header_by_left_header(node_items: Dict[str, NodeItem], header_row: HeaderRow, to_confirm_index):
        header = header_row.cells[to_confirm_index]
        left_header = header_row.cells[to_confirm_index - 1]
        # todo 暂时直接找右边的单元格
        l_box = left_header.bbox
        left_most_header_node = None
        for _, node_item in node_items.items():
            node_box = node_item.bbox
            if node_box.right > l_box.right and node_box.is_same_line(l_box, 0.3):
                if (left_most_header_node is None or node_box.left < left_most_header_node.bbox.left) \
                        and node_box.left > left_header.bbox.right:
                    left_most_header_node = node_item

        # 分割
        if left_most_header_node and len(left_most_header_node.text) > len(header.gt_text):
            left_most_header_node = TableBuilder._split_header_node(left_most_header_node, header.gt_text)

        # 如果找到的表头已经在已知的表头中了，则放弃
        if left_most_header_node in header_row.node_items:
            left_most_header_node = None

        # 如果找到的left_most_header_node与left_header中间有item，则说明找到了右边的右边
        if left_most_header_node is not None:
            bbox = BBox([left_header.bbox.center[0], left_header.bbox.bottom, left_most_header_node.bbox.center[0],
                         left_header.bbox.bottom + left_header.bbox.height])
            if len([k for k, v in node_items.items() if bbox.contain_center(v.bbox)]) > 0:
                left_most_header_node = None

        if left_most_header_node is None:
            # 各种尝试后依然找不到，则生成一个虚拟的, TODO: 生成虚拟表头的策略
            # 若左侧有两个表头，则生成的表头宽度等于左侧两个表头的中点距离， width = left1.width, center = center_distance(left1, left2) + center(left1)
            # TODO: 根据右边的value_items生成表头
            if to_confirm_index >= 2:
                left_header1 = header_row.cells[to_confirm_index - 1]
                left_header2 = header_row.cells[to_confirm_index - 2]
                width = len(header.gt_text) * left_header1.bbox.width / len(left_header1.gt_text)
                center_x = left_header1.bbox.center_dis(left_header2.bbox) + left_header1.bbox.center[0]
                # TODO: 根据gt_text和左边两项的间距求left？
                left = center_x - width / 2
                top = left_header1.bbox.top
                bottom = left_header1.bbox.bottom
                right = left + width
                left_most_header_node = NodeItem(
                    [header.gt_text, int(left), int(top), int(right), int(bottom), 0,
                     [1 for i in range(len(header.gt_text))]], ltrb=True)
            else:
                width = len(header.gt_text) * left_header.bbox.width / len(left_header.gt_text)
                # TODO: left???
                left = left_header.bbox.right + left_header.bbox.width / 2
                top = left_header.bbox.top
                right = left + width
                bottom = left_header.bbox.bottom
                left_most_header_node = NodeItem(
                    [header.gt_text, int(left), int(top), int(right), int(bottom), 0,
                     [1 for i in range(len(header.gt_text))]], ltrb=True)
            # TODO: 左侧只有一个的时候
        header.node_item = left_most_header_node
        header.confirmed = True

    def _build_above_offset_node_items(self, exclude_node_items: [NodeItem]) -> Dict[str, NodeItem]:
        """
        获取偏移纠正后的node_items
        :return:
        """
        result = {}
        for uid, node_item in self.node_items.items():
            if node_item in exclude_node_items:
                result[uid] = node_item
            else:
                new_item = copy.deepcopy(node_item)
                node_item.bbox = self._offset_above(node_item.bbox)
                result[uid] = new_item
        return result

    def _offset_above(self, bbox: BBox) -> BBox:
        def value_to_pixel(value, base):
            check_error = ValueError(f'偏移量[{value}]必须为数字或包含%的字符串，如5或"-20%"')
            if isinstance(value, int) or isinstance(value, float):
                return value
            if isinstance(value, str):
                if len(value) < 2 or value[-1] != '%':
                    raise check_error
                percent_str = value[:-1]
                try:
                    percent_float = float(percent_str)
                    return base * percent_float / 100
                except Exception:
                    raise check_error
            raise check_error

        offset_x, offset_y = self.above_offset
        left = bbox.left + value_to_pixel(offset_x, bbox.left)
        top = bbox.top + value_to_pixel(offset_y, bbox.top)

        return BBox([left, top, bbox.right, bbox.bottom])
