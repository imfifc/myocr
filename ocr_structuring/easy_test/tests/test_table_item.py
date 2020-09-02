import unittest
import json
import os

from typing import Dict, List
from ocr_structuring.easy_test.table_item import TableItem

gt_table = [
    {'name': '医疗费', 'charge': 1.0},
    {'name': '治疗费', 'charge': '2.0'},
    {'charge': '2.0'},
    {'name': '诊察费'},
]

pred_table = [
    {'name': '医疗费', 'charge': ''},
    {'name': '治疗费', 'charge': 2.0},
    {'name': '检查', 'charge': '2.0'},
]


class TestTableItem(unittest.TestCase):
    def test_by_row(self):
        titem = TableItem('table')
        titem.compare_by_row(gt_table, pred_table, None)
        self.assertTrue(list(titem._items.keys()) == ['name', 'charge'])
        name_item = titem._items['name']
        charge_item = titem._items['charge']

        self.assertEqual(3, name_item.cnt_gt)
        self.assertEqual(2, name_item.cnt_pred)
        self.assertEqual(2, name_item.cnt_pred_pass)
        self.assertEqual(2, name_item.cnt_pred_pass_hit)
        self.assertEqual(1, name_item.cnt_pred_err)
        self.assertEqual('诊察费', name_item.wrong_items[0].gt)
        self.assertEqual(0, name_item.cnt_pred_pass_err)
        self.assertEqual(0, name_item.cnt_invalid_gt)
        self.assertEqual(0, name_item.cnt_pass_invalid_gt)

        self.assertEqual(3, charge_item.cnt_gt)
        self.assertEqual(3, charge_item.cnt_pred)
        self.assertEqual(2, charge_item.cnt_pred_pass)
        self.assertEqual(1, charge_item.cnt_pred_err)
        self.assertEqual(0, charge_item.cnt_pred_pass_err)

    def test_by_key(self):
        titem = TableItem('table')
        titem.compare_by_special_key(gt_table, pred_table, None, unique_key='name')
        self._byKeyAssertEqual(titem)

    def test_by_key_with_value(self):
        titem = TableItem('table')
        titem.compare_by_special_key(gt_table, pred_table, None, unique_key='name', value_key=['charge'])
        self._byKeyAssertEqual(titem)

    def test_by_key_with_not_exist_value(self):
        titem = TableItem('table')
        titem.compare_by_special_key(gt_table, pred_table, None, unique_key='name', value_key=['charge', 'price'])
        self._byKeyAssertEqual(titem)

    def _byKeyAssertEqual(self, titem):
        self.assertTrue(list(titem._items.keys()) == ['name', 'charge'])
        name_item = titem._items['name']
        print(name_item.acc)
        self.assertEqual(3, name_item.cnt_gt)
        self.assertEqual(3, name_item.cnt_pred)
        self.assertEqual(2, name_item.cnt_pred_pass)
        self.assertEqual(2, name_item.cnt_pred_pass_hit)
        self.assertEqual(1, name_item.cnt_pred_err)
        self.assertEqual(0, name_item.cnt_pred_pass_err)
        self.assertEqual(0, name_item.cnt_invalid_gt)
        self.assertEqual(0, name_item.cnt_pass_invalid_gt)

        charge_item = titem._items['charge']
        print(charge_item.acc)
        self.assertEqual(2, charge_item.cnt_gt)
        self.assertEqual(2, charge_item.cnt_pred)
        self.assertEqual(1, charge_item.cnt_pred_pass)
        self.assertEqual(1, charge_item.cnt_pred_pass_hit)
        self.assertEqual(1, charge_item.cnt_pred_err)
        self.assertEqual(0, charge_item.cnt_pred_pass_err)
        self.assertEqual(0, charge_item.cnt_invalid_gt)
        self.assertEqual(0, charge_item.cnt_pass_invalid_gt)


if __name__ == '__main__':
    unittest.main()
