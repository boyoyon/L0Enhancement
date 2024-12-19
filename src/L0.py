import cv2, os, sys
import numpy as np
from L0_Smoothing import L0Smoothing

def main():

    argv = sys.argv
    argc = len(argv)

    print('%s executes L0-smoothing' % argv[0])
    print('[usage] python %s <image file>' % argv[0])

    if argc < 2:
        quit()

    base = os.path.basename(argv[1])
    filename = os.path.splitext(base)[0]
    dst_path = 'L0smoothed_%s.png' % filename

    Smoothed = L0Smoothing(argv[1], param_lambda=0.01).run()
    Smoothed = np.squeeze(Smoothed)
    Smoothed = np.clip(Smoothed, 0, 1)
    Smoothed *= 255
    Smoothed = Smoothed.astype(np.uint8)

    cv2.imwrite(dst_path, Smoothed)
    print('Save %s' %dst_path)

if __name__ == '__main__':
    main()