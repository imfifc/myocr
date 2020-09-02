OUTPUT_DIR = '/Users/xuan/Documents/project/structuring/tmp/viz_res/zhuyuan'
TTF_FONT_PATH = '/System/Library/Fonts/PingFang.ttc'
CLASS_NAME = 'beijing_zhuyuan'
SAVE_GROUP_BY_FID = False # 检查单项时，可以关闭这个选项，设置为False时，debug保存的图片会按照fid的文件夹组织
CLEAN_DIR = False  # 在本次测试时是否删除该文件夹下上次存留的debug信息

# --------------------- DEBUG 前景偏移---------------------
VIZ_BG_SCALE_AND_ABOVE_OFFSET = False # 是否要对bg scale 和 above offset 进行可视化
VIZ_ABOVE_OFFSET_DETAIL = False # 是否要展示详细的前景偏移计算过程
VIZ_AREA_FILTER =False


# ------------------DEBUG fg item 处理过程
VIZ_PRE_FUNC = False # 展示 prefunc 处理前后的差异
VIZ_REGEX_FILTER = False  # 展示正则过滤结果
VIZ_POST_FUNC = False # 展示后处理返回结果



# --------------DEBUG SPECIAL-----------------
# 对一些特殊的处理函数单独定制debug 过程，这里展示crnn的处理区域，处理结果
VIZ_POST_CRNN_FUNC = False


# -------------DEBUG TMPL POST FUNC -----------
# 展示后处理结果
VIZ_TMPL_POST_FUNC = False

# 这里显示要对哪些fg item的结构化过程做可视化
VIZ_FG_ITEM_LIST = [
]

# -------------------- VIS_FID ---------------------
# 这里显示要对哪些 fidnn 的结果保留可视化结果
FID_SUPPORT_LIST =[
]
# ['0c300001bfa84554ac6bbf6ce8e5536c', 'c26f64a2e7ec49478cfa5fcca978344d', '41b3574544f3456e966a362b237f047a', '04e0d26f12074e5f962123ae35881fad', '6b5de6ebf0494f0a86634345a6edcab5', '02b99a8d352741c3961ee7c2b356a70e', 'e62403cee0f24df09b50ecf5cc014731', 'c4ecaff10bb04c198a0098dda5fc54f3', 'f2047040d5ee4b6faf77896314e38cf1', '872a39035ce346d3a9c388c2c7671bad', 'bdabb776696949039b2fedad02b045a1', 'b2d8fd8bdd044f44b6d58fe2e20183a1', '43450718c18b43f1b2a71fb14a0a0770', '55bf6705dda24c62b115e8914e4e319c', 'd5d47e4315f344ccbe3a1fdccf85d3ef', '82ce3f2fd0414f2397c13e5a1ebe4f39', '66f24325567b4254a07240a5d8d5af34', '9445748a29054ef6a414d3e2d278460b', '0de6624728304e4e873a89116795da83', 'e00cbc16fa8b441981286e3cbbcc3f13', '8be0135e9d3440999455ff9bfc1e1218', '5df5b883acb0473d9f70e90d03d62ebd', 'fdb31b29158548eb8e8d060ace08d845', '15801300adb74c8d80ab1a50ce6cfc3d', '99af267b48e549be8ef6bd16221d4160', '740bcaefeccf4e269abdd7b9e9daa755', '3155d398d476409980ce42e19ac04b8a']