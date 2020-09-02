"""
北京的医院都有一个 8 位的代号，如果你的票据上有这样一个**编号**，可以查出对应的医院名

.. code-block:: python

    from ocr_structuring.core.utils.beijing_hospital import beijing_hospital_code_name_map
    hospital_name = beijing_hospital_code_name_map['02110003']
    # 北京大学第一医院(北京大学北大医院）

"""

import os

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

beijing_hospital_code_name_map = {}

with open(os.path.join(CURRENT_DIR, 'beijing_hospital.txt'), 'r', encoding='utf-8') as f:
    lines = f.readlines()

    for line in lines:
        line = line.strip()
        splited_line = line.split()
        beijing_hospital_code_name_map[splited_line[0]] = splited_line[1]
