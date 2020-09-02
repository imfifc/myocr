from ...utils.table.body import BodyRow
from ...utils.table.header import HeaderRow


class Table:
    def __init__(self, header_row: HeaderRow, rows: [BodyRow]) -> None:
        self.header_row = header_row
        self.rows = rows
