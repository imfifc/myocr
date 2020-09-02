import functools
import os
import shutil
import cv2
import numpy as np
import matplotlib.pyplot as plt
import copy
from matplotlib.font_manager import FontManager, FontProperties
from .viz_common import *
from ..structuring_viz import cfgs

from PIL import Image, ImageDraw, ImageFont


def above_item_offset(self, node_items, img):
    class_name = cfgs.CLASS_NAME
    template_jpg = os.path.join(
        get_par_dir(os.path.abspath(__file__), 3), 'template/config/', f'{class_name}.jpg')
    show_above_offset = cv2.imread(template_jpg)

    show_above_offset = cv2.putText(
        show_above_offset, 'after  above offset : green', (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0), 1)
    show_above_offset = cv2.putText(
        show_above_offset, 'after bg scale is : red', (10, 60), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)

    for node in node_items.values():

        if node.above_offset_bbox is not None:
            c = get_contour_of_box(node.above_offset_bbox.rect)
            # green is after above item offset
            cv2.drawContours(show_above_offset, [c], 0, (0, 255, 0), 2)

        rect = node.bg_scaled_bbox.rect if node.bg_scaled_bbox is not None else node.trans_bbox.rect
        c = get_contour_of_box(rect)
        cv2.drawContours(show_above_offset, [c], 0, (0, 0, 255), 2)
    return show_above_offset


def viz_bg_scale_and_above_offset(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)

        # 做一些绘图操作
        if self.debug_data is not None and \
                cfgs.VIZ_BG_SCALE_AND_ABOVE_OFFSET and \
                str(self.debug_data.fid) in cfgs.FID_SUPPORT_LIST:
            node_items, img, *_ = args
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            viz_bg = viz_bg_node_items(node_items, img)

            org_img_with_bbx, org_img_with_text = viz_all_node_items(node_items, img)
            above_offset_show = above_item_offset(self, node_items, img)

            # 为above offset 画上模板的框：

            cv2.imwrite(os.path.join(write_path, f'{fid}_offset_01_scale_viz_bg.jpg'), viz_bg)
            cv2.imwrite(os.path.join(write_path, f'{fid}_offset_02_scale_org_img_with_bbx.jpg'), org_img_with_bbx)
            cv2.imwrite(os.path.join(write_path, f'{fid}_offset_03_scale_org_img_with_text.jpg'), org_img_with_text)
            cv2.imwrite(os.path.join(write_path, f'{fid}_offset_04_above_item_offset.jpg'), above_offset_show)

    return wrapper


def viz_above_item_offset_iou(func):
    @functools.wraps(func)
    def wrapper(self, node_items, *args, **kwargs):
        if self.debug_data is not None and \
                cfgs.VIZ_ABOVE_OFFSET_DETAIL and \
                str(self.debug_data.fid) in cfgs.FID_SUPPORT_LIST:
            node_items_bak = copy.deepcopy(node_items)

        func(self, node_items, *args, **kwargs)
        if self.debug_data is not None and \
                cfgs.VIZ_ABOVE_OFFSET_DETAIL and \
                str(self.debug_data.fid) in cfgs.FID_SUPPORT_LIST:

            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)

            content_similarity = self.debug_data.above_item_offset_info['content_similarity']
            current_best_match = self.debug_data.above_item_offset_info['current_best_match']
            best_match_above_region = self.debug_data.above_item_offset_info['best_match_above_region']
            # 首先，展示current_best_match

            template = get_template(self)
            for above_idx, above_item in self.above_items.items():
                template_copy = template.copy()
                above_bbox = [above_item.bbox.rect]
                template_copy = add_contour_to_image(template_copy, above_bbox, color=(0, 0, 255))

                # 列出所有的可能匹配的节点在变换后的坐标？
                for node_id, value in content_similarity[above_idx].items():
                    if value > 0.7:
                        node_item = node_items_bak[node_id]
                        template_copy = add_contour_to_image(template_copy, [node_item.trans_bbox.rect],
                                                             color=(255, 0, 0))
                        loc_xmin, loc_ymin, *_ = node_items_bak[node_id].trans_bbox.rect
                        if node_items_bak[node_id].text != '':
                            template_copy = viz_chinese_char_on_img(template_copy, node_items_bak[node_id].text,
                                                                    (loc_xmin, loc_ymin), (0, 0, 0))
                        else:
                            template_copy = viz_chinese_char_on_img(template_copy, 'null', (loc_xmin, loc_ymin),
                                                                    (0, 0, 0))
                cv2.putText(template_copy, str(above_item.is_ban_offset), (10, 10), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                            (0, 255, 0), 1)
                cv2.imwrite(os.path.join(write_path, f'{fid}_offset_05_{above_item.item_name}_01_org_match.jpg'),
                            template_copy)

                # 拿到对应的nodeitem的信息
                template_copy = template.copy()
                if best_match_above_region[above_idx]:
                    use_info = list(best_match_above_region[above_idx].values())[0]
                    if use_info != -1:
                        regeion = above_item.bbox_alternative[use_info].rect
                        template_copy = add_contour_to_image(template_copy, [regeion], color=(0, 0, 255))
                    else:
                        template_copy = add_contour_to_image(template_copy, above_bbox, color=(0, 0, 255))
                else:
                    template_copy = add_contour_to_image(template_copy, above_bbox, color=(0, 0, 255))
                if sum(current_best_match[above_idx].values()) != 0:
                    max_value = max(current_best_match[above_idx].values())
                    for node_idx, value in current_best_match[above_idx].items():
                        if value == max_value:
                            node_item = node_items_bak[node_idx]
                            loc_xmin, loc_ymin, *_ = node_item.trans_bbox.rect
                            template_copy = viz_chinese_char_on_img(template_copy, str(value),
                                                                    (loc_xmin, loc_ymin), (0, 0, 0))
                            template_copy = add_contour_to_image(template_copy, [node_item.trans_bbox.rect])
                cv2.imwrite(os.path.join(write_path, f'{fid}_offset_05_{above_item.item_name}_02_best_match.jpg'),
                            template_copy)

    return wrapper
