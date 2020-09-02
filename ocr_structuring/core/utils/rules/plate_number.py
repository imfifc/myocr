import re


def correct_plate_number(content: str) -> str:
    place = {'黑', '辽', '晋', '吉', '新', '青', '赣', '桂', '皖', '冀', '陕', '川', '闽', '浙', '甘', '云', '贵', '湘', '豫', '鲁', '宁',
             '鄂', '藏', '苏', '渝', '粤', '蒙', '琼',  '京', '沪'}
    mapping = {'O': '0', 'I': '1'}
    rev_mapping = {'0': 'O', '1': 'I'}

    regexp = r'[%s][A-Z0-9]{6,}' % '|'.join(place)
    content = re.search(regexp, content)

    result = ''
    if content:
        content = list(content.group())
        # 一般车牌最长为8位（含新能源）
        content = content[:8]
        if not content[1].isalpha() and content[1] in rev_mapping:
            content[1] = rev_mapping[content[1]]

        if len([i for i in content[2:] if i.isalpha()]) > 2:
            for i in range(2, len(content)):
                if content[i] in mapping:
                    content[i] = mapping[content[i]]

        result = ''.join(content)

    return result


if __name__ == '__main__':
    assert correct_plate_number('浙E0AZ19') == '浙E0AZ19'
    assert correct_plate_number('北E123A34') == ''
    assert correct_plate_number('豫AI2Z7G') == '豫A12Z7G'
    assert correct_plate_number('吉AX123456') == '吉AX12345'
    assert correct_plate_number('浙E0AZI9') == '浙E0AZ19'
    assert correct_plate_number('川A123AB') == '川A123AB'
    assert correct_plate_number('川A123AB123') == '川A123AB1'
    assert correct_plate_number('浙10AZI9') == '浙I0AZ19'
    assert correct_plate_number('川0123AB') == '川O123AB'
    assert correct_plate_number('京A23456') == '京A23456'