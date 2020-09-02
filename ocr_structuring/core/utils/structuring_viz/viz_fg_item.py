import functools
import matplotlib.pyplot as plt

from .viz_common import *
from ..structuring_viz import cfgs

plt.rc('figure', figsize=(20, 20))


def get_par_dir(file_path, loop=3):
    for i in range(loop):
        file_path = os.path.dirname(file_path)
    return file_path


def viz_area_filter(func):
    @functools.wraps(func)
    def wrapper(self, area_item):
        func(self, area_item)

        # 对框做filter前后filter后
        # post_func_name = self.debug_data.fg_item_config[self.item_name].get('item_pre_func_name', None)
        # pre_func_name = self.debug_data.fg_item_config[self.item_name].get('item_post_func_name', None）

        #  对node 处理处理前和处理后画图
        if cfgs.VIZ_AREA_FILTER and common_plot_condition(self):
            org_image = self.debug_data.image
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            before_area_filter, _ = viz_all_node_items(self.node_items, org_image)
            after_area_filter = viz_filter_node_items(self.node_items, org_image)

            # 在模板图上绘制各个被在这一步保留的框的trans_box 和 area filter位置，以及绘制ioo
            template = get_template(self)
            pass_node_rect = np.array([pass_node.trans_bbox.rect for pass_node in self.get_passed_nodes().values()]).astype(int)
            template = add_contour_to_image(image=template,bbox=pass_node_rect,color=(0,255,0))
            filter_area = np.array(area_item.area.rect).reshape(1, 4)
            template = add_contour_to_image(image=template, bbox=filter_area, color=(0, 0, 0))
            template = viz_chinese_char_on_img(template,'过滤区域与被过滤留下的trans_box',(10,10),(0,0,0))
            cv2.imwrite(os.path.join(write_path, f'{fid}_parser_[{self.item_name}]_01_org_bbx.jpg'), before_area_filter)
            cv2.imwrite(os.path.join(write_path, f'{fid}_parser_[{self.item_name}]_02_area_filter_detail.jpg'),
                        template)
            cv2.imwrite(os.path.join(write_path, f'{fid}_parser_[{self.item_name}]_02_after_area_filter.jpg'),
                        after_area_filter)

    return wrapper


def viz_pre_func(func):
    @functools.wraps(func)
    def wrapper(self, img):
        if cfgs.VIZ_PRE_FUNC and common_plot_condition(self):
            org_image = self.debug_data.image
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            pre_func_name = self.debug_data.fg_item_config[self.item_name].get('item_pre_func_name', None)
            box, text_before = viz_all_node_items(self.get_passed_nodes(), img)
            cv2.imwrite(
                os.path.join(write_path,
                             f'{fid}_parser_[{self.item_name}]_03_before_prefunc_[{pre_func_name}]_text.jpg'),
                text_before)
        res = func(self, img)
        if cfgs.VIZ_PRE_FUNC and common_plot_condition(self) and \
                pre_func_name is not None:
            after_prefunc, text_after = viz_all_node_items(self.get_passed_nodes(), org_image)
            # text_after = viz_filter_node_items_text(self.node_items,img)
            cv2.imwrite(
                os.path.join(write_path,
                             f'{fid}_parser_[{self.item_name}]_04_after_prefunc_[{pre_func_name}]_filter.jpg'),
                after_prefunc)
            cv2.imwrite(
                os.path.join(write_path, f'{fid}_parser_[{self.item_name}]_05_after_prefunc_[{pre_func_name}]text.jpg'),
                text_after)
        return res

    return wrapper


def viz_regex_filter(func):
    @functools.wraps(func)
    def wrapper(self):
        func(self)
        if cfgs.VIZ_REGEX_FILTER and common_plot_condition(self):
            org_image = self.debug_data.image
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            after_regex_filter = viz_filter_node_items(self.node_items, org_image)
            cv2.imwrite(os.path.join(write_path, f'{fid}_parser_[{self.item_name}]_06_after_regex_filter.jpg'),
                        after_regex_filter)

    return wrapper


def viz_post_func(func):
    @functools.wraps(func)
    def wrapper(self, img):
        if cfgs.VIZ_POST_FUNC and common_plot_condition(self):
            post_func_name = self.debug_data.fg_item_config[self.item_name].get('item_post_func_name', None)
            if post_func_name is not None:
                box, text_before = viz_all_node_items(self.node_items, img)

        res = func(self, img)
        if cfgs.VIZ_POST_FUNC and common_plot_condition(self) and post_func_name is not None:
            org_image = self.debug_data.image.copy()
            fid = self.debug_data.fid
            write_path = get_write_path(cfgs.OUTPUT_DIR, fid)
            try:
                text = res[0]
            except:
                text = None
            org_image = viz_chinese_char_on_img(org_image, str(text))
            cv2.imwrite(
                os.path.join(write_path,
                             f'{fid}_parser_[{self.item_name}]_07_after_postfunc_[{post_func_name}]text.jpg'),
                org_image)
        return res

    return wrapper
