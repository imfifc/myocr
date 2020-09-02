from ...utils.table import header_cell_matcher
from ...utils.table.body_cell_matcher import body_cell_match
from ...utils.table.header import HeaderCell


class Col:
    """表列，包含1个表头单元格和一组表体单元格"""
    # TODO: 分离表头与配置
    def __init__(self, header: HeaderCell, header_matchers: [header_cell_matcher], body_matchers: [body_cell_match]):
        self.header = header
        self.cells = []
        self.header_matchers = header_matchers
        self.body_matchers:[body_cell_match] = body_matchers

    def __str__(self):
        return '{}[cell × {}]'.format(self.header.gt_text, len(self.cells))
