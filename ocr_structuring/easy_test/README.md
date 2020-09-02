# Easy Test

支持统计 key-value 形式的结果以及表格形式的结果

## 表头固定的表格
表格形式的数据如 `table_data` 中的示例，value 是一个数组，比较表格数据时从上到下每行比较，如果 gt 的行比 pred 多，则认为 pred 错了；
如果 pred 的行数比 gt 多则忽略


ground truth 的结构：
```json
{
  "structuring_data": [
    {
      "li_nian_zhang_hu_yu_e": {
        "content": "",
        "item_name": "li_nian_zhang_hu_yu_e"
      },
      "zi_fu": {
        "content": "",
        "item_name": "zi_fu"
      },
      "table_data": [
        {
          "production_name": "德胜",
          "specification": "Φ12",
          "dispatch_weight": "13.015",
          "dispatch_quantity": "5件",
          "actual_quantity_received": "5件",
          "actual_weight_received": "13.015",
          "date": "2019年1月16日"
        }
      ]
    }
  ]
}
```


pred 输出结果结构如下，structuring_meta 和 preprocess_result 不一定要有：
```json
{
  "structuring_data": [
    {
      "table_data": [
        {
          "production_name": "德胜",
          "specification": "Φ12",
          "dispatch_weight": "13.015",
          "dispatch_quantity": "5件",
          "actual_quantity_received": "5件",
          "actual_weight_received": "13.015",
          "date": "2019年1月16日"
        }
      ],
      "city": {
        "item_name": "city",
        "show_name": "城市",
        "content": "上海",
        "scores": [
          1
        ]
      },
      "registrationtype": {
        "item_name": "registrationtype",
        "show_name": "挂号类型",
        "content": "门诊",
        "scores": [
          1
        ]
      },
      "xian_jin_zhi_fu": {
        "item_name": "xian_jin_zhi_fu",
        "show_name": "现金支付",
        "content": 390.58,
        "scores": [
          0.9998237490653992,
          0.9999845027923584,
          0.999933123588562,
          0.9998409748077393,
          0.999561607837677,
          0.9997254014015198
        ]
      }
    }
  ],
  "structuring_meta": [
    {
      "class_name": "shanghai_menzhen"
    }
  ],
  "preprocess_result": {
    "roi": [
      63,
      179,
      1377,
      1044
    ]
  }
}
```

## 无表头表格

例如财报这类数据是没有表头的

gt 格式示例，table 是一个二维数组
```json
{
  "structuring_data": [
    {
      "table": [
        [
          "项目",
          "附注",
          "2014年12月31日",
          "2013年12月31日"
        ],
        [
          "流动资产：",
          "&&",
          "&&",
          "&&"
        ],
        [
          "货币资金",
          "六（一）",
          "23173710.60",
          "10035648.62"
        ]
      ]
    }
  ]
}

```

pred 格式示例，table 的 content 是一个二维数组
```json
{
  "structuring_data": [
    {
      "table": {
        "item_name": "table",
        "show_name": "table",
        "probability": 1.0,
        "content": [
          [
            "项目",
            "附注",
            "2014年12月31日",
            "2013年12月31日"
          ],
          [
            "流动资产：",
            "",
            "",
            ""
          ],
          [
            "货币资金",
            "（六（一）",
            "23,173,710.60",
            "10,035,648.62"
          ]
        ]
      }
    }
  ]
}
```