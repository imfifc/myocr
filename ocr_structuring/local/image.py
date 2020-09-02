import cv2
import numpy as np
from PIL import Image, ImageColor



def rotate_image(src, angle):
    """
    Rotate image counter-clockwise.
    :param src:
    :param angle: 逆时针旋转的弧度
    :return:
    """
    if angle == 0:
        return src

    h, w = src.shape[:2]
    rotate_matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle * 180 / np.pi, 1)
    rotate = cv2.warpAffine(src, rotate_matrix, (w, h),
                            borderValue=(255, 255, 255))
    return rotate

def rotate_image_expand(src, angle):
    """
    Rotate image counter-clockwise.
    :param src:
    :param angle: 逆时针旋转的弧度
    :return:
    """
    pil_img = Image.fromarray(src)
    pil_img = pil_img.rotate(angle * 180 / np.pi,
                             resample=Image.BICUBIC,
                             expand=True,
                             fillcolor=ImageColor.colormap['white'])
    return np.array(pil_img)


# copy from ocr-utils
def rotate_image_by_90(image, count):
    """
    :param image: opencv image data
    :param count: 0: not rotated
                  1: 90 degree (clockwise)
                  2: 180 degree
                  3: 270 degree
    :return: rotated image data
    """
    count = count & 0x3
    if count == 0:
        return image.copy()
    if count == 1:
        return cv2.flip(cv2.transpose(image), 1)
    if count == 2:
        return cv2.flip(image, -1)
    return cv2.flip(cv2.transpose(image), 0)
