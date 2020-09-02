# 注意，这个方法不能用来装饰parser_base，必须要在每个模板的parser下使用装饰器

import functools
import matplotlib.pyplot as plt

from .viz_common import *
from ..structuring_viz import cfgs


def viz_tmpl_post_func(func):
    @functools.wraps(func)
    def wrapper(self, structure_items, fg_items , img):
        res = func(self, structure_items, fg_items , img)
        if cfgs.VIZ_TMPL_POST_FUNC and common_plot_condition_for_tmpl_func(self, structure_items):
            org_image = self.debug_data.image
            for idx, need_plot in enumerate(cfgs.VIZ_FG_ITEM_LIST):
                structure_info = structure_items[need_plot]
                text = structure_info.item_name + ' : ' + str(structure_info.content)
                org_image = viz_chinese_char_on_img(org_image, text, loc=(10, (idx + 1) * 15))
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            cv2.imwrite(os.path.join(write_path, f'{fid}_viz_template_post_proc.jpg'), org_image)
        return res
    return wrapper
