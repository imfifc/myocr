# encoding=utf-8
import contextlib
import logging
import sys

import numpy as np
import shm_utils.numpy

from ..protos.structuring_pb2 import ImageData


def dump_image(image):
    shape = image.shape
    raw_data = image.tobytes()
    if len(shape) == 3:
        return ImageData(data=raw_data, height=shape[0], width=shape[1], channels=shape[2])
    elif len(shape) == 2:
        return ImageData(data=raw_data, height=shape[0], width=shape[1])
    raise AssertionError('cannot dump image since shape of this data is not correct')


def get_shape(image_data):
    if image_data.channels == 0:
        shape = (image_data.height, image_data.width)
    else:
        shape = (image_data.height, image_data.width, image_data.channels)
    return shape


def load_image(image_data):
    shape = get_shape(image_data)
    return np.frombuffer(image_data.data, dtype=np.uint8).reshape(shape)


@contextlib.contextmanager
def image_from_image_data(image_data):
    if not image_data.shm:
        yield load_image(image_data)
    else:
        shape = get_shape(image_data)
        with shm_utils.numpy.SharedMemory.from_token(image_data.shm, shape=shape, dtype=np.uint8) as shm:
            yield shm.ndarray


@contextlib.contextmanager
def images_from_image_datas(image_datas):
    shms = []
    try:
        images = []
        for image_data in image_datas:
            if not image_data.shm:
                images.append(load_image(image_data))
            else:
                shape = get_shape(image_data)
                shm = shm_utils.numpy.SharedMemory.from_token(image_data.shm, shape=shape, dtype=np.uint8)
                shm.open()
                shms.append(shm)
                images.append(shm.ndarray)
        
        yield images
    finally:
        for shm in shms:
            shm.close()


logger = logging.getLogger('service')
logger.setLevel('DEBUG')

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s[:%(lineno)d] - %(message)s')

log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel('DEBUG')
log_handler.setFormatter(log_formatter)

logger.addHandler(log_handler)
