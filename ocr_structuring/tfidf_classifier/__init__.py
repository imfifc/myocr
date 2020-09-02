from typing import List

from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .class_lists import class_lists

from .utils import remove_stop_words, get_corpus


class TfidfClassifier:
    def __init__(self, class_list_name='all'):
        """
        # TODO 这个 list 是不是应该放在 tfidf_classifier package 外面？
        :param class_list_name: class_lists 中有的分类列表名称，为了应对不同客户的分类需求，有些客户可能不需要那么多类
        """
        self.vectorizers = {}
        self.transformers = {}
        self.corpus_tfidfs = {}

        if class_list_name not in class_lists:
            raise NotImplementedError(f'class_list [{class_list_name}] is not implemented')

        self.supported_class_names = class_lists[class_list_name]
        self.supported_class_names.sort()

    def eval(self, raw_data: List[List], input_classes: List[str] = None):
        """
        根据 tmpl_names lazy 地创建分类器

        :param raw_data: 待分类图片的 raw_data
        :param input_classes: 待分类的所有类名
        :return:
            class_name: 模板的名称
            cos: 余弦值
        """
        if not raw_data:
            return None

        if input_classes is None:
            input_classes = self.supported_class_names
        else:
            # 过滤掉 tfidf 不支持的分类 TODO：是否要 raise exception？
            input_classes = list(filter(lambda x: x in self.supported_class_names, input_classes))
            input_classes.sort()

        if len(input_classes) == 0:
            return None

        input_str = ''
        for label in raw_data:
            input_str += remove_stop_words(label[0])

        transformer, vectorizer, corpus_tfidf = self._get_transformer_vec_tfidf(input_classes)

        input_tfidf = transformer.transform(vectorizer.transform([input_str]))

        cos_similarities = linear_kernel(input_tfidf, corpus_tfidf)[0]

        pred_class_idx = cos_similarities.argsort()[::-1][0]

        class_name = input_classes[pred_class_idx]

        return class_name, cos_similarities[pred_class_idx]

    def support(self, class_name) -> bool:
        """
        检查一个模板类型是否支持 tfidf 分类
        """
        return class_name in self.supported_class_names

    def _get_transformer_vec_tfidf(self, class_names):
        cache_key = ''.join(class_names)

        if cache_key not in self.transformers:
            vectorizer = CountVectorizer(analyzer='char')
            transformer = TfidfTransformer()
            tfidf = transformer.fit_transform(vectorizer.fit_transform(get_corpus(cache_key, class_names)))

            self.transformers[cache_key] = transformer
            self.vectorizers[cache_key] = vectorizer
            self.corpus_tfidfs[cache_key] = tfidf

        return self.transformers[cache_key], self.vectorizers[cache_key], self.corpus_tfidfs[cache_key]
