"""
结构化工具的实验对比功能，不支持跨实验室的比较，同实验室的两组实验进行比较，也无法看到两组实验的具体 **差异**。
该脚本可以输出两组实验的具体差异

使用限制
---------

- 两次实验的数据集必须是 dp 上同一个数据集
- 两组实验的字段必须是一致的
- 仅支持简单的 key-value 形式的结构化结果

执行脚本
---------

.. code:: bash

    PYTHONPATH=`pwd` python3 scripts/compare_st_experiment.py \\
        --st_url http://stf.cloud.tianrang-inc.com/ \\
        --output ./tmp \\
        --exp 1423 idcard_res18 1417 idcard_res50

- **st_url**：结构化工具的 url，默认 `http://st.cloud.tianrang-inc.com/`
- **output**：保存结果的目录，按每个字段分开保存比对结果 `{field_name}_{expid1}_{expid2}.json`
- **exp**：数组，两组实验的 id (例如，http://stf.cloud.tianrang-inc.com/experiment/detail/1423 的 id 为 1423)，以及对应的 tag，tag 可以自定设定，仅用作保存比对结果时方便查看

保存结果示例
-------------

比对文件已经按照字段区分，每个比对结果文件中会保存三个 key：

- same_gt_id_same_error：在同一个文件上错误 **相同**
- same_gt_id_diff_error：在同一个文件上错误 **不同**
- diff_gt_id：不同文件上的错误

比对结果中的 `raw_data_id` 可以用来在结构化工具中搜索对应的文件

.. code-block:: json

    {
      "same_gt_id_same_error": {
        "712582": {
          "1423_idcard_res18": {
            "gt_id": 712582,
            "raw_data_id": 16516,
            "exp_result_id": 51536,
            "gt__": "江西省南昌市新建县长堎镇建设路599号7栋1单元601户",
            "pred": "江西省南昌市新建县长凌镇建设路599号7栋1单元601户",
            "edit_distance": 1
          },
          "1417_idcard_res50": {
            "gt_id": 712582,
            "raw_data_id": 16401,
            "exp_result_id": 51019,
            "gt__": "江西省南昌市新建县长堎镇建设路599号7栋1单元601户",
            "pred": "江西省南昌市新建县长凌镇建设路599号7栋1单元601户",
            "edit_distance": 1
          }
        }
      },
      "same_gt_id_diff_error": {
        "712651": {
          "1423_idcard_res18": {
            "gt_id": 712651,
            "raw_data_id": 16584,
            "exp_result_id": 51516,
            "gt__": "广东省饶平县三饶镇南联何厝向南后围13号",
            "pred": "广东省饶平县三饶镇南联何唐向南后围13号",
            "edit_distance": 1
          },
          "1417_idcard_res50": {
            "gt_id": 712651,
            "raw_data_id": 16461,
            "exp_result_id": 50978,
            "gt__": "广东省饶平县三饶镇南联何厝向南后围13号",
            "pred": "广东省饶平县三饶镇南联何磨向南后围13号",
            "edit_distance": 1
          },
          "pred_compare": {
            "1423_idcard_res18": "广东省饶平县三饶镇南联何唐向南后围13号",
            "1417_idcard_res50": "广东省饶平县三饶镇南联何磨向南后围13号",
            "edit_distance": 1
          }
        }
      },
      "diff_gt_id": {
        "1423_idcard_res18": [
          {
            "gt_id": 712655,
            "raw_data_id": 16598,
            "exp_result_id": 51520,
            "gt__": "浙江省温岭市箬横镇马桥村马桥小区14幢5号",
            "pred": "浙江省温岭市善横镇马桥村马桥小区14幢5号",
            "edit_distance": 1
          }
        ],
        "1417_idcard_res50": [
          {
            "gt_id": 712656,
            "raw_data_id": 16469,
            "exp_result_id": 50983,
            "gt__": "江西省宜春市宜丰县车上林场小水分场9组6号",
            "pred": "1990江西省宜春市宜丰县车上林场小水分场9组6号",
            "edit_distance": 4
          }
        ]
      }
    }


"""
import argparse
import json
from pathlib import Path

import editdistance
from tqdm import tqdm

from scripts.st_client import StClient


class WrongItem:
    def __init__(self, name: str, st_client: StClient):
        """

        Args:
            name: 字段名称
            st_client: 结构化工具客户端
        """
        self.name = name
        self.st_client = st_client
        self.data = {}

    def add(self, gt_id: int, raw_data_id: int, exp_result_id: int):
        """

        Args:
            gt_id: dp 数据集中每张图片 ground truth 的 id
            raw_data_id: 即使是在同一个实验室中，不同实验的 raw_data_id 也不同，在结构化工具页面上显示的是这个 id
            exp_result_id: 调用 /api/exp_result/{id} 使用的 id
        """
        exp_result = self.st_client.fetch_exp_result(exp_result_id)

        value = exp_result["ground_truth_latest"]["output"].get("value", {})
        gt = value.get(self.name)
        pred = exp_result["result"]["pred"].get(self.name)

        if gt is None:
            gt = ""

        if pred is None:
            pred = ""

        self.data[gt_id] = {
            "gt_id": gt_id,
            "raw_data_id": raw_data_id,
            "exp_result_id": exp_result_id,
            "gt__": gt,
            "pred": pred,
            "edit_distance": editdistance.eval(gt, pred),
        }

    def gt(self, gt_id: int):
        return self.data[gt_id]["gt__"]

    def pred(self, gt_id: int):
        return self.data[gt_id]["pred"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser("比对两个实验的结构化结果，仅支持简单的 key-value 形式的结构化结果")
    parser.add_argument(
        "--st_url", default="http://st.cloud.tianrang-inc.com/", help="结构化工具地址",
    )
    parser.add_argument(
        "--output",
        required=True,
        help='结果的保存目录，结果文件默认格式为: "{field_name}_{expid1}_{expid2}.json"',
    )
    parser.add_argument(
        "--exp",
        required=True,
        help="结构化实验的 id 和对应的 tag，tag 仅用于保存在结果中方便查看，示例: `100 tag1 200 tag2`",
        nargs=argparse.REMAINDER,
    )

    args = parser.parse_args()
    assert len(args.exp) == 4, "exp 参数长度必须是 4"
    args.output = Path(args.output)
    if not args.output.exists():
        args.output.mkdir(parents=True, exist_ok=True)

    st_client = StClient(args.st_url)
    exp_id1, exp_tag1, exp_id2, exp_tag2 = args.exp
    exp_id1 = int(exp_id1)
    exp_id2 = int(exp_id2)

    raws1 = st_client.fetch_exp_result_by_field(exp_id1)
    raws2 = st_client.fetch_exp_result_by_field(exp_id2)

    assert (
        raws1.keys() == raws2.keys()
    ), f"实验室字段同不同，无法比较。 exp1 keys: {raws1.keys()} exp2 keys: {raws2.keys()}"

    # key: item_name
    # value: result of fetch_exp_result
    for item_name in raws1:
        print(f"Fetching {item_name}...")
        field1_items = raws1[item_name]["items"]
        field2_items = raws2[item_name]["items"]
        assert (
            field1_items[0]["gt_set_id"] == field2_items[0]["gt_set_id"]
        ), "两次实验的数据集(gt_set_id)不一样，无法比较"

        wrong_item1 = WrongItem(item_name, st_client)
        wrong_item2 = WrongItem(item_name, st_client)

        for item in tqdm(field1_items, desc=f"{exp_tag1}({exp_id1})"):
            if item["is_wrong"]:
                wrong_item1.add(item["gt_id"], item["raw_data_id"], item["id"])

        for item in tqdm(field2_items, desc=f"{exp_tag2}({exp_id2})"):
            if item["is_wrong"]:
                wrong_item2.add(item["gt_id"], item["raw_data_id"], item["id"])

        exp1_tag_id = f"{exp_id1}_{exp_tag1}"
        exp2_tag_id = f"{exp_id2}_{exp_tag2}"

        same_gt_ids = wrong_item1.data.keys() & wrong_item2.data.keys()

        same_gt_id_same_error = {}
        same_gt_id_diff_error = {}
        for gt_id in same_gt_ids:
            if wrong_item1.pred(gt_id) == wrong_item2.pred(gt_id):
                same_gt_id_same_error[gt_id] = {
                    exp1_tag_id: wrong_item1.data[gt_id],
                    exp2_tag_id: wrong_item2.data[gt_id],
                }
            else:
                same_gt_id_diff_error[gt_id] = {
                    exp1_tag_id: wrong_item1.data[gt_id],
                    exp2_tag_id: wrong_item2.data[gt_id],
                    "pred_compare": {
                        exp1_tag_id: wrong_item1.pred(gt_id),
                        exp2_tag_id: wrong_item2.pred(gt_id),
                        "edit_distance": editdistance.eval(
                            wrong_item1.pred(gt_id), wrong_item2.pred(gt_id)
                        ),
                    },
                }

        tag1_diff_gt_ids = []
        for gt_id in wrong_item1.data:
            if gt_id not in same_gt_ids:
                tag1_diff_gt_ids.append(wrong_item1.data[gt_id])

        tag2_diff_gt_ids = []
        for gt_id in wrong_item2.data:
            if gt_id not in same_gt_ids:
                tag2_diff_gt_ids.append(wrong_item2.data[gt_id])

        result = {
            "same_gt_id_same_error": same_gt_id_same_error,
            "same_gt_id_diff_error": same_gt_id_diff_error,
            "diff_gt_id": {
                exp1_tag_id: tag1_diff_gt_ids,
                exp2_tag_id: tag2_diff_gt_ids,
            },
        }
        with open(
            args.output / f"{item_name}_{exp_id1}_{exp_id2}.json", "w", encoding="utf-8"
        ) as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
