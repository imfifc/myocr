from .bbox import BBox
from .classifier import LayerClassifier, ContentClassifier


class Label:
    def __init__(self, name, bbox, layer_classifier, scores):
        self.name = name
        self.bbox = BBox(bbox)
        self.layer_classifier = layer_classifier
        self.scores = scores

    def __str__(self):
        return self.name

    __repr__ = __str__

    def is_foreground(self):
        return self.layer_classifier == LayerClassifier.FOREGROUND


class TopLabel(Label):
    def __lt__(self, other):
        return self.bbox.top < other.bbox.top

    def __str__(self):
        return f'{self.name} {self.bbox.left}-{self.bbox.top}-{self.bbox.right}-{self.bbox.bot}'


class LabelWithContentClassifier:
    def __init__(self, label, content_classifier):
        self.label = label
        self.content = label.name
        self.content_classifier = content_classifier

    def __str__(self):
        return str(self.label)

    __repr__ = __str__

    def is_name(self):
        return self.content_classifier == ContentClassifier.NAME

    def is_amount(self):
        return self.content_classifier == ContentClassifier.AMOUNT

    def is_quantity(self):
        return self.content_classifier == ContentClassifier.QUANTITY
