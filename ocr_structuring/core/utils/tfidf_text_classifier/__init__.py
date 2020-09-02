# encoding=utf-8
import os

from .core import TfidfTextClassifier

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
BK_TREE_DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'bk_tree', 'data')

MEDICAL_INSURANCE_TYPE = 'medical_insurance_type.txt'
MEDICAL_INSTITUTION_TYPE = 'medical_institution_type.txt'

MEMORY = {
    MEDICAL_INSURANCE_TYPE: None,
    MEDICAL_INSTITUTION_TYPE: None
}


def medical_insurance_type_text_classifier() -> TfidfTextClassifier:
    return _get_classifier(MEDICAL_INSURANCE_TYPE)


def medical_institution_type_text_classifier() -> TfidfTextClassifier:
    return _get_classifier(MEDICAL_INSTITUTION_TYPE)


def _get_classifier(name) -> TfidfTextClassifier:
    if name not in MEMORY:
        raise NotImplementedError('Text classifier not implemented: %s' % name)
    if MEMORY[name] is None:
        corpus_path = os.path.join(BK_TREE_DATA_DIR, name)
        MEMORY[name] = TfidfTextClassifier(corpus_path)
    return MEMORY[name]
