_complex_map = {
    "零": 0,
    "壹": 1,
    "贰": 2,
    "叁": 3,
    "肆": 4,
    "伍": 5,
    "陆": 6,
    "柒": 7,
    "捌": 8,
    "玖": 9,
}

_base_keys = "仟佰拾个"

_section_keys = "兆亿万元"

_other_keys = "角分"

_ambiguous_map = {
    "千": "仟",
    "百": "佰",
    "十": "拾",
    "圆": "元",
    "园": "元",
    "花": "元",
    "一": "壹",
    "二": "贰",
    "三": "叁",
    "四": "肆",
    "五": "伍",
    "六": "陆",
    "七": "柒",
    "八": "捌",
    "久": "玖",
}


def str2currency(content):
    rmb_sign = False
    if content.startswith("￥"):
        content = content[1:]
        rmb_sign = True
    if len(content) > 2:
        return content[:-2] + "." + content[-2:]
    elif rmb_sign:
        r = "0.00"
        return r[: len(r) - len(content)] + content
    return content


def currency2zh(currency_str):
    pass


def zh2currency(currency_zh):
    sections = split_sect(currency_zh)
    r = "".join(sections)
    return trim_leading_zero(r)


def trim_leading_zero(content):
    pos = 0
    for ch in content:
        if ch == "0":
            pos += 1
        else:
            break

    if content[pos] == '.':
        if pos == 0:
            return "0" + content
        else:
            pos -= 1;
    return content[pos:]


def split_sect(currency_zh):
    parts = []
    part = ""
    for ch in currency_zh:
        ch_t = _ambiguous_map.get(ch, ch)
        part += ch_t
        if ch_t in _section_keys:
            parts.append(convert_sect(part))
            part = ""

    if len(part) > 0:
        parts.append(convert_tail(part))
    return parts


def convert_sect(part):
    d = {
        "仟": 0,
        "佰": 0,
        "拾": 0,
        "个": 0
    }
    r = ""
    last = "个"
    for p in reversed(part):
        if p == "拾":
            d["拾"] = 1
        if p in _complex_map and last in d:
            d[last] = _complex_map[p]
        if not p in _section_keys:
            last = p

    r = "".join([str(d[ch]) for ch in _base_keys])
    return r


def convert_tail(part):
    r = ""
    for p in reversed(part):
        if p in _complex_map:
            r = str(_complex_map[p]) + r
    r = "." + r
    while len(r) < 3:
        r += "0"
    return r


if __name__ == "__main__":
    samples = [
        "￥1321321",
        "1321322",
        "￥33",
        "22"
    ]

    for key in samples:
        print(key, str2currency(key))

    samples = [
        "壹元柒角叁分",
        "伍亿陆仟柒佰捌拾贰万伍仟壹佰叁拾肆元柒角叁分",
        "叁佰兆零伍亿陆仟万拾元柒角叁分",
        "贰元正",
        "贰元整",
        "拾元陆角整",
        "二元整",
        "三角",
        "公司",
    ]
    for key in samples:
        print(key, zh2currency(key))
