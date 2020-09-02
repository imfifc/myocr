from .classifier import ContentClassifier


class Row:
    def __init__(self, labels):
        self.labels = labels
        self.names = []
        self.amounts = []
        self.quantities = []

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        return self.labels[i]

    def __str__(self):
        return str(self.labels)

    __repr__ = __str__

    def sort(self, key):
        self.labels.sort(key=key)

    def append(self, label):
        self.labels.append(label)

    def stat(self):
        for i in range(0, len(self.labels)):
            content_classifier = self.labels[i].content_classifier
            if content_classifier == ContentClassifier.NAME:
                self.names.append(i)
            elif content_classifier == ContentClassifier.AMOUNT:
                self.amounts.append(i)
            elif content_classifier == ContentClassifier.QUANTITY:
                self.quantities.append(i)
