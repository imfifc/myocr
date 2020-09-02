import re

import editdistance as ed

from ocr_structuring.core.utils.address_util import get_city_info_dict as city_data

def get_province_data():
    for province, cities in city_data().items():
        if province.endswith('市'):
            continue
        yield province, cities


def get_city_data():
    for province, cities in city_data().items():
        if province.endswith('市'):
            yield province, cities['市辖区']

        for city, counties in cities.items():
            yield city, counties


def province_exists(province: str) -> bool:
    for p, _ in get_province_data():
        if p == province:
            return True
    return False


def city_exists(city: str) -> bool:
    for c, _ in get_city_data():
        if c == city:
            return True
    return False


def fix_province_by_city(province_part: str, city: str) -> str:
    """
    通过城市修复省份残片，如给定省份残片为"苏省"，城市为"苏州市"，则输出为"江苏省"
    :param province_part:
    :param city:
    :return:
    """
    provinces = get_province_data()
    for province, cities in provinces:
        if city in cities.keys():
            return province
    return province_part


def guess_province_city_county(province_part: str, city_part: str, county: str) -> str:
    """
    通过残缺城市和县区预测省份残片，如给定省份残片为"苏省"，城市为"苏州市"，则输出为"江苏省"
    :param province_part:
    :param city_part:
    :return:
    """
    provinces = get_province_data()
    province_data = city_data().get(province_part, None)
    if province_data:  # 如果存在该省，就只使用该省
        provinces = [(province_part,province_data)]

    candis = []
    for p, cities in provinces:
        p_eval = ed.eval(p, province_part)
        guess_cc = guess_city_county(city_part, county, list(cities.items()))
        candis.append((p, guess_cc[0], guess_cc[1], p_eval+guess_cc[2]))
        if p_eval == 0 or guess_cc[2] == 0:
            return candis[-1]
    return __min_dist(candis, 3, province_part)


def guess_city_county(city_part: str, county: str , cities = None):
    """
    通过残缺城市和县区预测省份残片，如给定省份残片为"苏省"，城市为"苏州市"，则输出为"江苏省"
    :param province_part:
    :param city_part:
    :return:
    """
    if city_part is None and county is None:
        return (None, None, 0)

    if cities is None:
        cities = list(get_city_data())

    if city_part:
        city_data = [item for item in cities if item[0] == city_part]
        if len(city_data) > 0:  # 如果有完全匹配的城市，则只使用完全匹配的城市数据
            cities = city_data
    # 如果不存在县区，直接返回最小编辑距离的城市
    candis = []
    if county is None:
        min1 = __min_dist([(c, county, ed.eval(c, city_part)) for c, _ in cities], 2, city_part)
        if min1[2] == 0:
            return min1
        min2 = __guess_city_county(None,city_part,cities,remove_suffix=False,filter=lambda x:x.endswith('市'))
        return  min1 if min2 is None or min1[2] <min2[2] else (min2[1],None,min2[2])

    return __guess_city_county(city_part,county,cities)


def __guess_city_county(city_part: str, county: str, cities=None,remove_suffix=True, filter=None):
    county_part = county
    candis = []
    if remove_suffix and len(county) > 1:  # 去掉区县，计算编辑距离
        county_part = county[:-1]
    for city, counties in cities:
        city_eval = ed.eval(city, city_part) if city_part else 0
        county_min = (county, len(county)) if len(counties) == 0 \
            else __min_dist([(c, ed.eval(c[:-1], county_part)) for c in counties if filter is None or not filter(c)], 1, county)
        if county_min:
            candis.append((city, county_min[0], city_eval + county_min[1]))
        # 找到城市完全相等的直接返回
        if city_part and city_eval == 0:
            return candis[-1]
    return __min_dist(candis, 2, city_part)


def __min_dist(candis,index_key,text=None):
    """
    优先取最小值中，文本与Text相互包含的item
    :param candis:元组list，且元组的第一个元素为文本
    :param index_key:
    :param text:
    :return:
    """
    if len(candis)==0:
        return None
    if text is None:
        return min(candis,key=lambda x:x[index_key])
    candis.sort(key=lambda x:x[index_key])
    result = candis[0]
    for item in candis:
        if item[index_key] != result[index_key]:
            break
        if text in item[0] or item[0] in text:
            result = item
            break
    return result
def fix_city_by_province(city_part: str, province: str) -> str:
    """
    通过省份修复城市
    :param city_part:
    :param county:
    :return:
    """
    province_cities = city_data().get(province,None)
    if not province_cities:
        return city_part
    candis = {}
    for city, _ in province_cities.items():
        candis[city] = ed.eval(city, city_part)
    if len(candis) == 0:
        return city_part

    return min(candis, key=candis.get)


def fix_city_by_county(city_part: str, county: str) -> str:
    """
    通过区县修复城市残片，如给定城市残片"海市"，区或县为"浦东新区"，则输出为"上海市"
    :param city_part:
    :param county:
    :return:
    """
    cities = get_city_data()
    candis = {}
    for city, counties in cities:
        if county in counties:
            candis[city] = ed.eval(city, city_part)
    if len(candis) == 0:
        return city_part

    return min(candis, key=candis.get)


def __change_text_by_span(text, sub_text, span):
    return text[:span[0]] + sub_text + text[span[1]:]


def guess_address(address: str, add_province=False, add_city=True, redress_province=True, redress_city=True, redress_county=True):
    pattern = re.compile(r'(.*省)?(.{,6}市)?(.{,6}[县区])?')
    matcher = pattern.match(address)
    if not matcher:
        return address
    province, city, county = matcher.group(1), matcher.group(2), matcher.group(3)
    guess_city = None
    if province:
        # 省份存在
        province_span = matcher.span(1)
        result = guess_province_city_county(province, city, county)
        guess_province, guess_city, guess_county, _ = guess_province_city_county(province, city, county)
    else:
        # 省份不存在
        guess_city, guess_county, _ = guess_city_county(city, county)
    # 区县修正
    if redress_county and county and county != guess_county:
        if not add_city and city is None:  # 解决将‘杭州余杭区’ 纠正成‘余杭区’的情况
            city_county = guess_city[:-1] + guess_county
            if ed.eval(city_county,county) < ed.eval(guess_county,county):
                guess_county = city_county
        # 区县纠正时，不纠正最后一个字，避免将‘山东省沾化县’ 修成 ‘山东省沾化区’
        address = __change_text_by_span(address, guess_county[:-1], (matcher.span(3)[0], matcher.span(3)[1]-1))

    # 城市修正
    if redress_city and city and city != guess_city:
        if not add_province and province is None:  # 解决将‘河南郑州市’ 纠正成‘郑州市’的情况
            guess_province = fix_province_by_city('', guess_city)
            if guess_province and len(guess_province) > 0:
                province_city = guess_province[:-1] + guess_city
                if ed.eval(province_city, city) < ed.eval(guess_city, city):
                    guess_city = province_city
        address = __change_text_by_span(address, guess_city, matcher.span(2))

    # 省份修正
    if redress_province and province and province != guess_province:
        address = __change_text_by_span(address, guess_province, matcher.span(1))

    if city is None and add_city:
        matcher = pattern.match(address)
        province, county = matcher.group(1),  matcher.group(3)
        if province:
            address = address[0:matcher.span(1)[1]]+guess_city +address[matcher.span(1)[1]:]
        elif county:
            address = address[0:matcher.span(3)[0]]+guess_city +address[matcher.span(3)[0]:]

    if province is None and add_province:
        if guess_city:
            address = fix_province_by_city('', guess_city) + address
    return address


def fix_address_prefix(address: str) -> str:
    matcher = re.match(r'(.*省)?(.{,6}市)?(.{,6}[县区])?', address)
    if not matcher:
        return address
    province, city, county = matcher.group(1), matcher.group(2), matcher.group(3)

    # 省份存在但不正确且城市存在的情况下，修复省份
    if province and city and not province_exists(province) and city_exists(city):
        fixed_province = fix_province_by_city(province, city)
        if fixed_province != province:
            province_span = matcher.span(1)
            return fixed_province + address[province_span[1]:]

    # 省份存在且正确但城市错误的情况下，修复城市
    if province and city and province_exists(province) and not city_exists(city):
        fixed_city = fix_city_by_province(province, city)
        if fixed_city != city:
            city_span = matcher.span(2)
            return address[:city_span[0]] + fixed_city + address[city_span[1]:]

    # 省份不存在且城市存在但城市不正确且县区存在的情况下，修复城市
    if not province and city and not city_exists(city) and county:
        fixed_city = fix_city_by_county(city, county)
        if fixed_city != city:
            city_span = matcher.span(2)
            return address[:city_span[0]] + fixed_city + address[city_span[1]:]

    return address



def assert_fix(address_part, expect, add_province=False, add_city=True, redress_province=True, redress_city=True, redress_county=True):
   # fixed_address = fix_address_prefix(address_part)
    fixed_address = guess_address(address_part,
                                  add_province=add_province,
                                  add_city=add_city,
                                  redress_province=redress_province,
                                  redress_city=redress_city,
                                  redress_county=redress_county,
                                  )
    if fixed_address != expect:
        raise RuntimeError(f'【{address_part}】 expect fixed to 【{expect}】, but actual is 【{fixed_address}】')

def __test_default():
    test_data = [('江西省上集市鄱日县芦田乡小塘村828号', '江西省上饶市鄱阳县芦田乡小塘村828号'),
                    ('南省洛阳市涧西区1号', '河南省洛阳市涧西区1号'),
                    ('省涧西区1号', '河南省洛阳市涧西区1号'),
                    ('阳市涧西区1号', '洛阳市涧西区1号'),
                    ('市涧西区1号', '洛阳市涧西区1号'),
                    ('海市浦东新区1号', '上海市浦东新区1号'),
                    ('市浦东新区1号', '上海市浦东新区1号'),
                    ('浦东新区1号', '上海市浦东新区1号'),
                    ('河南州市二七区3号', '河南郑州市二七区3号'),
                    ('浦东新区1号', '上海市浦东新区1号')]

    for args in test_data:
        assert_fix(args[0], args[1])

def __test_add_province():
    test_data = [
                    ('江西省上集市鄱日县芦田乡小塘村828号', '江西省上饶市鄱阳县芦田乡小塘村828号'),
                    ('洛阳市涧西区1号', '河南省洛阳市涧西区1号'),
                    ('涧西区1号', '河南省洛阳市涧西区1号'),
                    ('阳市涧区1号', '河南省洛阳市涧西区1号'),
                    ('市涧西区1号', '河南省洛阳市涧西区1号'),
                    ('海市浦东新区1号', '上海市浦东新区1号'),
                    ('市浦东新区1号', '上海市浦东新区1号'),
                    ('浦东新区1号', '上海市浦东新区1号')]

    for args in test_data:
        assert_fix(args[0], args[1],add_province=True)

def __test_no_add_city():
    test_data = [('江西省上集市鄱日县芦田乡小塘村828号', '江西省上饶市鄱阳县芦田乡小塘村828号'),
                    ('南省阳市涧西区1号', '河南省洛阳市涧西区1号'),
                    ('省涧西区1号', '河南省涧西区1号'),
                    ('阳市涧西区1号', '洛阳市涧西区1号'),
                    ('涧西区1号', '涧西区1号'),
                    ('亢州余杭区2号', '杭州余杭区2号'),
                    ('海市浦东新区1号', '上海市浦东新区1号'),
                    ('市浦东新区1号', '上海市浦东新区1号'),
                    ('浦东新区1号', '浦东新区1号')]

    for args in test_data:
        assert_fix(args[0], args[1],add_city=False)

if __name__ == '__main__':
    __test_default()
    __test_add_province()
    __test_no_add_city()