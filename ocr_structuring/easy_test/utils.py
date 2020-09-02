import logging


logger = logging.getLogger('easy_test')
logger.setLevel(logging.DEBUG)

log_handler = logging.StreamHandler()
log_formatter = logging.Formatter('%(levelname)s - %(filename)s[:%(lineno)d] - %(message)s')
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(log_formatter)

logger.addHandler(log_handler)


