import unittest
from ocr_structuring.easy_test.item import Item


class TestEasyTestItem(unittest.TestCase):
    def test_item(self):
        item = Item('dummy')
        data = [
            {'gt': 1, 'pred': 1, 'hit': True},
            {'gt': 2, 'pred': 2, 'hit': True},
            {'gt': "&&", 'pred': 3, 'hit': False},  # gt 无效，无论 pred 是什么，都认为错误
            {'gt': "&&", 'pred': "&&", 'hit': False},  # gt 无效，无论 pred 是什么，都认为错误
            {'gt': '', 'pred': '', 'hit': True},  # gt 和 pred 都为空，认为正确
        ]
        for d in data:
            gt, pred, hit = d['gt'], d['pred'], d['hit']
            self.assertEqual(hit, item.compare(gt, pred, 0))

        print('acc', item.acc)
        print('keep', item.keep)
        print('keep_acc', item.keep_acc)
        print('valid_keep_acc', item.valid_keep_acc)
        print('valid_acc', item.valid_acc)
        self.assertEqual(5, item.cnt_gt)
        self.assertEqual(2, item.cnt_invalid_gt)
        self.assertEqual(5, item.cnt_pred)
        self.assertEqual(5, item.cnt_pred_pass)
        self.assertEqual(2, item.cnt_pred_pass_err)
        self.assertEqual(3, item.cnt_pred_pass_hit)

        self.assertEqual(0.6, item.acc)
        self.assertEqual(1, item.keep)
        self.assertEqual(0.6, item.keep_acc)


if __name__ == '__main__':
    unittest.main()
