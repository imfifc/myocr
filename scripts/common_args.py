import argparse


def get_common_parser():
    parser = argparse.ArgumentParser()
    # easy test 中表格比较相关的参数
    parser.add_argument('--table_compare_method', default='by_row', choices=['by_row', 'by_row_headless', 'by_key'],
                        help='only by_row or by_key is supported')
    parser.add_argument('--table_compare_unique_key', default=None)
    parser.add_argument('--table_compare_values', default=None, nargs='+')

    parser.add_argument('--compare_item_group', default=None, help='easy_test 统计时会额外统计某些字段的准确率')
    parser.add_argument('--ignore_items', default=(), nargs='+', help='easy_test 统计时不会统计这些项目的准确率')
    return parser
