import os, sys, cv2
import numpy as np

## # Constants
lam = 1
k = 5
p = 0.8 # Power norm: The parameter p controls the sensitivity to the edges in the    input image
eps = 0.0001
gamma = 0.5 * p - 1
c =  p * eps**gamma

from l0smooth import *

color = (0, 255,0)
thickness = 1

ESC_KEY = 27

# keycode for cv2.waitKeyEx()
LEFT  = 2424832
UP    = 2490368
RIGHT = 2555904
DOWN  = 2621440

font = cv2.FONT_HERSHEY_PLAIN
font_size = 2
font_color = (0, 255, 0)
font_pos = (10, 30)

WIDTH = 1920
HEIGHT = 1080

def AlphaBlend(img1, img2, alpha):
    dst = alpha * img1 + (1.0 - alpha) * img2
    return dst

def usage(progName):
    print('%s executes l0 enhancement' % progName)
    print('%s <image>' % progName)

def main():

    global mouse_x, mouse_y, state

    argv = sys.argv
    argc = len(argv)

    usage(argv[0])
    
    if argc < 2:
        quit()
   
    SCALE = 1.0
    prevSCALE = -1.0

    ALPHA = 0.5
    prevALPHA = -1.0

    src1 = cv2.imread(argv[1])
    H1, W1 = src1.shape[:2]

    if W1 > WIDTH:
        SCALE = WIDTH / W1

    F = read_image(argv[1])
    src2 = ILS_Norm(F,c,lam, interface='parallel_numpy')

    src1 = src1.astype(np.float32) / 255.0

    print('Hit +/- to up/down scale')
    print('Hit arrow-key to up/down alpha')
    print('Hit s-key to save alpha blended image')
    print('hit ESC-key to terminate')

    w = int(W1 * SCALE)
    h = int(H1 * SCALE)

    clone1 = cv2.resize(src1, (w, h))
    clone2 = cv2.resize(src2, (w, h))

    cv2.imshow('source1', clone1)
    cv2.imshow('source2', clone2)
    
    fUPDATE = True

    while True:

        if ALPHA != prevALPHA:
            fUPDATE = True
            prevALPHA = ALPHA


        if SCALE != prevSCALE:
            w = int(W1 * SCALE)
            h = int(H1 * SCALE)
            clone1 = cv2.resize(src1, (w, h))
            clone2 = cv2.resize(src2, (w, h))
            fUPDATE = True
            prevSCALE = SCALE

        if fUPDATE:
            dst = AlphaBlend(clone1, clone2, ALPHA)
            clone3 = np.clip(dst *255, 0,255).astype(np.uint8)
            
            cv2.putText(clone3, 'alpha: %.1f' % ALPHA, 
                font_pos, font, font_size, font_color, 2)
            cv2.imshow('blend', clone3)
            fUPDATE = False

        key = cv2.waitKeyEx(10)
    
        if key == LEFT:
            ALPHA -= 0.1
        
        elif key == UP:
            ALPHA += 0.3

        elif key == RIGHT:
            ALPHA += 0.1

        elif key == DOWN:
            ALPHA -= 0.3

        elif key == ord('-'):
            SCALE *= 0.9

        elif key == ord('+'):
            SCALE *= 1.1

        elif key == ord('s'):
            dst = AlphaBlend(src1, src2, ALPHA)
            dst *= 255.0
            dst = np.clip(dst, 0, 255)
            dst = dst.astype(np.uint8)
            cv2.imwrite('blend.png', dst)

        elif key == ESC_KEY:
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':

    main()
