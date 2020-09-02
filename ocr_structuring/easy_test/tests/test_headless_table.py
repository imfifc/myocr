import unittest
import json
import os

from typing import Dict, List
from ocr_structuring.easy_test.table_item import TableItem

gt_table = [
    [
        "项目",
        "附注",
        "2014年16月31日",
        "2013年12月31日"
    ],
    [
        "流动资产：",
        "&&",
        "&&",
        "&&"
    ]
]

pred_table = [
    [
        "项目",
        "附注",
        "2014年12月31日",
        "2013年12月31日"
    ],
    [
        "流动资产：",
        "123",
        "",
        ""
    ],
]


class TestHeadlessTableItem(unittest.TestCase):
    def test_by_row_headless(self):
        titem = TableItem('table')
        titem.compare_by_row_headless(gt_table, pred_table, None)

        self.assertEqual(len(titem.items), 1)

        self.assertTrue('headless_table' in titem._items)

        item = titem._items['headless_table']
        print(item.name)
        self.assertEqual(item.cnt_gt, 8)
        self.assertEqual(item.cnt_invalid_gt, 3)
        self.assertEqual(item.cnt_pass_invalid_gt, 1)
        self.assertEqual(item.cnt_pred, 8)
        self.assertEqual(item.cnt_pred_err, 4)
        self.assertEqual(item.cnt_pred_pass, 6)
        self.assertEqual(item.cnt_pred_pass_hit, 4)
        self.assertEqual(item.cnt_pred_pass_err, 2)


if __name__ == '__main__':
    unittest.main()
