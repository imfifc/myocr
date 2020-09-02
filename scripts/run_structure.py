import sys
from pathlib import Path

sys.path.insert(0, '../')
sys.path.insert(0, '../ocr_structuring')
import multiprocessing

multiprocessing.freeze_support()
from scripts.common_args import get_common_parser
from ocr_structuring.local.procedure import StsServerConfig, run
from ocr_structuring.easy_test import run as easy_test_run

if __name__ == '__main__':
    def parse_args():
        parser = get_common_parser()
        parser.add_argument('--class_name', required=True, help='结构化的类型')
        parser.add_argument('--gt_dir', required=True, help='原始图片用于 CRNN 重识别')
        parser.add_argument('--raw_dir', required=True, help='存放 batch_server 输出的结果')
        parser.add_argument('--output_dir', required=True, help='保存新的结构化结果的目录')
        parser.add_argument('--test_output_dir', default=None, help='保存 easy_test 的输出结果')
        parser.add_argument('--num_processes', type=int, default=1, help='跑结构化的进程数')
        parser.add_argument('--target_fid', default=None, help='指定跑某一个文件')
        parser.add_argument('--skip_load_tp_config', action='store_true',
                            help='不加载模板结构化的配置文件，对于调试非模板的结构化可以提高调试效率')
        parser.add_argument('--not_ltrb', action='store_true')

        parser.add_argument('--sts', action='store_true', help='是否发送数据到结构化 debug 工具后台')
        parser.add_argument('--sts_url', default='http://172.18.192.89:42002/', help='结构化调优工具地址')
        parser.add_argument('--sts_category', default='default')
        parser.add_argument('--sts_tag', default='default', help='category 下的二级分类，category 和 tag 会检查唯一性')
        parser.add_argument('--sts_dataset', default='default', help='gt 的子目录名称')
        parser.add_argument('--sts_skip_structure', action='store_true',
                            help='在没有写结构化代码前，把 raw data 发送到 debug 工具')
        parser.add_argument('--skip_easy_test', action='store_true',
                            help='跳过easy test')

        args = parser.parse_args()

        args.gt_dir = Path(args.gt_dir)
        args.raw_dir = Path(args.raw_dir)
        args.output_dir = Path(args.output_dir)
        args.ltrb = not args.not_ltrb

        if not args.gt_dir.exists():
            parser.error(f'gt_dir not exist: {args.gt_dir}')

        if not args.raw_dir.exists():
            parser.error(f'raw_dir not exist: {args.raw_dir}')

        if not args.output_dir.exists():
            print(f'Creat output dir {args.output_dir}')
            args.output_dir.mkdir(parents=True)

        if not args.sts:
            args.sts_cfg = None
        else:
            args.sts_cfg = StsServerConfig(url=args.sts_url,
                                           category=args.sts_category,
                                           name=args.sts_tag,
                                           dataset_name=args.sts_dataset)
            args.sts_cfg.check_exit()

        return args


    cmd_args = parse_args()

    run(
        class_name=cmd_args.class_name,
        gt_dir=cmd_args.gt_dir,
        raw_dir=cmd_args.raw_dir,
        output_dir=cmd_args.output_dir,
        num_processes=cmd_args.num_processes,
        target_fid=cmd_args.target_fid,
        ltrb=cmd_args.ltrb,
        should_init_tp_structure=not cmd_args.skip_load_tp_config,
        sts_cfg=cmd_args.sts_cfg,
        sts_skip_structure=cmd_args.sts_skip_structure
    )

    if cmd_args.test_output_dir is None:
        cmd_args.test_output_dir = Path(str(cmd_args.output_dir) + '_easy_test')
    else:
        cmd_args.test_output_dir = Path(cmd_args.test_output_dir)

    if not cmd_args.test_output_dir.exists():
        print(f'Creat test_output_dir {cmd_args.test_output_dir}')
        cmd_args.test_output_dir.mkdir(parents=True)
    if cmd_args.table_compare_values:
        cmd_args.table_compare_values = cmd_args.table_compare_values

    if not cmd_args.skip_easy_test:
        easy_test_run(
            gt_dir=cmd_args.gt_dir,
            pred_dir=cmd_args.output_dir,
            output_dir=cmd_args.test_output_dir,
            table_compare_method=cmd_args.table_compare_method,
            table_compare_unique_key=cmd_args.table_compare_unique_key,
            table_compare_values=cmd_args.table_compare_values,
            ignore_items=cmd_args.ignore_items if cmd_args.ignore_items is not None else [],
            compare_item_group_path=cmd_args.compare_item_group
        )
