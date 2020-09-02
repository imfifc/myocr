import unittest

from ...utils.bk_tree import loader, SHANGHAI_HOSPITAL_NAME, utils, CURRENT_DIR


class TestBKTree(unittest.TestCase):
    def test_loader(self):
        from_source_file = loader.load_from_disk(CURRENT_DIR, SHANGHAI_HOSPITAL_NAME, force=True)
        from_tree_file = loader.load_from_disk(CURRENT_DIR, SHANGHAI_HOSPITAL_NAME)
        utils.compare_node(from_source_file.root, from_tree_file.root)
        self.assertTrue(True)

    def test_search(self):
        sh = loader.load_from_disk(CURRENT_DIR, SHANGHAI_HOSPITAL_NAME)
        self.assertEqual(sh.search_one('复旦大学附属中山?院'), '复旦大学附属中山医院')


if __name__ == '__main__':
    unittest.main()
