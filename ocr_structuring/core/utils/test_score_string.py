from unittest import TestCase

from ocr_structuring.core.utils.score_string import ScoreString


class TestScoreString(TestCase):
    def test_empty_scores(self):
        text = "2019-3-1.1"
        scores = []

        ss = ScoreString(text, scores)
        self.assertEqual(ss.scores, [1] * len(text))

    def test_slice(self):
        text = "2019-3-1.1"
        scores = []

        ss = ScoreString(text, scores)
        self.assertEqual(text[:4], "2019")

    def test_short_scores(self):
        text = "2019"
        scores = [0.9, 0.8]

        ss = ScoreString(text, scores)
        self.assertEqual(len(ss.scores), len(text))
        self.assertAlmostEqual(ss.scores[2], 0.85)
        self.assertAlmostEqual(ss.scores[3], 0.85)

    def test_long_scores(self):
        text = "2"
        scores = [0.9, 0.8]

        ss = ScoreString(text, scores)
        self.assertEqual(len(ss.scores), len(text))
        self.assertEqual(ss.scores[0], 0.9)

    def test_empty_text(self):
        text = ""
        scores = [0.9, 0.8]

        ss = ScoreString(text, scores)
        self.assertEqual(len(ss.scores), len(text))

    def test_all_empty(self):
        text = ""
        scores = []

        ss = ScoreString(text, scores)
        self.assertEqual(len(ss.scores), len(text))

    def test_add(self):
        text1 = "11"
        scores1 = [0.9, 0.8]

        ss1 = ScoreString(text1, scores1)

        text2 = "22"
        scores2 = [0.7, 0.6]

        ss2 = ScoreString(text2, scores2)

        ss = ss1 + ss2
        self.assertEqual(ss.scores, scores1 + scores2)
        self.assertEqual(len(ss.scores), len(ss.data))
        self.assertEqual(ss.data, text1 + text2)

    def test_length(self):
        text = "1.1.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5]

        ss = ScoreString(text, scores)
        self.assertEqual(len(ss), 5)

    def test_replace_single_char_with_empty(self):
        text = "1.121"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "")
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.7, 0.6, 0.5])
        self.assertEqual(replaced_ss.data, "1121")

        text = "1.12.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.4, 0.5]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "")
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.7, 0.6, 0.5])
        self.assertEqual(replaced_ss.data, "1121")

    def test_replace_single_char_with_single_char(self):
        text = "1.12.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "a")
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.7, 0.6, 0.5, 0.4])
        self.assertEqual(replaced_ss.data, "1a12a1")

    def test_replace_single_char_with_multi_char(self):
        text = "1.12.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "aa", count=2)
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.8, 0.7, 0.6, 0.5, 0.5, 0.4])
        self.assertEqual(replaced_ss.data, "1aa12aa1")

    def test_replace_single_char_with_multi_char_count1(self):
        text = "1.12.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "aa", count=1)
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.8, 0.7, 0.6, 0.5, 0.4])
        self.assertEqual(replaced_ss.data, "1aa12.1")

    def test_replace_multi_char_with_single_char(self):
        text = "1.12..1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace("..", "a")
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.7, 0.6, 0.5, 0.3])
        self.assertEqual(replaced_ss.data, "1.12a1")

    def test_replace_multi_char_with_multi_char(self):
        text = "1.12..1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace("..", "aaa")
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.45, 0.3])
        self.assertEqual(replaced_ss.data, "1.12aaa1")

    def test_replace_single_char_with_single_char_thresh_filter(self):
        text = "1.12.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "a", thresh=0.6)
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.data, "1.12a1")
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.7, 0.6, 0.5, 0.4])

        text = "1.12.1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace(".", "a", thresh=0.9)
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.data, "1a12a1")
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.7, 0.6, 0.5, 0.4])

    def test_replace_multi_char_with_multi_char_thresh_filter(self):
        text = "1.12..1"
        scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.1, 0.4]

        ss = ScoreString(text, scores)
        replaced_ss = ss.replace("..", "aaa", thresh=0.6)
        self.assertEqual(len(replaced_ss.scores), len(replaced_ss.data))
        self.assertEqual(replaced_ss.data, "1.12aaa1")
        self.assertEqual(replaced_ss.scores, [0.9, 0.8, 0.7, 0.6, 0.5, 0.1, 0.3, 0.4])
