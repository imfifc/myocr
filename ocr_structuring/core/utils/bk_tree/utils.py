# encoding=utf-8
import hashlib


def md5(filepath):
    """
    https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
    :return md5 string
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# 进行两个node的deep比较
def compare_node(node1, node2):
    if node1.word != node2.word:
        raise Exception("word %s != %s", node1.word, node2.word)
    for k, v in node1.children.items():
        if k not in node2.children:
            raise Exception("key %s not in node2 %s", k, node2.word)
        compare_node(v, node2.children[k])
    for k, v in node2.children.items():
        if k not in node1.children:
            raise Exception("key %s not in node1 %s", k, node1.word)
