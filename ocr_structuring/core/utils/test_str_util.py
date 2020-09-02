from unittest import TestCase

from ocr_structuring.core.utils import str_util


class TestStrUtil(TestCase):
    def test_find_sub(self):
        self.assertEquals((5, 7), str_util.find_sub('2015-0223', 2, key=lambda x: 1 <= int(x) <= 12, start_index=4))
        self.assertEquals((5, 7), str_util.find_sub('2015-0223', 2, key=lambda x: 1 <= int(x) <= 12, start_index=4,
                                                    reverse=True))

    def test_digitalizing(self):
        self.assertEquals('00.753000', str_util.digitalizing('ab.753000'))
        self.assertEquals('11.753000', str_util.digitalizing('ab.753000', lambda x, index, collected: '1'))
        self.assertEquals(
            '1.0753000',
            str_util.digitalizing(
                'abc753000',
                lambda x, index, collected: '1' if index == 0 else '.' if '.' not in collected else '0'
            )
        )

    def test_add_dot(self):
        self.assertEquals('123.0000', str_util.add_dot('1230000', 123, 999))
        self.assertEquals(None, str_util.add_dot('990000', 123, 199))

    def test_contain_continue_nums(self):
        self.assertTrue(str_util.contain_continue_nums('', 0))
        self.assertTrue(str_util.contain_continue_nums('1123', 4))
        self.assertTrue(str_util.contain_continue_nums('1.123', 3))
        self.assertFalse(str_util.contain_continue_nums('1123', 5))
        self.assertFalse(str_util.contain_continue_nums('陆百元', 1))
        self.assertTrue(str_util.contain_continue_nums('陆百元', 0))
