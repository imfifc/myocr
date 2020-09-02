import math
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import cv2

from ocr_structuring import debugger
from ...utils.debug_data import DebugData
from ...utils.algorithm import ternary_max_search
from ...utils.bbox import BBox
from ocr_structuring.utils.logging import logger
from ...template.tp_node_item import TpNodeItem
from ...template.matcher.tp_conf_bg_item import TpConfBgItem


class BgScale:
    def __init__(self, conf):
        self.bg_items = {}
        is_tp_conf = conf.get('is_tp_conf', False)
        for item_conf in conf.get("bg_items", []):
            node = TpConfBgItem(item_conf, is_tp_conf)
            self.bg_items[node.uid] = node

        self.template_info = conf.get("template_img_size", None)
        self.try_scale_by_template_size = conf.get("try_scale_by_template_size", False)
        if self.template_info is not None and self.try_scale_by_template_size:
            self.template_ratio = self.template_info[0] / self.template_info[1]

    def eval(
        self,
        node_items: Dict[str, TpNodeItem],
        img_height: int,
        img_width: int,
        debug_data: DebugData = None,
    ):
        # 背景元素匹配
        bg_match_pairs = []
        bg_match_all = {}
        new_node_items = {}

        bg_nodes_count = 0
        for bg_item in self.bg_items.values():
            matched_node_items = bg_item.match_node(node_items)

            if len(matched_node_items) == 0:
                continue
            elif len(matched_node_items) == 1:
                matched_node_item = matched_node_items[0]
                matched_node_item.is_bg_item = True

                # merge/split 模式可能会产生新的 node_item，添加到输入中
                if matched_node_item.uid not in node_items:
                    new_node_items[matched_node_item.uid] = matched_node_item

                bg_match_pairs.append((bg_item.uid, matched_node_item.uid))

            if len(matched_node_items) > 0:
                bg_nodes_count += 1
                bg_match_all[bg_item.uid] = matched_node_items

        if (
            bg_nodes_count <= 1
            and self.template_info is not None
            and abs(img_height / img_width - self.template_ratio) < 0.2
        ):
            return self.resize_by_2d_scale(node_items, img_height, img_width)

        node_items.update(new_node_items)

        # 背景缩放
        # self.scale_by_best_match(node_items, bg_match_pairs, bg_match_all)
        if self.check_do_perspective(node_items, bg_match_pairs, img_height, img_width):
            H, mask = self.scale_by_perspective(node_items, bg_match_pairs)

            status = self.check_if_is_normal(node_items)
            if not status:
                logger.debug("use perspective fail , use normal method")
                self.scale_by_best_match(node_items, bg_match_pairs, bg_match_all)

            if H is not None:
                logger.debug("Do bg scale by perspective")
                if debug_data:
                    debug_data.set_H(H)
                debugger.variables.set_H(H)
        else:
            logger.debug("Do bg scale by best match")
            self.scale_by_best_match(node_items, bg_match_pairs, bg_match_all)

    def resize_by_2d_scale(self, node_items, img_height, img_width):
        for node in node_items.values():
            xmin, ymin, xmax, ymax = node.bbox.rect
            org_height = ymax - ymin
            org_width = xmax - xmin
            new_h = org_height / img_height * self.template_info[0]
            new_w = org_width / img_width * self.template_info[1]
            new_xmin = xmin / img_width * self.template_info[1]
            new_ymin = ymin / img_height * self.template_info[0]
            node.bg_scaled_bbox = BBox(
                [new_xmin, new_ymin, new_xmin + new_w, new_ymin + new_h]
            )

    def check_if_is_normal(self, node_items: Dict[str, TpNodeItem]):
        is_normal = True
        # 最简单的判断，如果有很多的框的坐标都到了边界（负值），判断为false
        strange_count = 0
        for node in node_items.values():
            if len(list(filter(lambda x: x < -20, node.trans_bbox))) > 0:
                # 认为存在异常
                strange_count += 1
            if min(node.trans_bbox) < -200:
                is_normal = False
        else:
            if strange_count / len(node_items) > 0.2:
                is_normal = False
        return is_normal

    def scale_by_best_match(
        self,
        node_items: Dict[str, TpNodeItem],
        bg_match_pairs: List[Tuple[str, str]],
        bg_match_all: Dict[str, List[TpNodeItem]],
    ):
        """
        寻找图片与模板图片最佳的缩放和旋转匹配
        :param node_items:
        :param bg_match_pairs:  (bg.uid, node.uid)
        :param bg_match_all:
        :return:
        """
        top_k = min(5, len(bg_match_pairs))
        best_result = None
        best_similarity_value = 0
        for i in range(top_k):
            # 选定一个 label 作为 anchor, 去计算最佳匹配
            match_result = self.get_fixed_label_best_match(
                node_items, i, bg_match_pairs, bg_match_all
            )
            if match_result["similarity_value"] > best_similarity_value:
                best_similarity_value = match_result["similarity_value"]
                best_result = match_result

        if best_result is None:
            return

        for node in node_items.values():
            node.bg_scaled_bbox = node.bbox.transform(
                best_result["target_origin_point"],
                best_result["best_scale"],
                best_result["best_angle"],
                best_result["bg_origin_point"],
            )

    def get_fixed_label_best_match(
        self,
        node_items: Dict[str, TpNodeItem],
        match_pair_idx: int,
        bg_match_pairs: List[Tuple[str, str]],
        bg_match_all: Dict[str, List[TpNodeItem]],
    ):
        """
        :param node_items:
        :param match_pair_idx:
        :param bg_match_pairs:  (bg.uid, node.uid)
        :param bg_match_all:
        :return:
        """
        bg_item = self.bg_items[bg_match_pairs[match_pair_idx][0]]
        matched_node = node_items[bg_match_pairs[match_pair_idx][1]]

        target_w, target_h = matched_node.bbox.width, matched_node.bbox.height
        bg_w, bg_h = bg_item.bbox.width, bg_item.bbox.height
        bg_center = bg_item.bbox.center
        matched_node_center = matched_node.bbox.center

        scale_x, scale_y = bg_w * 1.0 / target_w, bg_h * 1.0 / target_h
        min_scale = min(scale_x / 2.0, scale_y / 2.0)
        max_scale = max(scale_x * 2.0, scale_y * 2.0)
        min_angle, max_angle = -3, 3

        # 将原点移动到锚点的中心
        bg_bboxes = {}
        for bg_uid, it in self.bg_items.items():
            bg_bboxes[bg_uid] = it.bbox.transform(bg_center)

        max_similarity, best_scale, best_angle = self.search_best_scale_and_angle(
            bg_bboxes,
            bg_match_all,
            matched_node_center,
            (min_angle, max_angle),
            (min_scale, max_scale),
        )

        result = {
            "similarity_value": max_similarity,
            "best_angle": best_angle,
            "best_scale": best_scale,
            "bg_origin_point": bg_center,
            "target_origin_point": matched_node_center,
        }

        return result

    def search_best_scale_and_angle(
        self,
        bg_bboxes: Dict[str, BBox],
        matched_bboxes: Dict[str, List[TpNodeItem]],
        matched_node_center: Tuple[float, float],
        angle_range: Tuple[float, float],
        scale_range: Tuple[float, float],
    ):
        """
        三分法搜索最佳缩放与角度大小
        :param bg_bboxes:
        :param matched_bboxes: 把匹配到的背景元素和 node 元素移动到固定锚点的中心
        :param matched_node_center:
        :param angle_range: 角度搜索的范围
        :param scale_range: 缩放搜索的范围
        :return:
        """

        def scale_search(angle):
            def scale_serach_cal_fn(scale: float):
                scale_and_rotate_bboxs = defaultdict(list)
                for bg_uid, boxes in matched_bboxes.items():
                    for it in boxes:
                        scale_and_rotate_bboxs[bg_uid].append(
                            it.bbox.transform(matched_node_center, scale, angle)
                        )

                return self.cal_match_similarity(bg_bboxes, scale_and_rotate_bboxs)

            _result_scale, scale_max_similarity = ternary_max_search(
                scale_range[0], scale_range[1], cal_fn=scale_serach_cal_fn, eps=0.01
            )
            return _result_scale, scale_max_similarity

        def angle_search_cal_fn(angle: float):
            # 固定一个 angle 进行 scale search
            scale, similarity = scale_search(angle)
            return similarity, scale

        result_angle, (best_similarity, result_scale) = ternary_max_search(
            angle_range[0],
            angle_range[1],
            cal_fn=angle_search_cal_fn,
            cal_fn_key=lambda x: x[0],
            eps=0.1,
        )
        return best_similarity, result_scale, result_angle

    def cal_match_similarity(
        self, bg_bboxes: Dict[str, BBox], matched_bbox: Dict[str, List[BBox]]
    ):
        """
        计算两组 bbox 的相似度, 相似度越大说明越匹配
        """
        distances = []
        for bg_uid, bg_bbox in bg_bboxes.items():
            if bg_uid not in matched_bbox:
                continue

            for bbox in matched_bbox[bg_uid]:
                dis = bg_bbox.center_dis(bbox)
                distances.append((dis, bg_uid))

        distances.sort()

        back_matches = {}
        for it in distances:
            bg_uid = it[1]
            if bg_uid in back_matches:
                continue
            back_matches[bg_uid] = it

        similarity_value = 0
        # 根据距离的大小来求匹配程度
        for it in back_matches.values():
            if it is not None:
                similarity_value += math.exp(-it[0] / 1000)
        similarity_value /= len(bg_bboxes) + 1e-8
        return similarity_value

    def scale_by_perspective(
        self, node_items: Dict[str, TpNodeItem], bg_match_pairs: List[Tuple[str, str]]
    ):
        """
        使用 bg_item 的中心点和 node 的中心点做投影变换
        该函数会修改 label_node_list 中的 trans_position
        :param node_items:
        :param bg_match_pairs: (bg_uid, node_uid)
        :return:
        """
        tp_bg_centers = []
        pred_centers = []

        for bg_uid, node_uid in bg_match_pairs:
            tp_bg_centers.append(self.bg_items[bg_uid].bbox.center)
            pred_centers.append(node_items[node_uid].bbox.center)

        # 单应矩阵解释：
        # - https://docs.opencv.org/4.0.0-beta/d9/dab/tutorial_homography.html
        # - https://ags.cs.uni-kl.de/fileadmin/inf_ags/3dcv-ws11-12/3DCV_WS11-12_lec04.pdf
        # mask 表示哪些点参与到了矩阵的计算中
        # LMEDS 和 RANSAC 在参与计算点数较少的情况下效果更差
        H, mask = cv2.findHomography(
            srcPoints=np.array(pred_centers), dstPoints=np.array(tp_bg_centers),
        )

        if H is None:
            return None

        # self.simple_rotate_and_boundingRect(node_items, H)
        self.simple_boundingRect(node_items, H)

        return H, mask

    def simple_rotate_and_boundingRect(self, node_items, H):
        # 投影变换的结果旋正以后求 bounding box
        # http://git.tianrang-inc.com/tianshi/ocr-structuring/issues/2
        rotate_theta = self.get_rotation_theta(H)
        for node in node_items.values():
            src_points = node.bbox.points
            trans_points = cv2.perspectiveTransform(
                np.array([src_points]).astype(np.float32), H
            )[0]
            trans_and_rotate = self.rotate(rotate_theta, trans_points)
            rect = cv2.boundingRect(trans_and_rotate)
            trans_rect = [
                int(rect[0]),
                int(rect[1]),
                int(rect[0] + rect[2]),
                int(rect[1] + rect[3]),
            ]
            node.bg_scaled_bbox = BBox(trans_rect)

    def complex_rotate_and_boundingRect(self, node_items, H):
        # 对每一个投影变换的结果，旋正以后求 bounding box
        # http://git.tianrang-inc.com/tianshi/ocr-structuring/issues/2
        for node in node_items.values():
            src_points = node.bbox.points
            trans_points = cv2.perspectiveTransform(
                np.array([src_points]).astype(np.float32), H
            )[0]
            rotate_theta = self.get_rotation_theta(H, trans_points, use_boundrect=True)
            trans_and_rotate = self.rotate(rotate_theta, trans_points)
            rect = cv2.boundingRect(trans_and_rotate)
            trans_rect = [
                int(rect[0]),
                int(rect[1]),
                int(rect[0] + rect[2]),
                int(rect[1] + rect[3]),
            ]
            node.bg_scaled_bbox = BBox(trans_rect)

    def simple_boundingRect(self, node_items, H):
        # 投影变幻的结果直接求 bounding box
        for node in node_items.values():
            src_points = node.bbox.points
            trans_points = cv2.perspectiveTransform(
                np.array([src_points]).astype(np.float32), H
            )[0]

            rect = cv2.boundingRect(trans_points)

            trans_rect = [
                int(rect[0]),
                int(rect[1]),
                int(rect[0] + rect[2]),
                int(rect[1] + rect[3]),
            ]

            node.bg_scaled_bbox = BBox(trans_rect)

    @staticmethod
    def get_rotation_theta(
        H,
        normal_box=[[100, 100], [300, 100], [300, 200], [100, 200]],
        use_boundrect=True,
    ):
        if use_boundrect:
            xmin, ymin, w, h = cv2.boundingRect(np.array(normal_box))
            xmax = xmin + w
            ymax = ymin + h
            normal_box = np.array(
                [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
            ).reshape(1, 4, 2)
        else:
            normal_box = np.array(normal_box).reshape(1, 4, 2)
        trans_points = cv2.perspectiveTransform(normal_box.astype(np.float32), H)
        pnt0 = trans_points[0][0]
        pnt1 = trans_points[0][1]
        pnt2 = trans_points[0][2]
        pnt3 = trans_points[0][3]
        theta = np.arctan((pnt1[1] - pnt0[1]) / (pnt1[0] - pnt0[0])) * 180 / np.pi
        return theta

    @staticmethod
    def rotate(rotate_theta, trans_points):
        pnt0 = trans_points[0]
        pnt1 = trans_points[1]
        pnt2 = trans_points[2]
        pnt3 = trans_points[3]
        center = (pnt0 + pnt2) / 2 + (pnt1 + pnt3) / 2
        center = center / 2
        M = cv2.getRotationMatrix2D((center[0], center[1]), rotate_theta, 1)
        trans_and_rotate = cv2.transform(trans_points.reshape(1, 4, 2), M)
        return trans_and_rotate

    def check_do_perspective(
        self,
        node_items: Dict[str, TpNodeItem],
        bg_match_pairs: List[Tuple[str, str]],
        img_height: int,
        img_width: int,
    ):
        """
        检查是否要使用投影变换进行背景的缩放匹配
        1. 匹配到的背景图片大于等于 4 个
        TODO: 如果 ROI 没有检测出来，并且目标票据不在图片中间的话，这个条件不好
        2. 将图片划分为四个区域，匹配到的背景至少应该在其中三个区域中
        :return:
        """
        if len(bg_match_pairs) < 4:
            return False

        h, w = img_height, img_width
        blocks = [
            BBox([0, 0, w // 2, h // 2]),  # 'left-top'
            BBox([w // 2, 0, w, h // 2]),  # 'right-top'
            BBox([0, h // 2, w // 2, h]),  # 'left-bottom'
            BBox([w // 2, h // 2, w, h]),  # 'right-bottom'
        ]

        blocks_count = [0, 0, 0, 0]

        for bg_uid, node_uid in bg_match_pairs:
            node = node_items[node_uid]
            for i, block in enumerate(blocks):
                if block.contain_center(node.bbox):
                    blocks_count[i] += 1

        return np.count_nonzero(blocks_count) >= 3
