import re


def discount(summary_labels, detailed_labels, origin_detailed_labels):

    result = {'甲': [], '乙': [], '丙': []}
    have = False
    sort_names = ['甲', '乙', '丙']

    for detail in detailed_labels:
        for name in sort_names:
            regx = '[\(\[【{].*?[' + name + '].*?[\)\]}】]'
            if re.search(regx, detail.name.val):
                have = True
                result[name].append(detail)

    return have, result

