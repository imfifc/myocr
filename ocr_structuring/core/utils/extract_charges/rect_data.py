class RectData:
    def __init__(self, rect, content, text_type):
        self.rect = rect
        self.content = content
        self.text_type = text_type
        self.scores = [1 for _ in content]


class ChargeItem:
    def __init__(self, val, scores):
        self.val = val
        self.scores = scores

    def __str__(self):
        return self.val


class SummaryItemContent:
    def __init__(self, name, charge):
        """
        大体收费项的 content 内容结构
        :param name: ChargeItem. e.g. 西药费/床位费
        :param charge: ChargeItem. 费用
        """
        self.name = name
        self.charge = charge

    def __str__(self):
        return 'name:{} total:{}'.format(self.name.val, self.charge.val)

    @property
    def score(self):
        out = []
        out.extend(self.name.scores)
        out.extend(self.charge.scores)

        if len(out) == 0:
            return 0

        return sum(out) / float(len(out))

    __repr__ = __str__

    # def __repr__(self):
    #     return str({
    #         "name": self.name.__dict__,
    #         "charge": self.charge.__dict__
    #     })


class DetailItemContent:
    def __init__(self, name, unit_price, total_price):
        """
        细分收费项的 content 内容结构
        :param name: ChargeItem. e.g. 检查项目名称/药品名称/器械名称
        :param unit_price: ChargeItem. 单价，可能为 None
        :param total_price: ChargeItem. 总价，可能为 None
        """
        self.name = name
        self.unit_price = unit_price
        self.total_price = total_price

    def __str__(self):
        return 'name:{}|unit:{}|total:{}'.format(self.name.val, self.unit_price.val,
                                                 self.total_price.val)

    @property
    def score(self):
        out = []
        out.extend(self.name.scores)
        out.extend(self.unit_price.scores)
        out.extend(self.total_price.scores)

        if len(out) == 0:
            return 0

        return sum(out) / float(len(out))

    __repr__ = __str__

    # def __repr__(self):
    #     return str({
    #         'name': self.name.__dict__,
    #         'unit_price': self.unit_price.__dict__,
    #         'total_price': self.total_price.__dict__
    #     })
