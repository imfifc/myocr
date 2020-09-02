import json
from functools import lru_cache

import requests


class StClient:
    """结构化工具客户端"""

    def __init__(self, server_addr: str):
        self.server_addr = (
            server_addr[:-1] if server_addr.endswith("/") else server_addr
        )

    def fetch_exp_result_by_field(self, exp_id):
        """
        /api/experiment/{exp_id}/result/by_field

        返回示例：
            - id: 获得结构化信息
            - gt_set_id：dp 上数据集的 id
            - gt_id：dp 数据集中每张图片 ground truth 的 id
            - is_wrong：结构化工具比对的结果，是否正确
            - raw_data_id：即使是在同一个实验室中，不同实验的 raw_data_id 也不同，在结构化工具页面上显示的是这个 id

            {
              "address": {
                "title": "住址",
                "items": [
                  {
                    "id": 50978,
                    "raw_data_id": 16461,
                    "gt_id": 712651,
                    "gt_set_id": 1314,
                    "is_wrong": true
                  }
                ]
              },
              "birthday": {
                "title": "出生日期",
                "items": [
                  {
                    "id": 50997,
                    "raw_data_id": 16448,
                    "gt_id": 712625,
                    "gt_set_id": 1314,
                    "is_wrong": true
                  }
                ]
              }
            }

        """
        url = f"{self.server_addr}/api/experiment/{exp_id}/result/by_field"
        resp = requests.get(url, verify=False)
        return self._get_resp_data(resp)

    @lru_cache(maxsize=None)
    def fetch_exp_result(self, exp_result_id: int):
        """
        /api/exp_result/{id}

        返回示例（仅列举了部分）：

            {
                "ground_truth_latest": {
                    "output": {
                        "id": 11,
                        "value": {
                            "key1": "value1",
                            "key2": "value2"
                        }
                    }
                },
                "result": {
                    "pred": {
                        "key1": "value1",
                        "key2": "value2"
                    }
                }
            }
        """
        url = f"{self.server_addr}/api/exp_result/{exp_result_id}"
        resp = requests.get(url, verify=False)
        return self._get_resp_data(resp)

    def fetch_raw_data_list(self, lab_id, page_num: int, page_size: int):
        """
        获取rawData列表
        :param lab_id:
        :param page_num:
        :param page_size:
        :return:
        """
        url = f"{self.server_addr}/api/lab/{lab_id}/raw_data"
        resp = requests.get(
            url, {"page_num": page_num, "page_size": page_size,}, verify=False
        )
        return self._get_resp_data(resp)

    def fetch_media(self, media_id) -> bytearray:
        """获取media，返回byte数组"""
        url = f"{self.server_addr}/api/media/{media_id}"
        resp = requests.get(url, verify=False)
        resp.raise_for_status()
        # TODO: check media response
        # body = resp.json()
        # if body and body['code'] != 0:
        #     raise RuntimeError(f'[{body["code"]}]{body["message"]}')
        return resp.content

    def download_media(self, media_id, save_path: str):
        """
        下载media
        :param media_id:
        :param save_path: 保存路径
        :return:
        """
        content = self.fetch_media(media_id)
        with open(save_path, "wb") as f:
            f.write(content)

    def upload_experiment_result(self, exp_id, result):
        url = f"{self.server_addr}/api/experiment/{exp_id}/exp_result"
        resp = requests.post(
            url,
            data=json.dumps(
                result, ensure_ascii=False, default=lambda x: x.__dict__
            ).encode("utf-8"),
            verify=False,
        )
        return self._get_resp_data(resp)

    def _get_resp_data(self, resp: requests.Response):
        resp.raise_for_status()
        body = resp.json()
        if body["code"] != 0:
            raise RuntimeError(f'[{body["code"]}]{body["message"]}')
        if "data" in body:
            return body["data"]
