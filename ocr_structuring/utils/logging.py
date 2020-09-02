import logging
import sys

from ocr_structuring import settings

cfg = settings.MyConfig()
logger = logging.getLogger('structuring')
logger.setLevel(cfg.log_level.value)
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(process)d] %(message)s')
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(cfg.log_level.value)
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
