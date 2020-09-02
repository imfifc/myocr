"""

该方法基于朴素贝叶斯

.. code-block:: python

    >>> guess_gender("周杰伦")
    ('男', 0.9502604753109102)

"""
import os

__all__ = ['guess_gender']


class Guesser(object):

    def __init__(self):
        self._load_model()

    def _load_model(self):
        self.male_total = 0
        self.female_total = 0
        self.freq = {}

        with open(os.path.join(os.path.dirname(__file__),
                               'charfreq.csv'),
                  'rb') as f:
            # skip first line
            next(f)
            for line in f:
                line = line.decode('utf-8')
                char, male, female = line.split(',')
                self.male_total += int(male)
                self.female_total += int(female)
                self.freq[char] = (int(female), int(male))

        self.total = self.male_total + self.female_total

        for char in self.freq:
            female, male = self.freq[char]
            self.freq[char] = (1. * female / self.female_total,
                               1. * male / self.male_total)

    def guess(self, name):
        firstname = name[1:]
        for char in firstname:
            assert u'\u4e00' <= char <= u'\u9fa0', u'姓名必须为中文'

        pf = self.prob_for_gender(firstname, 0)
        pm = self.prob_for_gender(firstname, 1)

        if pm > pf:
            return '男', 1. * pm / (pm + pf)
        elif pm < pf:
            return '女', 1. * pf / (pm + pf)
        else:
            return 'unknown', 0

    def prob_for_gender(self, firstname, gender=0):
        p = 1. * self.female_total / self.total \
            if gender == 0 \
            else 1. * self.male_total / self.total

        for char in firstname:
            p *= self.freq.get(char, (0, 0))[gender]

        return p


guesser = Guesser()


def guess_gender(name):
    return guesser.guess(name)
