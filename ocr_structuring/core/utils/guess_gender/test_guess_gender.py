from unittest import TestCase

from ocr_structuring.core.utils.guess_gender import guess_gender


class TestGuessGender(TestCase):
    def test_guess_gender(self):
        gender, score = guess_gender("周杰伦")
        self.assertEqual(gender, "男")
