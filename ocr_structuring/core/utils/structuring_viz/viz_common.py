import cv2
import os
import numpy as np
import shutil
from matplotlib.font_manager import FontManager, FontProperties
from PIL import Image, ImageDraw, ImageFont
from collections import OrderedDict
from ..structuring_viz import cfgs
from .cfgs import CLASS_NAME

def get_write_path(output_dir, fid):
    if cfgs.SAVE_GROUP_BY_FID:
        write_path = os.path.join(output_dir, fid)
    else:
        write_path = output_dir


    if os.path.exists(write_path) and cfgs.CLEAN_DIR:
        cfgs.CLEAN_DIR = False  # 注意，现在这个程序是线程不安全的，多线程目录会被清空多次
        shutil.rmtree(write_path)
    if not os.path.exists(write_path):
        os.mkdir(write_path)
    return write_path


def common_plot_condition(self):
    cond1 = self.debug_data is not None
    cond2 = str(self.debug_data.fid) in cfgs.FID_SUPPORT_LIST
    cond3 = self.item_name in cfgs.VIZ_FG_ITEM_LIST
    return cond1 and cond2 and cond3


def common_plot_condition_for_post_func(self, item_name):
    cond1 = self.debug_data is not None
    cond2 = str(self.debug_data.fid) in cfgs.FID_SUPPORT_LIST
    cond3 = item_name in cfgs.VIZ_FG_ITEM_LIST
    return cond1 and cond2 and cond3


def common_plot_condition_for_tmpl_func(self, structure_items):
    # self 有debug_data , 然后 structure_item包含cfgs中需要绘制的内容
    cond1 = self.debug_data is not None
    cond2 = str(self.debug_data.fid) in cfgs.FID_SUPPORT_LIST
    cond3 = set(cfgs.VIZ_FG_ITEM_LIST).intersection(set(structure_items.keys())) == set(cfgs.VIZ_FG_ITEM_LIST)
    return cond1 and cond2 and cond3


def get_par_dir(file_path, loop=3):
    for i in range(loop):
        file_path = os.path.dirname(file_path)
    return file_path


def getChineseFont():
    return FontProperties(fname=cfgs.TTF_FONT_PATH)


def get_contour_of_box(bbox):
    xmin, ymin, xmax, ymax = np.array(bbox).astype(int)
    contour = np.array([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
    return contour


def add_contour_to_image(image, bbox, color=(0, 0, 0)):
    image = image.copy()
    for bx in bbox:
        contour = get_contour_of_box(bx)
        image = cv2.drawContours(image, [contour], -1, color, 1)
    return image


def get_template(self):
    if self.debug_data is not None:
        class_name = cfgs.CLASS_NAME
        template_jpg = os.path.join(
            get_par_dir(os.path.abspath(__file__), 3), 'template/config/', f'{class_name}.jpg')
        template_jpg = cv2.imread(template_jpg)
        return template_jpg.copy()
    else:
        assert 1 == 2, 'template not exists'


def get_bbx(node_items):
    if type(node_items) == dict or type(node_items) == OrderedDict:
        bbx = [node.bbox.rect for node in node_items.values()]
    else:
        bbx = [node.bbox.rect for node in node_items]
    bbx_c = []
    for bx in bbx:
        xmin, ymin, xmax, ymax = bx
        bbx_c.append([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
    bbx = np.array(bbx_c)
    return bbx


def viz_bg_node_items(node_items, img):
    # 展示哪些node_items被认为是一个bg_item
    filter_items = [node for node in node_items.values() if node.is_bg_item]
    bbx = get_bbx(filter_items)
    img_org = img.copy()
    img_with_bbx = cv2.drawContours(img_org, bbx, -1, 255, 3)
    return img_with_bbx


def viz_all_node_items(node_items, img):
    # 用于检查未做处理前的bbx的信息
    bbx = get_bbx(node_items)
    img_org = img.copy()
    img_with_bbx = cv2.drawContours(img_org, bbx, -1, 255, 3)

    img_text = np.ones(shape=img_org.shape) * 255
    img_text = Image.fromarray(img_text.astype(np.uint8))
    draw = ImageDraw.Draw(img_text)
    font = ImageFont.truetype(cfgs.TTF_FONT_PATH,
                              15, encoding='utf-8')
    for bx, node in zip(bbx, node_items.values()):
        xmin, ymin = bx[0].tolist()
        draw.text((xmin, ymin), node.text, (0, 0, 0), font=font)
    img_text = cv2.cvtColor(np.array(img_text), cv2.COLOR_RGB2BGR)
    img_text = cv2.drawContours(img_text, bbx, -1, 255, 3)
    return img_with_bbx, img_text


def viz_chinese_char_on_img(img, text, loc=(10, 20), color=(0, 0, 0)):
    img_text = Image.fromarray(img)
    draw = ImageDraw.Draw(img_text)
    font = ImageFont.truetype(cfgs.TTF_FONT_PATH,
                              15, encoding='utf-8')

    draw.text(loc, text, color, font=font)
    return np.array(img_text)


def viz_filter_node_items_text(node_items, img):
    bbx = get_bbx(node_items)
    img_org = img.copy()
    img_text = np.ones(shape=img_org.shape) * 255
    img_text = Image.fromarray(img_text.astype(np.uint8))
    draw = ImageDraw.Draw(img_text)
    font = ImageFont.truetype(cfgs.TTF_FONT_PATH,
                              25, encoding='utf-8')
    for bx, node in zip(bbx, node_items.values()):
        if node.is_filtered != False:
            xmin, ymin = bx[0].tolist()
            draw.text((xmin, ymin), node.text, (0, 0, 0), font=font)

    img_text = cv2.cvtColor(np.array(img_text), cv2.COLOR_RGB2BGR)
    for bx, node in zip(bbx, node_items.values()):
        if not node.is_filtered:
            img_text = cv2.drawContours(img_text, [bx], 0, 255, 3)

    return img_text


def viz_filter_node_items(node_items, img):
    # 用于检查未做处理前的bbx的信息
    bbx = get_bbx(node_items)
    img_org = img.copy()
    for bx, node in zip(bbx, node_items.values()):
        if not node.is_filtered:
            img_org = cv2.drawContours(img_org, [bx], 0, 255, 3)

    return img_org


def viz_bg_node_items(node_items, img):
    # 展示哪些node_items被认为是一个bg_item
    filter_items = [node for node in node_items.values() if node.is_bg_item]
    bbx = get_bbx(filter_items)
    img_org = img.copy()
    img_with_bbx = cv2.drawContours(img_org, bbx, -1, 255, 3)
    return img_with_bbx


def viz_bg_node_items(node_items, img):
    # 展示哪些node_items被认为是一个bg_item
    filter_items = [node for node in node_items.values() if node.is_bg_item]
    bbx = get_bbx(filter_items)
    img_org = img.copy()
    img_with_bbx = cv2.drawContours(img_org, bbx, -1, 255, 3)
    return img_with_bbx
