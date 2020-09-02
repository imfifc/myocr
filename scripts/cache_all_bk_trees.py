import os
from concurrent import futures
from datetime import datetime
from ocr_structuring.core.utils.bk_tree import CURRENT_DIR
from ocr_structuring.core.utils.bk_tree.loader import load_from_disk, SOURCE_DIR_NAME

if __name__ == '__main__':
    print('Start loading bk-trees')
    start_time = datetime.now()
    count = 0
    pool = futures.ProcessPoolExecutor()
    fs = []
    for filename in os.listdir(os.path.join(CURRENT_DIR, SOURCE_DIR_NAME)):
        fs.append(pool.submit(load_from_disk, CURRENT_DIR, filename, force=False))
        count += 1
    futures.wait(fs)
    print(f'Complete loading bk-trees[{count}]: {(datetime.now() - start_time).total_seconds()}s')
