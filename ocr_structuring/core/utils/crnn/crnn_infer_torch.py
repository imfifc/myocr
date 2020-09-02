import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from ocr_structuring.core.utils.algorithm import order_points, polygon_to_to_rectangle
from ocr_structuring.core.utils.rbox import RBox
from ocr_structuring.utils.logging import logger
from .helper import ctc_greedy_decoder, softmax
from .label_converter import LabelConverter


class CRNNInferTorch:
    IMG_HEIGHT = 32

    def __init__(self, torch_script_model, chars_file):
        self.converter = LabelConverter(chars_file=chars_file,
                                        ctc_invalid_index=0)
        logger.debug('Load torch script model: %s' % torch_script_model)
        self.model = torch.jit.load(torch_script_model)

        self.model.eval()
        self.input_channel = self.query_input_channel()

        self.to_tensor = transforms.ToTensor()
        self.norm = transforms.Normalize([0.5], [0.5])

    def query_input_channel(self):
        cnn_part = None
        cnn = getattr(self.model, 'cnn')
        if not cnn:
            return 1
        conv0 = getattr(cnn, 'conv0')
        if not conv0:
            return 1

        if conv0.weight.shape[1] in [1, 3]:
            return conv0.weight.shape[1]
        else:
            raise Exception('model with input shape {} not supported !'.format(cnn_part.weight.shape[1]))

    def run(self, img, roi):
        """
        :param img: 原始图像
        :param roi: 目标区域 roi, 可能是一个 (x1, y1, x2, y2) 表示的矩形，可能是一个(x1,y2,x2,y2,x3,y3,x4,y4)的四边形
        :return:
            res: string 重识别的结果
            mean_score: float. Top one path 的每个时间步 softmax 以后求均值
            scores: 每个时间步的 softmax 值
        """
        if check_roi(img, roi):
            return '', []
        croped_img = self._img_pre_process(img, roi)

        # [batch_size, time_step, num_classes]
        logits = self.model(croped_img)

        logits = logits.data.numpy()

        res, index_res = ctc_greedy_decoder(logits, self.converter.ctc_invalid_index)
        res = self.converter.decode(res[0])

        if len(index_res) == 0:
            # return FGItem.NONE_RES
            return '', []

        top_steps = []
        for i in index_res:
            top_steps.append(logits[0][i])

        top_steps = np.array(top_steps)
        softmax_out = softmax(top_steps, axis=1)
        max_softmax = np.max(softmax_out, axis=1)

        return res, max_softmax.tolist()

    def _img_pre_process(self, img, roi):
        """
        crop -> 灰度 -> keep radio resize -> 归一化
        """
        if len(roi) == 4:
            croped_img = self._img_pre_process_hroi(img, roi)
        elif len(roi) == 8:
            croped_img = self._img_pre_process_rroi(img, roi)
            # cv2.imwrite('/Users/xuan/Desktop/test_crop/{}.jpg'.format(np.random.rand()), croped_img)

        # import cv2
        # cv2.imshow('a', croped_img)
        # cv2.waitKey()
        croped_pil_img = Image.fromarray(croped_img)

        if self.input_channel == 1:
            croped_pil_img = croped_pil_img.convert('L')
        w, h = croped_pil_img.size
        w = int(w / h * self.IMG_HEIGHT)
        croped_pil_img = croped_pil_img.resize((w, self.IMG_HEIGHT), Image.BILINEAR)

        out_img = self.norm(self.to_tensor(croped_pil_img))
        out_img = out_img.unsqueeze(0)

        return out_img

    def _img_pre_process_hroi(self, img, roi):
        croped_img = img[int(roi[1]):int(roi[3]), int(roi[0]): int(roi[2])]
        return croped_img

    def _img_pre_process_rroi(self, img, roi):

        """

        :param img: 输入一张图片
        :param rroi: 输入一个rroi(list of x1,y1,x2,y2,x3,y3,x4,y4)
        :return:
        """
        roi = np.array(roi).reshape(4, 2)

        # 获取theta
        ordered_result = order_points(roi)

        xc, yc, w_trans, h_trans, angle = polygon_to_to_rectangle(ordered_result.ravel())

        # 首先获得boudingRect
        xmin, ymin, width, height = cv2.boundingRect(roi)
        xmax = xmin + width
        ymax = ymin + height
        xmin = max(0, xmin)
        ymin = max(0, ymin)

        # 适度的进行enlarge
        enlarge = int(0.1 * width)
        xmin = max(0, xmin - enlarge)
        xmax = xmax + enlarge
        ymin = max(0, ymin - enlarge)
        ymax = ymax + enlarge

        sub_img = img[ymin:ymax, xmin:xmax]

        rows, cols = sub_img.shape[:2]
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        trans_img = cv2.warpAffine(sub_img, M, (cols, rows))

        # 去除掉两侧的
        cx, cy = trans_img.shape[1] / 2, trans_img.shape[0] / 2
        trans_ymin = int(max(0, cy - h_trans / 2))
        trans_xmin = int(max(0, cx - w_trans / 2))
        trans_ymax = int(cy + h_trans / 2)
        trans_xmax = int(cx + w_trans / 2)
        trans_img = trans_img[trans_ymin: trans_ymax, trans_xmin: trans_xmax, :]
        return trans_img


def check_roi(img, roi):
    """
    检查roi是否合法
    :param img:
    :param roi:
    :return:
    """
    if isinstance(roi, RBox) or (isinstance(roi, list) and len(roi) == 8):
        xmin = min(roi[0], roi[2], roi[4], roi[6])
        xmax = max(roi[0], roi[2], roi[4], roi[6])
        ymin = min(roi[1], roi[3], roi[5], roi[7])
        ymax = max(roi[1], roi[3], roi[5], roi[7])
    else:
        xmin, ymin, xmax, ymax = roi

    if ymin > img.shape[0] or ymax > img.shape[0]:
        return True
    if xmin > img.shape[1] or xmax > img.shape[1]:
        return True
    return False
