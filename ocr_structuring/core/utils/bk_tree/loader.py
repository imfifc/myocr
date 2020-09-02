import os
import json
from . import utils
from .core import BKTree, Node

from ...utils import str_util
from ocr_structuring.utils.logging import logger

# 目录名称
SOURCE_DIR_NAME = 'data'
TREE_DIR_NAME = '.tree'


def load_from_disk(working_dir, tree_name, force=False):
    """
    从磁盘中读取数据入BK-TREE
        1. 先尝试从当前目录下的 .tree 目录下读取之前已经落盘的树文件
        2. 如果之前并没有落盘（或者树源文件MD5变化了)，则从源文件中生成树并落盘
        3. 如果Force为True，则强制重新从源文件中生成树
    :param working_dir: 工作目录
    :param tree_name:
    :param force: 是否强行生成
    :return:
    """
    logger.debug('Load BK tree: {}'.format(tree_name))
    source_dir = os.path.join(working_dir, SOURCE_DIR_NAME)
    tree_dir = os.path.join(working_dir, TREE_DIR_NAME)
    source_file_path = os.path.join(source_dir, tree_name)

    if not os.path.exists(source_file_path):
        logger.error('BK-Tree source file not exist: {}'.format(source_file_path))
        raise AssertionError('BK-Tree source file not exist: {}'.format(source_file_path))

    if not os.path.exists(tree_dir):
        os.makedirs(tree_dir)

    file_md5 = utils.md5(source_file_path)
    tree_file_path = os.path.join(tree_dir, file_md5 + '.json')

    if force:
        logger.debug('Force create a new tree')
        bk_tree = load_from_source_file(source_file_path)
        save_to_tree_file(bk_tree, tree_file_path)
    elif not os.path.exists(tree_file_path):  # 树文件不存在代表树之前没有落过盘
        logger.debug('Create a new tree since there is no cache')
        bk_tree = load_from_source_file(source_file_path)
        save_to_tree_file(bk_tree, tree_file_path)
    else:
        logger.debug('Load tree from tree file: %s' % tree_file_path)
        bk_tree = load_from_tree_file(tree_file_path)

    return bk_tree


class BKTreeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Node):
            json_str = {
                'word': o.word,
                'children': {}
            }
            for dist, node in o.children.items():
                json_str['children'][str(dist)] = node
            return json_str
        else:
            return json.JSONEncoder.default(self, o)


class BKTreeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(BKTreeDecoder, self).__init__(object_hook=self.dict_to_node, *args, **kwargs)

    @staticmethod
    def dict_to_node(d):
        if 'word' in d:
            n = Node(d['word'])
            for k, v in d['children'].items():
                n.children[int(k)] = v
            return n
        else:
            return d


def load_from_source_file(source_filepath):
    bk_tree = BKTree()
    with open(source_filepath, encoding='utf-8', mode='r') as f:
        logger.debug('build bktree...')
        for line in f.readlines():
            word = line.strip()
            word = str_util.str_sbc_2_dbc(word)
            bk_tree.insert_node(word)
        logger.debug('finish build bktree...')
    return bk_tree


def load_from_tree_file(tree_filepath):
    with open(tree_filepath, mode='r', encoding='utf-8') as f:
        root = json.load(f, cls=BKTreeDecoder)
    return BKTree(root)


def save_to_tree_file(bk_tree, bk_tree_filepath):
    with open(bk_tree_filepath, mode='w', encoding='utf-8') as f:
        json.dump(bk_tree.root, f, separators=(',', ':'), cls=BKTreeEncoder, ensure_ascii=False)
