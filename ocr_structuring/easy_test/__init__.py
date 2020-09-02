from pathlib import Path

from .tester import Tester


def run(
    gt_dir: Path,
    pred_dir: Path,
    output_dir: Path,
    table_compare_method: str = "by_row",
    table_compare_unique_key=None,
    table_compare_values=None,
    ignore_items=(),
    compare_item_group_path=None,
    thresh_search: bool = False,
):
    tester = Tester(
        gt_dir,
        pred_dir,
        output_dir,
        table_compare_method,
        table_compare_unique_key,
        table_compare_values,
        ignore_items,
        compare_item_group_path,
        thresh_search
    )
    tester.run()
    if thresh_search:
        tester.run_thresh_search()
