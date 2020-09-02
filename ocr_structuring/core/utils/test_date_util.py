from unittest import TestCase

from ocr_structuring.core.utils import date_util


class TestDateUtil(TestCase):
    def test_format_date_fields(self):
        self.assertEquals(['2018', '02', '11'], date_util.format_date_fields('18', '2', '11', 1949))
        self.assertEquals(['2018', '02', '11'], date_util.format_date_fields('018', '2', '11', 1949))
        self.assertEquals(['2018', '02', '11'], date_util.format_date_fields('2018', '2', '11', 1949))
        self.assertEquals(['1998', '02', '11'], date_util.format_date_fields('98', '2', '11', 1949))
        self.assertEquals(['1998', '02', '11'], date_util.format_date_fields('998', '2', '11', 1949))
        self.assertEquals(['1998', '02', '11'], date_util.format_date_fields('1998', '2', '11', 1949))

    def test_parse_date(self):
        def aml(date_text, expects: str):
            """assert most like"""
            dates = date_util.parse_date(date_text, 1900, 2099)
            if dates.most_possible_item is None:
                raise AssertionError(date_text, '----------', expects)
            self.assertEquals(dates.most_possible_item.to_string(), expects)

        aml('2019-11-23', '2019-11-23')
        aml('2019ab11cd23', '2019-11-23')
        aml('2019年1月3日', '2019-01-03')
        aml('2019年1月03日', '2019-01-03')
        aml('2019年01月3日', '2019-01-03')
        aml('2019年01月03日', '2019-01-03')
        aml('20191123', '2019-11-23')
        aml('2019-1123', '2019-11-23')
        aml('2019-112', '2019-11-02')
        aml('2019-1-2', '2019-01-02')
        aml('0190123', '2019-01-23')
        aml('19abc0123', '2019-01-23')  # 如果设置的最小业务年份为1900，则还会生成'1901-02-03'
        # aml('90123', '1990-12-03') # TODO 修一下
        aml('2022. 0118', '2022-01-18')
        aml('2025-_10-08', '2025-10-08')
        aml('2025-01-20-长期', '2025-01-20')
