import cv2
import sys
import os
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('必须传递一个参数作为图片路径')
        exit(-1)
    img_path = sys.argv[1]
    img = cv2.imread(img_path)
    winname = os.path.basename(img_path).encode("gbk").decode(errors="ignore")
    cv2.imshow(winname, img)
    cv2.waitKey()
