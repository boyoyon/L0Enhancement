# https://github.com/safaa-alnabulsi/ILS/blob/main/development/ILS-notebook.ipynb
# pip install pyfftw

# https://github.com/safaa-alnabulsi/ILS/blob/main/development/ILS-notebook.ipynb
# pip install pyfftw

from __future__ import division            # forces floating point division 
import numpy as np                          # Numerical Python 
#import matplotlib.pyplot as plt             # Python plotting
#from PIL import Image                       # Python Imaging Library
import cv2, os, sys
# to measure exec time
#from timeit import default_timer as timer   
import pyfftw

## # Constants
lam = 1
k = 5
p = 0.8 # Power norm: The parameter p controls the sensitivity to the edges in the    input image
eps = 0.0001
gamma = 0.5 * p - 1
c =  p * eps**gamma


# point spread function (PSF) is impulse response, describes the response of an imaging system to a point source or point object.
# optical transfer function (OTF) is defined as the Fourier transform of the point spread function 
# ---------------------------------------------------------------------

def _fft(img, interface='single'):
    if interface == 'single':
        out = np.fft.fft2(img,axes=(0,1))
    elif interface == 'parallel_numpy':
        out = pyfftw.interfaces.numpy_fft.fft2(img,axes=(0,1))
    elif interface == 'parallel_scipy':
        out = pyfftw.interfaces.scipy_fftpack.fft2(img,axes=(0,1)) 
    return out

def _ifft(img, interface='single'):
    if interface == 'single':
        out = np.fft.ifft2(img,axes=(0,1)).real
    elif interface == 'parallel_numpy':
        out = pyfftw.interfaces.numpy_fft.ifft2(img,axes=(0,1)).real
    elif interface == 'parallel_scipy':
        out = pyfftw.interfaces.scipy_fftpack.ifft2(img,axes=(0,1)).real
    return out


def psf2otf_Dx(outSize, interface):
    psf = np.zeros(outSize)
    psf = psf.astype('float32')
    psf[0, 0] = -1 
    psf[0, -1] = 1 
    otf =  _fft(psf, interface)
    return otf

def psf2otf_Dy(outSize, interface):
    psf = np.zeros(outSize)
    psf = psf.astype('float32')
    psf[0, 0] = -1 
    psf[-1, 0] = 1 
    otf =  _fft(psf, interface)
    return otf

def ILS_Norm(F,c,lam, interface='single'):
    N, M, D = F.shape # (768, 1024, 3)
    sizeI2D = [N, M]

    # ----------------------------------------------------------------------------------------------------------

    # pre-compute
    otfFx = psf2otf_Dx(sizeI2D,interface)
    otfFy = psf2otf_Dy(sizeI2D,interface)

    Denormin = np.abs(otfFx)**2 + np.abs(otfFy)**2  # take the real part and to power of two
    Denormin = Denormin[:,:, np.newaxis] # add a third axis
    Denormin = np.repeat(Denormin, D, axis=2) # repeat the same data D=3 times on the third axis=2

    denominator = 1 + 0.5 * c * lam * Denormin
    
    # ----------------------------------------------------------------------------------------------------------
    U = F
    normin1 =  _fft(U, interface)
    # ----------------------------------------------------------------------------------------------------------

    for i in range(4):
        ## Step 1:  eq 7 - Intermediate variables \mu update, in x-axis and y-axis direction

        # Gradients delta u on x axis and delta u on y axis

        # image gradient in x direction
        u_extra_col = (U[:,0,:] - U[:,-1,:])[:,np.newaxis,:]
        u_extra_row = (U[0,:,:] - U[-1,:,:])[np.newaxis,:,:]

        u_h = np.hstack((np.diff(U,1,1), u_extra_col))
        u_v = np.vstack((np.diff(U,1,0), u_extra_row))


        mu_h = c * u_h - p * u_h * (u_h * u_h + eps)**gamma
        mu_v = c * u_v - p * u_v * (u_v * u_v + eps)**gamma 


        ### ---------------------------------------------------------------------------- ##
        ## Step 2: eq 9 - Update the smoothed image U

        # The diff causes loss in one columns
        extra_col = (mu_h[:,-1,:] - mu_h[:, 0,:])[:,np.newaxis,:]
        extra_row = (mu_v[-1,:,:] - mu_v[0,:,:])[np.newaxis,:,:]    

        # we calculate the diff - the inverse first order derivative of μxn along x-axis & μyn along y-axis 
        normin2_h = np.hstack((extra_col , - np.diff(mu_h,1,1)))
        normin2_v = np.vstack((extra_row , - np.diff(mu_v,1,0)))
        
        fft_normin_h_v = _fft(normin2_h + normin2_v, interface)

        numerator = normin1 + 0.5 * lam * fft_normin_h_v

        FU = numerator / denominator
        U =  _ifft(FU, interface)

        # U = np.abs(ifft2(FU,axes=(0,1)))
        normin1 = FU
    
    return U


def show_image(original, smoothed, t):
    fig = plt.figure(figsize=(20, 16), dpi=80)

    ax1 = fig.add_subplot(3,3,1)
    ax1.imshow(original)
    ax1.set_title('Original Image')

    ax2 = fig.add_subplot(3,3,2)
    ax2.imshow(smoothed)
    ax2.set_title(t)

    smoothed= np.int32(smoothed)
    original= np.int32(original)
    reduced_noise = original - smoothed
    
    ax3 = fig.add_subplot(3,3,3)
    ax3.imshow(reduced_noise)
    ax3.set_title('Reduced Noise')

    plt.show()
    

def show_reduced_noise(original, smoothed, t):
    fig = plt.figure(figsize=(20, 16), dpi=80)

    ax3 = fig.add_subplot(3,3,1)

    reduced_noise = get_reduced_noise_image(original, smoothed)
    ax3.imshow(reduced_noise)
    ax3.set_title(t)

    plt.show()

def show_single_image(img,t=''):
    plt.figure()
    plt.imshow(img)
    plt.title(t)

# Read the image and normalize its values between zero and one
def read_image(image_fulll_path):
    im = cv2.imread(image_fulll_path)
    info = np.iinfo(im.dtype) # get the data type of the input image
    F = im.astype('float32') / info.max # divide all values by the largest possible value in the datatype
    return F


def get_reduced_noise_image(original, smoothed):
    smoothed= np.int32(smoothed)
    original= np.int32(original)

    return original - smoothed

def main():

    argv = sys.argv
    argc = len(argv)

    print('%s executes L0-smoothing' % argv[0])
    print('[usage] python %s <image>' % argv[0])

    if argc < 2:
        quit()

    #freq = cv2.getTickFrequency()

    F = read_image(argv[1])

    #count0 = cv2.getTickCount()

    #smoothed1 = ILS_Norm(F,c,lam,interface='single')

    #count1 = cv2.getTickCount()
    #print((count1 - count0) / freq)

    #cv2.imshow('smoothd1', smoothed1)

    #count0 = cv2.getTickCount()

    smoothed2 = ILS_Norm(F,c,lam, interface='parallel_numpy')

    #count1 = cv2.getTickCount()
    #print((count1 - count0) / freq)

    #cv2.imshow('smoothed2', smoothed2)

    #count0 = cv2.getTickCount()

    #smoothed3 = ILS_Norm(F,c,lam,interface='parallel_scipy')

    #count1 = cv2.getTickCount()
    #print((count1 - count0) / freq)

    cv2.imshow('smoothed2', smoothed2)

    print('Hit s-key to save and terminate')
    print('Hit any other key to quit')

    key = cv2.waitKey(0)
    cv2.destroyAllWindows()

    if key == ord('s') or key == ord('S'):
        base = os.path.basename(argv[1])
        filename = os.path.splitext(base)[0]
        dst_path = '%s_l0smoothed.png' %    filename

        dst = np.clip(smoothed3 * 255,0,255).astype(np.uint8)
        cv2.imwrite(dst_path, dst)
        print('save %s' % dst_path)

if __name__ == '__main__':
    main()