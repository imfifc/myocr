from typing import Dict

from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import linear_kernel

from ocr_structuring.core.utils.node_item import NodeItem


def load_corpus(filepath) -> str:
    with open(str(filepath), 'r', encoding='utf-8') as f:
        data = f.read()
        data = [x.strip() for x in data]
    return ''.join(data)


class TfidfTextClassifier:
    def __init__(self, corpus_path: str):
        corpus = load_corpus(corpus_path)
        self.vectorizer = CountVectorizer(analyzer='char')
        self.transformer = TfidfTransformer()
        self.tfidf = self.transformer.fit_transform(self.vectorizer.fit_transform([corpus]))

    def score(self, text: str) -> float:
        """
        返回输入 text 和对应语料的余弦相似度
        :param text:
        :return:
        """
        if not text:
            return 0

        input_tfidf = self.transformer.transform(self.vectorizer.transform([text]))

        cos_similarities = linear_kernel(input_tfidf, self.tfidf)[0]

        pred_class_idx = cos_similarities.argsort()[::-1][0]

        return cos_similarities[pred_class_idx]

    def max_score_node(self, node_item: Dict[str, NodeItem]) -> NodeItem:
        return max(node_item.values(), key=lambda x: self.score(x.text))
