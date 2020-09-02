import os

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

SUMMARY_CHARGES = 'summary_charges.txt'

# 内存中的text数据
DATA_MEMORY = {
    SUMMARY_CHARGES: None
}


def summary_charges():
    return __get_data(SUMMARY_CHARGES)


def __get_data(data_name):
    if data_name not in DATA_MEMORY:
        raise NotImplementedError('DATA: %s not existed' % data_name)
    if DATA_MEMORY[data_name] is None:
        with open(os.path.join(CURRENT_DIR, data_name), 'r', encoding='utf-8') as f:
            DATA_MEMORY[data_name] = set([t.strip() for t in f.readlines()])
    return DATA_MEMORY[data_name]