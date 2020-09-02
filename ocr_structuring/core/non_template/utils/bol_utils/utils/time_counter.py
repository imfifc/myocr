import time

from ocr_structuring.utils.logging import logger


def record_time(f):
    def func(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        logger.info('function {} using time : {}'.format(f.__name__, end_time - start_time))
        return result

    return func
