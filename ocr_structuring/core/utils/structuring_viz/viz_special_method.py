import functools
import numpy  as np
import cv2
import matplotlib.pyplot as plt
from ..structuring_viz import cfgs
from .viz_common import *


def viz_crnn_result(crnn_res, crnn_rect, img):
    img_copy = img.copy()
    contour = get_contour_of_box(crnn_rect)
    img_copy = cv2.drawContours(img_copy, [contour], -1, (0, 255, 0), 2)
    img_copy = cv2.putText(img_copy, 'text is {}'.format(crnn_res), (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                           (0, 255, 0), 1)
    return img_copy


def viz_post_crnn_date(func):
    @functools.wraps(func)
    def wrapper(self, item_name, passed_nodes, node_items, img):
        res = func(self, item_name, passed_nodes, node_items, img)
        if cfgs.VIZ_POST_CRNN_FUNC and common_plot_condition_for_post_func(self, item_name):
            if self.debug_data.post_func_info['post_func_crnn_data'].get(item_name, None) is not None:
                # 说明做了这个处理：
                crnn_res = self.debug_data.post_func_info['post_func_crnn_data'][item_name]['crnn_res']
                crnn_rect = self.debug_data.post_func_info['post_func_crnn_data'][item_name]['crnn_rect']
                img_copy = viz_crnn_result(crnn_res, crnn_rect, self.debug_data.image)
            else:
                img_copy = img.copy()
                img_copy = cv2.putText(img_copy, 'crnn not detect any data', (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8,
                                       (0, 255, 0), 1)
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            cv2.imwrite(
                os.path.join(write_path, f'{fid}_parser_[{item_name}]_08_crnn_result.jpg'), img_copy
            )
        return res

    return wrapper


