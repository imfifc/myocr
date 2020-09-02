import os
from pathlib import Path
from typing import List

CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
CORPUS_DIR = CURRENT_DIR / 'data'

stops = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '"', '$', '%', '&', "'", "(", ")", "*", '+', ',',
         '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '_'}


def load_corpus(filepath) -> str:
    with open(str(filepath), 'r', encoding='utf-8') as f:
        data = f.read()
        data = [x.strip() for x in data]
    return ''.join(data)


def remove_stop_words(text: str) -> str:
    if not text:
        return text

    out = []
    for c in text:
        if c not in stops:
            out.append(c)
    return ''.join(out)


corpus = {}


def get_corpus(cache_key: str, class_names: List[str]):
    """
    必须保证出去的 corpus 顺序和 tmpl_names 顺序一样，否则分类会出错
    """
    global corpus
    if cache_key not in corpus:
        corpus[cache_key] = {name: load_corpus(CORPUS_DIR / ('%s.txt' % name)) for name in class_names}

    out = []
    for name in class_names:
        out.append(corpus[cache_key][name])

    return out
