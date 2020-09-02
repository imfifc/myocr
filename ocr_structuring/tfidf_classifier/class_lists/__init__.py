class_lists = {
    'all': [],
    'medical_invoice': [
        "beijing_menzhen",
        "beijing_menzhen_teshu",
        "beijing_zhuyuan",
        "shanghai_menzhen",
        "shanghai_zhuyuan"
    ],
    'huarui_huodan': [
        "huarui_yuxiang_jida1",
        "huarui_yuxiang_jida2",
        "huarui_yuxiang_shouxie",
        "huarui_zhongjian_jida",
        "huarui_zhongjian_shouxie_h",
        "huarui_zhongjian_shouxie_v",
    ],
    'huarui_hodan_zhongjian_jida': [
        'zhongjian_jida1',
        'zhongjian_jida2',
        'zhongjian_jida3',
        'zhongjian_jida4',
        'zhongjian_jida5',
        'zhongjian_jida6',
        'zhongjian_jida7',
        'zhongjian_jida8',
        'zhongjian_jida9',
    ],
    'idcard': [
        'idcard',
        'idcard_bk',
    ]
}

for k, v in class_lists.items():
    if k != 'all':
        class_lists['all'].extend(v)
