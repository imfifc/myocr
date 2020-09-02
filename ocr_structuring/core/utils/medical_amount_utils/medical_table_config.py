RE_RECOGNIZE_MONEY = False
PRECISELY_SEARCH = False

replace_map = {'O': '0', ',': '.', '_': '', 'Q': '0', 'D': '0', '@': '0', 'B': '8', 'L': '1',
               '~': '', ',': '.', ']': '1', '[': '1', '-': '', 'S': '5', 'Y': '7', ':': '', 'l': '1', 'G': '6'
               }

beijing_table_config1 = {
    'left': [
        ['^门诊大额支付$', '^门诊大.*支付$', '^门.大额支付$', '.{2,}大额支付$', '诊大额支付'],
        ['退休补充支付', '^.{2}补充支付', '.*休补充支付'],
        ['残军补助支付', '.军补助支付'],
        ['单位补.*公疗.*支付', '.*原公疗.*'],
        []
    ],
    'right': [
        ['本次医保范围内金额', '本次医保范.内金额'],
        ['累计医保内范围金额', '累计医保内范.*金额', '累计医保内范围.*'],
        ['年度门诊大额累计支付', '^年度门诊大额累计', '^年度门.*大额累计'],
        ['本次支付后个人账户余额', '本次支付后个人账户.*'],
        []
    ],
    'name': [
        'men_zhen_da_e_zhi_fu',
        'tui_xiu_bu_chong_zhi_fu',
        'can_jun_bu_zhu_zhi_fu',
        'dan_wei_bu_chong_xian_zhi_fu',
        'medicalpaymoney'
    ],
    'template_bg_config':
        {
            'loc': [0, 283, 459, 459],
            'width': 819,
            'height': 497
        },
    're_recog': False
}
beijing_table_config2 = {
    'left': [
        ['本次医保范围内金额', '本次医保范.*内金'],
        ['累计医保内范围金额', '累计医保内范.*金额'],
        ['年度门诊大额累计支付'],
        ['本次支付后个人账户余额', '本次支付后个人账户.*'],
        []

    ],
    'right': [
        ['^起付金额', '^起付金'],
        ['超封顶金额', '超封.金额', '超.{2}金额'],
        ['自付二'],
        ['自费'],
        [],
    ],
    'name': [
        'ben_ci_yi_bao_fan_wei_nei_jin_e',
        'lei_ji_yi_bao_fan_wei_nei_jin_e',
        'nian_du_men_zhen_da_e_lei_ji_zhi_fu',
        'ben_ci_zhi_fu_hou_ge_ren_zhang_hu_yu_e',
        'personal_account_pay_money'
    ],
    'template_bg_config':
        {
            'loc': [245, 283, 590, 457],
            'width': 819,
            'height': 497
        },
    're_recog': False
}
beijing_table_config3 = {
    'left': [
        ['自付一', '自村一'],
        ['起付金额', '起村金额'],
        ['超封顶金额', '超封.*金额'],
        ['自付二', '自村二'],
        ['自费'],
        ['个人.*付金额']
    ],
    'right': None,
    'name': [
        'selfpayone',
        'qi_fu_jin_e',
        'chao_feng_ding_jin_e',
        'selfpaytwo',
        'selfpaymoney',
        'personpaymoney'
    ],
    'template_bg_config':
        {
            'loc': [408, 285, 732, 456],
            'width': 819,
            'height': 497
        },
    're_recog': True
}
beijing_table_config4 = {
    'left': [
        ['本次医保范围内金', '本.*医保范围内金', '本次医保范.内金额'],
        ['年度累计医保范围内金额', '年度累.医.范围内金', '年度.计医保范.内金额', '.*累计医保范围内金额'],
        ['年度居民基本医疗保险基金门诊累计支付', '年.居民基本医疗保险基金', '年度居民基本医疗保.基金门诊.*', '.*居民基本医疗*.'],
        []
    ],
    'right': None,
    'name': [
        'ben_ci_yi_bao_fan_wei_nei_jin_e',
        'lei_ji_yi_bao_fan_wei_nei_jin_e',
        'nian_du_men_zhen_da_e_lei_ji_zhi_fu',
        'medicalpaymoney'
    ],
    'template_bg_config':
        {
            'loc': [82, 283, 459, 459],
            'width': 819,
            'height': 497
        },
    're_recog': False
}

beijing_table_config = [
    beijing_table_config1,
    beijing_table_config2,
    beijing_table_config3,
    beijing_table_config4
]

beijing_teshu_table_config1 = {
    'left': [
        ['统筹基金支付', '统.基金支.{2}'],
        ['住院大额支付', '住院大.支付', '住.大额支付'],
        ['退休补充支付', '^.{2}补充支付', '.*休补充支付'],
        ['残军补助支付', '.军补助支付'],
        ['单位补.*公疗.*支付', '.*原公疗.*'],
        []
    ],
    'right': [
        ['费用起止时间', '.*用起止时.*', '.*用起.*时间'],
        ['本次医保范围内金', '本.*医保范围内金', '本次医保范.*内金额'],
        ['年度统筹基金累计支付', '年度统.*基.*累计支.', '.*度统筹.金累计.*'],
        ['年度大额资金.*住院.*累计支付', '年度大.*资金.*住院.*计支.', '年.大额.*金.*住院.*累计支付'],
        ['本次支付后个人账户余额', '本次支付后个人账户余.*', '.*支付后个人账户.*'],
        []
    ],
    'name': [
        'tong_chou_ji_jin_zhi_fu',
        'zhu_yuan_da_e_zhi_fu',
        'tui_xiu_bu_chong_zhi_fu',
        'can_jun_bu_zhu_zhi_fu',
        'dan_wei_bu_chong_xian_zhi_fu',
        'medicalpaymoney',
    ],
    're_recog': False
}

beijing_teshu_table_config2 = {
    'left': [
        ['本次医保范围内金', '本.*医保范围内金', '本次医保范.*内金额'],
        ['年度统筹基金累计支付', '年度统.*基.*累计支.', '.*度统筹.金累计.*'],
        ['年度大额资金.*住院.*累计支付', '年度大.*资金.*住院.*计支.', '年.大额.*金.*住院.*累计支付'],
        ['本次支付后个人账户余额', '本次支付后个人账户余.*', '.*支付后个人账户.*'],
        []
    ],
    'right': [
        ['起付金额', '起村金额'],
        ['超封顶金额', '超封.*金额'],
        ['自付二', '自村二'],
        ['自费'],
        ['个人.*付金额']
    ],
    'name': [
        'ben_ci_yi_bao_fan_wei_nei_jin_e',
        'nian_du_tong_chou_ji_jin_lei_ji_zhi_fu',
        'nian_du_da_e_zi_jin_zhu_yuan_lei_ji_zhi_fu',
        'ben_ci_zhi_fu_hou_ge_ren_zhang_hu_yu_e',
        'personal_account_balance'
    ],
    're_recog': False
}

beijing_teshu_table_config3 = {
    'left': [
        ['自付一', '自村一'],
        ['起付金额', '起村金额'],
        ['超封顶金额', '超封.*金额'],
        ['自付二', '自村二'],
        ['自费'],
        ['个人.*付金额']
    ],
    'right': None,
    'name': [
        'selfpayone',
        'qi_fu_jin_e',
        'chao_feng_ding_jin_e',
        'selfpaytwo',
        'selfpaymoney',
        'personpaymoney'
    ],
    're_recog': True
}

beijing_table_teshu_config4 = {
    'left': [
        ['本次医保范围内金额', ],
        ['年度居民基本医疗保险', '年度居民基本医疗保.', '金累计.住院.支付金.'],
        []
    ],
    'right': None,
    'name': [
        'ben_ci_yi_bao_fan_wei_nei_jin_e',
        'nian_du_ju_min_ji_ben_yi_liao_bao_xian_ji_jin_lei_ji_zhu_yuan_zhi_fu',
        'medicalpaymoney',
    ],
    're_recog': True
}

beijing_teshu_table_config = [
    beijing_teshu_table_config1,
    beijing_teshu_table_config2,
    beijing_teshu_table_config3,
    beijing_table_teshu_config4
]
