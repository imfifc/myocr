import json
import os

__city_info_dict = None

def get_city_info_dict():
    global __city_info_dict
    if __city_info_dict is None:
        __city_info_dict = json.load(open(os.path.join(os.path.dirname(__file__), 'city.json'), 'r', encoding='utf-8'))
    return  __city_info_dict

