import json
import os
from collections import defaultdict
from distance_metrics import lcs
from ...utils import bk_tree
from ocr_structuring.utils.logging import logger

city_info_dict = json.load(open(os.path.join(os.path.dirname(__file__), 'city.json'), 'r', encoding='utf-8'))
district_info_dict = {}
for province, city_list in city_info_dict.items():
    for city_name in city_list:
        if district_info_dict.get(city_name, None):
            district_info_dict[city_name].extend(city_list[city_name])
        else:
            district_info_dict.update({city_name: city_list[city_name]})

# 建立一个 从 city 往province 的映射
city_2_province = defaultdict(list)
for province in city_info_dict:
    if '市' in province:
        continue
    city_list = city_info_dict[province].keys()
    for city in city_list:
        city_2_province[city].append(province)

# 建立一个三级索引，有市有县/区信息
province_city_district = []
for province in city_info_dict:
    if '市' in province:
        continue
    for city in city_info_dict[province]:
        for district in city_info_dict[province][city]:
            province_city_district.append((province, city, district))

province_2_city_and_district = defaultdict(list)
for province in city_info_dict:
    if '市' in province:
        continue
    for city in city_info_dict[province]:
        for district in city_info_dict[province][city]:
            if len(city) > 2 and len(district) > 2:
                province_2_city_and_district[province].append(city + district)


def format_address(address: str):
    address = _simple_recover_province(address)
    address = _simple_recover_city(address)
    if '省' in address[:10]:
        new_address = _handle_province(address)
    else:
        new_address = _handle_city(address)
    return new_address


def search_by_lcs(text, probable_list):
    max_dis = 0
    prob_list = []
    for prob in probable_list:
        dis = lcs.llcs(text, prob)
        if dis > max_dis:
            prob_list = [prob]
            max_dis = dis
        elif dis == max_dis:
            prob_list.append(prob)
    return prob_list, max_dis


def _simple_recover_city(address):
    # 如果一个城市信息中，有省有市，检查这个市是否真的在省里面，如果不在，进行简单的修正
    # 这一步在 _simple_recover_province 后做，则表明这个 city 一定是在city 表中找不到的错误city
    if '省' in address and '市' in address:
        province = address.split('省')[0] + '省'
        other_info = ''.join(address.split('省')[1:])
        city = other_info.split('市')[0] + '市'
        district_info = ''.join(other_info.split(city)[1:])
        if province in city_info_dict.keys():
            city_of_province = city_info_dict[province].keys()
            if city not in city_2_province:
                # 首先，从 city_of_province 中找一个最接近的
                prob_city, prob = search_by_lcs(city, city_of_province)
                if len(prob_city) == 1 and prob >= 2:
                    return province + prob_city[0] + district_info

    return address


def _simple_recover_province(address):
    # 遍历所有可能出现的city，查看省份信息
    probable_province = []
    city_name = None
    for city in city_2_province:
        if city in address:
            probable_province = city_2_province[city]
            city_name = city
            break
    if probable_province:
        # 检索到了可能的省份
        # 如果在city_name前面还有至少两个字，认为信息就是真实的省份信息
        if address.index(city_name) >= 2:
            for province in probable_province:
                match = False
                for char in province:
                    if char != '省' and char in address:
                        # 至少包含一个省份信息
                        match = True
                if match:
                    # 对广西壮族自治区做特殊处理;
                    if province == '广西壮族自治区':
                        if '壮族' not in address[:7] and '自治' not in address[:7]:
                            province = '广西省'
                    if province == '新疆维吾尔自治区':
                        if '维吾尔' not in address[:7] and '自治' not in address[:7]:
                            province = '新疆省'

                    if '省' in address:
                        address = province + address[address.index(city_name):]
                    else:
                        address = province.replace('省', '') + address[address.index(city_name):]
                    break
    return address


def _handle_province(address: str) -> str:
    if '省' in address:
        province_info = address.split('省')[0]
        other_info = ''.join(address.split('省')[1:])

        best_province = bk_tree.province().search_one(province_info, search_dist=2, min_len=2)
        # new_other_info = _handle_city(other_info, best_province)
        new_other_info = other_info
        if new_other_info != other_info:
            logger.debug('change city info {} to {} in province process'.format(other_info, new_other_info))
            other_info = new_other_info
        if best_province:
            address = best_province + other_info
        else:
            logger.debug('search bk tree failed , org text is {}'.format(province_info))

    return address


def _handle_city(address: str, province=None):
    # TODO 按照省份的信息来修改市的信息
    # 如果传入省的信息，则在省内进行edit_distance查找
    if '市' in address:
        city_info = address.split('市')[0]
        other_info = ''.join(address.split('市')[1])
        if len(city_info) < 5:
            # 预计他不可能包含省份信息
            best_city = None
            if not province:
                best_city = bk_tree.city().search_one(city_info, search_dist=2, min_len=2)
            else:
                city_list = city_info_dict[province].keys()
                city_tree = bk_tree.BKTree()
                for city in city_list:
                    city_tree.insert_node(city)
                best_city = city_tree.search_one(city_info, search_dist=2, min_len=1)
            if best_city:
                # other_info = _handle_district(other_info, best_city)
                address = best_city + other_info

        else:
            # 用前半部分去省份搜，用后半部分去市搜
            best_province = bk_tree.province().search_one(city_info[:len(city_info) // 2 + 2], search_dist=2,
                                                          min_len=2)
            best_city = bk_tree.city().search_one(city_info[max(0, -len(city_info) // 2 - 2):], search_dist=2,
                                                  min_len=2)
            if best_province and best_city:
                if best_province != best_city:
                    # 防止北京市这种问题
                    # other_info = _handle_district(other_info, best_city)
                    address = best_province + best_city + other_info
    return address


def _handle_district(address: str, city=None):
    if '区' not in address and '县' not in address:
        return address

    if '区' in address:
        key_words = '区'
    elif '县' in address:
        key_words = '县'

    district_info = address.split(key_words)[0] + key_words
    other_info = address.split(key_words)[1]
    if not city:
        # 暂时先不做处理
        return address
    else:
        district_list = district_info_dict.get(city, None)
        if district_list:
            district_tree = bk_tree.BKTree()
            for district in district_list:
                district_tree.insert_node(district)
            best_district = district_tree.search_one(district_info, search_dist=2, min_len=1)
            if best_district:
                if best_district != district_info:
                    logger.debug('replace {} to {} by district process'.format(district_info, best_district))
                    address = best_district + other_info
    return address


if __name__ == "__main__":
    wrong_address = '江西省上集市都阳县芦田乡小塘村828号'
    # 安徽省长明市居巢区巢湖中路商业
    format_result = format_address(wrong_address)
    print(format_result)
