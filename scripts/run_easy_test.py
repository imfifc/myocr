import sys

from scripts.common_args import get_common_parser

sys.path.insert(0, "../")
sys.path.insert(0, "../ocr_structuring")
from pathlib import Path
from ocr_structuring.easy_test import run

if __name__ == "__main__":

    def parse_args():
        parser = get_common_parser()
        parser.add_argument("--gt_dir")
        parser.add_argument("--pred_dir")
        parser.add_argument("--output_dir")
        parser.add_argument(
            "--thresh_search",
            action="store_true",
            help="是否进行每个字段的阈值搜索，如果设为 True，pred_dir 必须是 debug_server 保存的结构化结果",
        )
        args = parser.parse_args()

        args.gt_dir = Path(args.gt_dir)
        args.pred_dir = Path(args.pred_dir)
        args.output_dir = Path(args.output_dir)

        if not args.pred_dir:
            parser.error("pred_dr not exist: {}".format(args.pred_dir))

        if not args.gt_dir:
            parser.error("gt_dir not exist: {}".format(args.gt_dir))

        if not args.output_dir.exists():
            print(f"Creat output dir {args.output_dir}")
            args.output_dir.mkdir(parents=True)

        return args

    cmd = parse_args()

    run(
        cmd.gt_dir,
        cmd.pred_dir,
        cmd.output_dir,
        cmd.table_compare_method,
        cmd.table_compare_unique_key,
        cmd.table_compare_values,
        ignore_items=cmd.ignore_items,
        compare_item_group_path=cmd.compare_item_group,
        thresh_search=cmd.thresh_search,
    )
