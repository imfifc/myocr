import os


class Stroke_utils():
    def __init__(self):
        self.strokes = None

    def load_strokes(self):
        strokes = []
        with open(os.path.join(os.path.dirname(__file__), 'strokes.txt'), 'r') as fr:
            for line in fr:
                strokes.append(int(line.strip()))
        return strokes

    def get_stroke(self, c):
        if self.strokes is None:
            self.strokes = self.load_strokes()

        # 如果返回 0, 则也是在unicode中不存在kTotalStrokes字段
        unicode_ = ord(c)
        if 13312 <= unicode_ <= 64045:
            return self.strokes[unicode_ - 13312]
        elif 131072 <= unicode_ <= 194998:
            return self.strokes[unicode_ - 80338]
        else:
            print(f"{c} should be a CJK char, or not have stroke in unihan data.")
            return -1

    def get_stroke_of_string(self, string):
        return [self.get_stroke(char) for char in string]

    def compare_stroke_diff(self, text1, text2):
        s1 = self.get_stroke_of_string(text1)
        s2 = self.get_stroke_of_string(text2)
        return abs(sum(s1) - sum(s2))


stroke_utils = Stroke_utils()

if __name__ == '__main__':
    s1 = stroke_utils.get_stroke_of_string('林安')
    s2 = stroke_utils.compare_stroke_diff('徐', '安')
    print(s1, s2)
