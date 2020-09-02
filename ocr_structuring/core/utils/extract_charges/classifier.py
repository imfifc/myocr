class CharClassifier:
    CH = 0  # 我
    EN = 1  # x
    NUM = 2  # 3
    MISC = 3  # !


class ContentClassifier:
    NAME = 0  # 诊疗费
    AMOUNT = 1  # 23.12
    QUANTITY = 2  # 15
    MISC = 3  # 1CoX12支


class LayerClassifier:
    FOREGROUND = 2
    BACKGROUND = 1
