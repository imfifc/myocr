# encoding=utf-8
import numpy as np


class StructureItem:
    VERSION = 'V1'

    def __init__(self,
                 item_name,
                 show_name,
                 content,
                 scores):
        """
        :param item_name: 与模板配置文件中的 item_name 对应
        :param show_name: 与模板配置文件中的 show_name 对应
        :param content: 结构化结果，可能有不同的类型 str | int | float | List[obj]
                        如果是 summary_charges/detail_charges，则为 List[SummaryItemContent/DetailItemContent]
        :param scores: crnn 返回的所有字符的平均置信度.
            对于 SummaryCharges 和 DetailCharges 来说是所有内容的平均值
        """
        self.item_name = item_name
        self.show_name = show_name
        self.content = content
        self.scores = scores

    def to_dict(self):
        # TODO: 这里 scores 应该都是 list，check 一下哪里返回了 int
        if isinstance(self.scores, list) and len(self.scores) == 0:
            probability = 0
        else:
            probability = float(np.mean(self.scores))

        # content字段内如果放了一个对象，或者对象的列表，则会将对象转为Dict，如果写了to_dict方法
        if hasattr(self.content, 'to_dict'):
            content = self.content.to_dict()
        elif isinstance(self.content, list) and len(self.content) > 0:
            if hasattr(self.content[0], 'to_dict'):
                content = [item.to_dict() for item in self.content]
            elif isinstance(self.content[0], dict):
                # 列表项中是个字典的情况
                content = []
                for row in self.content:
                    temp = {}
                    for k, v in row.items():
                        temp[k] = row[k].to_dict()
                    content.append(temp)
            else:
                content = self.content
        else:
            content = self.content
        return {
            'item_name': self.item_name,
            'show_name': self.show_name,
            'content': content,
            'probability': probability,
        }

    def set_none(self):
        self.content = None
        self.scores = []

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())


class ChargeItem:
    def __init__(self, val, scores):
        self.val = val
        self.scores = scores

        if len(self.scores) == 0:
            self.probability = 0
        else:
            self.probability = sum(self.scores) / float(len(self.scores))

        self.show_name = ''

    def __str__(self):
        return self.val

    def to_dict(self):
        return {
            'content': str(self.val),
            'probability': self.probability,
            'show_name': self.show_name
        }


class SummaryChargeItem(ChargeItem):
    """
    用于对summary中的charge项进行空间回退
    """

    def __init__(self, val, scores, x, y):
        super().__init__(val, scores)
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return int(str(self.x) + str(self.y))


class SummaryItemContent:
    def __init__(self, name: ChargeItem, charge: ChargeItem):
        """
        大体收费项的 content 内容结构
        :param name: ChargeItem. e.g. 西药费/床位费
        :param charge: ChargeItem. 费用
        """
        self.name = name
        self.charge = charge

        self.name.show_name = '项目名称'
        self.charge.show_name = '金额'

    def __str__(self):
        return 'name:{} total:{}'.format(self.name.val, self.charge.val)

    @property
    def probability(self):
        out = []
        out.extend(self.name.scores)
        out.extend(self.charge.scores)

        if len(out) == 0:
            return 0

        return sum(out) / float(len(out))

    def __repr__(self):
        return str({
            'name': self.name.to_dict(),
            'charge': self.charge.to_dict()
        })

    def to_dict(self):
        return {
            'name': self.name.to_dict(),
            'charge': self.charge.to_dict()
        }


class DetailItemContent:
    def __init__(self, name: ChargeItem, unit_price: ChargeItem, total_price: ChargeItem):
        """
        细分收费项的 content 内容结构
        :param name: ChargeItem. e.g. 检查项目名称/药品名称/器械名称
        :param unit_price: ChargeItem. 单价，可能为 None
        :param total_price: ChargeItem. 总价，可能为 None
        """
        self.name = name
        self.unit_price = unit_price
        self.total_price = total_price

        self.name.show_name = '项目名称'
        self.unit_price.show_name = '单价'
        self.total_price.show_name = '总价'

    def __str__(self):
        return 'name:{}|unit:{}|total:{}'.format(self.name.val, self.unit_price.val,
                                                 self.total_price.val)

    @property
    def probability(self):
        out = []
        out.extend(self.name.scores)
        out.extend(self.unit_price.scores)
        out.extend(self.total_price.scores)

        if len(out) == 0:
            return 0

        return sum(out) / float(len(out))

    def __repr__(self):
        return str({
            'name': self.name.to_dict(),
            'unit_price': self.unit_price.to_dict(),
            'total_price': self.total_price.to_dict()
        })

    def to_dict(self):
        return {
            'name': self.name.to_dict(),
            'unit_price': self.unit_price.to_dict(),
            'total_price': self.total_price.to_dict()
        }
