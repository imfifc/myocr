import re
from .bbox import BBox
from .label import Label, LabelWithContentClassifier
from .classifier import CharClassifier, ContentClassifier, LayerClassifier
from .row import Row

float_pattern = re.compile('[1-9][,0-9]*\.[0-9]+')
int_pattern = re.compile('[1-9][0-9]*')
name_pattern = re.compile(r'[一-黿]{3,}')  # [一-黿] 代表汉字
zifu_pattern = re.compile(r'.*自付.?([一-黿]*)')  # [一-黿] 代表汉字


def group_into_rows(labels, fraction):
    """
    :param labels: List[Label]
    :param fraction: float
    :return: List[List[Label]]
    """
    res = []
    cur = Row(labels=[])
    for l in labels:
        label = LabelWithContentClassifier(label=l, content_classifier=ContentClassifier.MISC)
        if len(cur) == 0:
            cur.append(label)
            continue
        head = cur[0]
        if is_same_row(head.label.bbox, l.bbox, fraction):
            cur.append(label)
        else:
            cur.sort(key=lambda x: x.label.bbox.left)
            res.append(cur)
            cur = Row([label])
    if len(cur) > 0:
        cur.sort(key=lambda x: x.label.bbox.left)
        res.append(cur)
    return res


def is_same_row(a, b, fraction):
    """
    :param a: BBox
    :param b: BBox
    :param fraction: float
    :return: bool
    """
    if fraction > 1 or fraction <= 0:
        raise Exception('fraction must be within (0, 1]')
    delta_center_y = abs(a.center_y() - b.center_y())
    if delta_center_y < a.delta_y() * fraction and delta_center_y < b.delta_y() * fraction:
        return True
    return False


def classify(l):
    """
    :param s: str
    :return: ClassifiedText
    """
    s = l.label.name
    if len(s) == 0:
        return
    counter = {}
    for c in s:
        if is_chinese(c):
            counter[CharClassifier.CH] = 0 if CharClassifier.CH not in counter else counter[CharClassifier.CH] + 1
        elif is_english(c):
            counter[CharClassifier.EN] = 0 if CharClassifier.EN not in counter else counter[CharClassifier.EN] + 1
        elif is_number(c):
            counter[CharClassifier.NUM] = 0 if CharClassifier.NUM not in counter else counter[CharClassifier.NUM] + 1
        else:
            counter[CharClassifier.MISC] = 0 if CharClassifier.MISC not in counter else counter[CharClassifier.MISC] + 1

    # 连续出现三个或以上中文认为是名字
    name_pattern_res = name_pattern.search(s)
    if name_pattern_res:
        # 自付是北京的关键字，这里可以添加更多规则
        zifu_pattern_res = zifu_pattern.search(s)
        if zifu_pattern_res:
            s = zifu_pattern_res.groups()[0]
        if len(s) >= 3:
            if zifu_pattern_res:
                l.label.scores = l.label.scores[zifu_pattern_res.start(0): zifu_pattern_res.end(0)]
            else:
                l.label.scores = l.label.scores[name_pattern_res.start(0): name_pattern_res.end(0)]
            l.content = s
            l.content_classifier = ContentClassifier.NAME
            return
        else:
            s = l.label.name
    # 仅包含一个完整的小数认为是钱
    float_pattern_res = [x for x in float_pattern.finditer(s)]
    if len(float_pattern_res) == 1:
        m = float_pattern_res[0]
        text_val = m.group()
        l.label.name = text_val
        l.label.scores = l.label.scores[m.start(0): m.end(0)]
        l.content = float(text_val)
        l.content_classifier = ContentClassifier.AMOUNT
        return
    # 仅包含一个整数且数字占比较高认为是数量
    if CharClassifier.NUM in counter and (counter[CharClassifier.NUM]) >= len(s) * 0.5:
        int_pattern_res = [x for x in int_pattern.finditer(s)]
        # 设置上限为了过滤社保号和年月日等长串数，单张发票上的金额和数量大概率小于10万
        if len(int_pattern_res) == 1:
            m = int_pattern_res[0]
            text_val = m.group()
            int_val = int(text_val)
            if int_val < 100000:
                l.label.name = text_val
                l.label.scores = l.label.scores[m.start(0): m.end(0)]
                l.content = text_val
                l.content_classifier = ContentClassifier.QUANTITY
    return


def is_chinese(c):
    """
    :param c: chr
    :return: bool
    """
    return True if '\u4E00' <= c <= '\u9EFF' else False


def all_chinese(txt):

    """
    :param txt:
    :return:
    """

    for c in txt:
        if not is_chinese(c):
            return False
    return True



def is_number(c):
    """
    :param c: chr
    :return: bool
    """
    return True if '0' <= c <= '9' else False


def is_english(c):
    """
    :param c: chr
    :return: bool
    """
    return True if 'a' <= c <= 'z' or 'A' <= c <= 'Z' else False


def percent_2_absolute(coordinate_box, percent_box):
    """
    :param coordinate_box: BBox
    :param percent_box: BBox
    :return:
    """
    percent_box.left = round(coordinate_box.delta_x() * percent_box.left)
    percent_box.right = round(coordinate_box.delta_x() * percent_box.right)
    percent_box.top = round(coordinate_box.delta_y() * percent_box.top)
    percent_box.bot = round(coordinate_box.delta_y() * percent_box.bot)


def group_into_tables(rows, offset):
    """
    :param rows: List[List[Label]]
    :param offset: int
    :return: List[List[List[Label]]]
    """
    res = []
    cur = []
    left = 0
    for row in rows:
        cur_left = row[0].label.bbox.left
        if len(cur) == 0:
            left = cur_left
            cur.append(row)
            continue
        if abs(cur_left - left) < offset:
            cur.append(row)
        else:
            res.append(cur)
            cur = [row]
            left = row[0].label.bbox.left
    if len(cur) > 0:
        res.append(cur)
    return res


def bbox_of_row(row):
    """
    :param row: List[Label]
    :return: BBox
    """
    top = min([x.bbox.top for x in row])
    bot = max([x.bbox.bot for x in row])
    return BBox([row[0].bbox.left, top, row[-1].bbox.right, bot])


def divide_into_labels(label, c):
    """
    :param label: Label
    :return: (List[Label], bool)
    """
    res = []
    if c not in label.name:
        return res, False
    sub_names = label.name.split(c)
    char_width = label.bbox.delta_x() / float(len(label.name))
    offset = 0
    for sub_name in sub_names:
        sub_label = Label(sub_name, [label.bbox.left + offset * char_width, label.bbox.top,
                                     label.bbox.left + (offset + len(sub_name)) * char_width, label.bbox.bot],
                          label.layer_classifier, label.scores[offset:offset + len(sub_name)])
        res.append(sub_label)
        offset += len(sub_name) + 1
    return res, True


def merge_labels(labels):
    if len(labels) < 2:
        return labels
    res = []
    cur = labels[0]
    for i in range(1, len(labels)):
        label = labels[i]
        float_pattern_res = float_pattern.match(label.name)
        # python2 不提供 full match 功能
        if float_pattern_res and len(label.name) == float_pattern_res.end(0) - float_pattern_res.start(0):
            if cur is not None:
                res.append(cur)
            res.append(label)
        else:
            if cur is None:
                cur = label
            else:
                cur.name = cur.name + label.name
                cur.bbox.right = label.bbox.right
                cur.scores.extend(label.scores)
    if cur is not None:
        res.append(cur)
    return res


def adjust_label_classifier(label):
    """
    :param label: Label
    :return:
    """
    try:
        float(label.name)
        if label.layer_classifier == LayerClassifier.BACKGROUND:
            label.layer_classifier = LayerClassifier.FOREGROUND
    except ValueError:
        pass
