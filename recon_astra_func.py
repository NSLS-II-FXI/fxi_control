import tomopy
from skimage.transform import resize
import numpy as np
import matplotlib.pyplot as plt
import time
import h5py
from scipy.signal import medfilt2d
from pystackreg import StackReg
import scipy.fftpack as sf
import math
import matplotlib.pyplot as mplp
import scipy.ndimage as sn

plt.ion()

def find_rot(fn, thresh=0.05, method=1):
    sr = StackReg(StackReg.TRANSLATION)
    f = h5py.File(fn, "r")
    ang = np.array(list(f["angle"]))
    img_bkg = np.squeeze(np.array(f["img_bkg_avg"]))
    if np.abs(ang[0]) < np.abs(ang[0] - 90):  # e.g, rotate from 0 - 180 deg
        tmp = np.abs(ang - ang[0] - 180).argmin()
    else:  # e.g.,rotate from -90 - 90 deg
        tmp = np.abs(ang - np.abs(ang[0])).argmin()
    img0 = np.array(list(f["img_tomo"][0]))
    img180_raw = np.array(list(f["img_tomo"][tmp]))
    f.close()
    img0 = img0 / img_bkg
    img180_raw = img180_raw / img_bkg
    img180 = img180_raw[:, ::-1]
    s = np.squeeze(img0.shape)
    im1 = -np.log(img0)
    im2 = -np.log(img180)
    im1[np.isnan(im1)] = 0
    im2[np.isnan(im2)] = 0
    im1[im1 < thresh] = 0
    im2[im2 < thresh] = 0
    im1 = medfilt2d(im1, 3)
    im2 = medfilt2d(im2, 3)
    im1_fft = np.fft.fft2(im1)
    im2_fft = np.fft.fft2(im2)
    results = dftregistration(im1_fft, im2_fft)
    row_shift = results[2]
    col_shift = results[3]
    rot_cen = s[1] / 2 + col_shift / 2 - 1

    tmat = sr.register(im1, im2)
    rshft = -tmat[1, 2]
    cshft = -tmat[0, 2]
    rot_cen0 = s[1] / 2 + cshft / 2 - 1

    print(f"rot_cen = {rot_cen} or {rot_cen0}")
    if method:
        return rot_cen
    else:
        return rot_cen0


def rotcen_test2(
    fn,
    start=None,
    stop=None,
    steps=None,
    sli=0,
    block_list=[],
    return_flag=0,
    print_flag=1,
    bkg_level=0,
    txm_normed_flag=0,
    denoise_flag=0,
    fw_level=9,
    algorithm='gridrec',
    n_iter=5,
    circ_mask_ratio=0.95,
    options={},
    atten=None,
    clim=[],
    dark_scale=1,
    snr=3,
    filter_name='None',
    plot_flag=1,
    save_flag=1,
):
    import tomopy

    if not atten is None:
        ref_ang = atten[:, 0]
        ref_atten = atten[:, 1]
        fint = interp1d(ref_ang, ref_atten)

    f = h5py.File(fn, "r")
    tmp = np.array(f["img_tomo"][0])
    s = [1, tmp.shape[0], tmp.shape[1]]

    if denoise_flag:
        addition_slice = 100
    else:
        addition_slice = 0

    if sli == 0:
        sli = int(s[1] / 2)
    sli_exp = [
        np.max([0, sli - addition_slice // 2]),
        np.min([sli + addition_slice // 2 + 1, s[1]]),
    ]
    tomo_angle = np.array(f["angle"]) 
    theta = tomo_angle / 180.0 * np.pi
    img_tomo = np.array(f["img_tomo"][:, sli_exp[0] : sli_exp[1], :])

    if txm_normed_flag:
        prj_norm = img_tomo
    else:
        img_bkg = np.array(f["img_bkg_avg"][:, sli_exp[0] : sli_exp[1], :])
        img_dark = np.array(f["img_dark_avg"][:, sli_exp[0] : sli_exp[1], :]) / dark_scale
        prj = (img_tomo - img_dark) / (img_bkg - img_dark)
        if not atten is None:
            for i in range(len(tomo_angle)):
                att = fint(tomo_angle[i])
                prj[i] = prj[i] / att
        prj_norm = -np.log(prj)
    f.close()

    prj_norm = denoise(prj_norm, denoise_flag)    
    prj_norm[np.isnan(prj_norm)] = 0
    prj_norm[np.isinf(prj_norm)] = 0
    prj_norm[prj_norm < 0] = 0

    prj_norm -= bkg_level

    '''
    prj_norm = tomopy.prep.stripe.remove_stripe_fw(
        prj_norm, level=fw_level, wname="db5", sigma=1, pad=True
    )
    '''
    #prj_norm = tomopy.prep.stripe.remove_all_stripe(prj_norm, snr=snr)
    """    
    if denoise_flag == 1: # denoise using wiener filter
        ss = prj_norm.shape
        for i in range(ss[0]):
           prj_norm[i] = skr.wiener(prj_norm[i], psf=psf, reg=reg, balance=balance, is_real=is_real, clip=clip)
    elif denoise_flag == 2:
        from skimage.filters import gaussian as gf
        prj_norm = gf(prj_norm, [0, 1, 1])
    """
    s = prj_norm.shape
    if len(s) == 2:
        prj_norm = prj_norm.reshape(s[0], 1, s[1])
        s = prj_norm.shape

    if theta[-1] > theta[1]:
        pos = find_nearest(theta, theta[0] + np.pi)
    else:
        pos = find_nearest(theta, theta[0] - np.pi)
    block_list = list(block_list) + list(np.arange(pos + 1, len(theta)))
    if len(block_list):
        allow_list = list(set(np.arange(len(prj_norm))) - set(block_list))
        prj_norm = prj_norm[allow_list]
        theta = theta[allow_list]

    prj_norm = tomopy.prep.stripe.remove_all_stripe(prj_norm, snr=snr)

    if start == None or stop == None or steps == None:
        start = int(s[2] / 2 - 50)
        stop = int(s[2] / 2 + 50)
        steps = 26
    cen = np.linspace(start, stop, steps)
    img = np.zeros([len(cen), s[2], s[2]])
    for i in range(len(cen)):
        if print_flag:
            print("{}: rotcen {}".format(i + 1, cen[i]))
            if algorithm == 'gridrec':
                img[i] = tomopy.recon(
                prj_norm[:, addition_slice//2 : addition_slice//2 + 1],
                theta,
                center=cen[i],
                algorithm="gridrec",
                filter_name=filter_name
                )
            elif 'astra' in algorithm:
            	img[i] = tomopy.recon(
                prj_norm[:, addition_slice//2 : addition_slice//2 + 1],
                theta,
                center=cen[i],
                algorithm=tomopy.astra,
                options=options
                )
            else:
                img[i] = tomopy.recon(
                prj_norm[:, addition_slice//2 : addition_slice//2 + 1],
                theta,
                center=cen[i],
                algorithm=algorithm,
                num_iter=n_iter,
                #filter_name=filter_name
                )
    if save_flag:
        fout = "center_test.h5"
        with h5py.File(fout, "w") as hf:
            hf.create_dataset("img", data=img)
            hf.create_dataset("rot_cen", data=cen)
    img = tomopy.circ_mask(img, axis=0, ratio=circ_mask_ratio)
    if plot_flag:
        tracker = image_scrubber(img, clim)
    if return_flag:
        return img, cen


def recon_astra(fn, rot_cen, sli=[], binning=None, block_list=[], denoise_flag=0, snr=1,fw_level=9, circ_mask_ratio=0.95):
    
    ts = time.time()
    print('loading data ...')
    f = h5py.File(fn, "r")
    tmp = np.array(f["img_tomo"][0])
    s = [1, tmp.shape[0], tmp.shape[1]]
    slice_info = ""
    bin_info = ""
    if binning:
        bin_info = f"_bin_{binning}"
    else:
        binning = 1

    if len(sli) == 0:
        sli = [0, s[1]]
    elif len(sli) == 1 and sli[0] >= 0 and sli[0] <= s[1]:
        sli = [sli[0], sli[0] + 1]
        slice_info = "_slice_{}".format(sli[0])
    elif len(sli) == 2 and sli[0] >= 0 and sli[1] <= s[1]:
        slice_info = "_slice_{}_{}".format(sli[0], sli[1])
    else:
        print("non valid slice id, will take reconstruction for the whole object")

    sid = np.int32(f['scan_id'])
    x_eng = np.float32(f['X_eng'])
    img = np.array(f['img_tomo'][:, sli[0]:sli[-1]])
    bkg = np.array(f['img_bkg_avg'][:, sli[0]:sli[-1]])
    dark = np.array(f['img_dark_avg'][:, sli[0]:sli[-1]])
    scan_id = np.array(f["scan_id"])
    theta = np.array(f["angle"]) / 180.0 * np.pi
    eng = np.array(f["X_eng"])

    rot_cen = (rot_cen * 1.0) / binning    
    img = bin_image_stack(img, binning)
    bkg = bin_image_stack(bkg, binning)
    dark = bin_image_stack(dark, binning)

    img_norm = (img - dark)/(bkg - dark)
    img_norm = denoise(img_norm, denoise_flag)

    n_angle = len(theta)
    total_id = np.arange(n_angle)
    idx = set(list(total_id)) - set(list(block_list))
    idx = np.sort(list(idx))
    img_norm = img_norm[idx]
    theta = theta[idx]
    proj = -np.log(img_norm)
    proj[np.isnan(proj)] = 0
    ##proj = tomopy.prep.stripe.remove_all_stripe(proj, snr=0.2)
    #proj = tomopy.prep.stripe.remove_stripe_based_filtering(proj, sigma=3)
    #proj = tomopy.prep.stripe.remove_stripe_based_sorting(proj)   
    proj = tomopy.prep.stripe.remove_stripe_fw(proj, level=fw_level)
    ts1 = time.time()

    print('reconstruction ...')
    extra_options = {'MinConstraint': 0, }
    options = {'proj_type': 'cuda', 
                'method': 'FBP_CUDA', 
                'num_iter': 20,
                'extra_options': extra_options
                }    
    
    recon = tomopy.recon(proj,
                     theta,
                     center=rot_cen,
                     algorithm=tomopy.astra,
                     options=options,
                     ncore=4)
    ts2 = time.time()
    recon = tomopy.circ_mask(recon, axis=0, ratio=circ_mask_ratio)
    fsave = f"recon_{fn[4:-3]}{str(slice_info)}{str(bin_info)}.h5"
    print('saving data ...')
    with h5py.File(fsave, "w") as hf:
        hf.create_dataset("img", data=recon.astype(np.float32))
        hf.create_dataset("scan_id", data=scan_id)
        hf.create_dataset("X_eng", data=eng)
        hf.create_dataset("rot_cen", data=rot_cen)
        hf.create_dataset("binning", data=binning)
    print(f'file saved to {fsave}')
    ts3 = time.time()
    print(f'time for loading data:   {ts1-ts:3.2f} sec')
    print(f'time for reconstruction: {ts2-ts1:3.2f} sec')
    print(f'time for saving data:    {ts3-ts2:3.2f} sec')


def denoise(prj, denoise_flag):
    if denoise_flag == 1:  # Wiener denoise
        import skimage.restoration as skr

        ss = prj.shape
        psf = np.ones([2, 2]) / (2**2)
        reg = None
        balance = 0.3
        is_real = True
        clip = True
        for j in range(ss[0]):
            prj[j] = skr.wiener(
                prj[j], psf=psf, reg=reg, balance=balance, is_real=is_real, clip=clip
            )
    elif denoise_flag == 2:  # Gaussian denoise
        from skimage.filters import gaussian as gf

        prj = gf(prj, [0, 1, 1])
    return prj



def bin_image_stack(img_stack, binning=1):
    if binning == 1:
        return img_stack
    s = img_stack.shape
    img_b = resize(img_stack, (s[0], s[1]//binning, s[2]//binning))
    return img_b


def find_nearest(data, value):
    data = np.array(data)
    return np.abs(data - value).argmin()


class IndexTracker(object):
    def __init__(self, ax, X, clim):
        self.ax = ax
        self._indx_txt = ax.set_title(" ", loc="center")
        self.X = X
        self.slices, rows, cols = X.shape
        self.ind = self.slices // 2
        if len(clim)==2:
            self.im = ax.imshow(self.X[self.ind, :, :], cmap="gray", clim=clim)
        else:
            self.im = ax.imshow(self.X[self.ind, :, :], cmap="gray")
        self.update()

    def onscroll(self, event):
        if event.button == "up":
            self.ind = (self.ind + 1) % self.slices
        else:
            self.ind = (self.ind - 1) % self.slices
        self.update()

    def update(self):
        self.im.set_data(self.X[self.ind, :, :])
        # self.ax.set_ylabel('slice %s' % self.ind)
        self._indx_txt.set_text(f"frame {self.ind + 1} of {self.slices}")
        self.im.axes.figure.canvas.draw()


def image_scrubber(data, clim, *, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10,10))
    else:
        fig = ax.figure
    tracker = IndexTracker(ax, data, clim)
    # monkey patch the tracker onto the figure to keep it alive
    fig._tracker = tracker
    fig.canvas.mpl_connect("scroll_event", tracker.onscroll)
    return tracker


def dftregistration(buf1ft, buf2ft, usfac=100):
    
    """
           # function [output Greg] = dftregistration(buf1ft,buf2ft,usfac);
           # Efficient subpixel image registration by crosscorrelation. This code
           # gives the same precision as the FFT upsampled cross correlation in a
           # small fraction of the computation time and with reduced memory
           # requirements. It obtains an initial estimate of the
    crosscorrelation peak
           # by an FFT and then refines the shift estimation by upsampling the DFT
           # only in a small neighborhood of that estimate by means of a
           # matrix-multiply DFT. With this procedure all the image points
    are used to
           # compute the upsampled crosscorrelation.
           # Manuel Guizar - Dec 13, 2007

           # Portions of this code were taken from code written by Ann M. Kowalczyk
           # and James R. Fienup.
           # J.R. Fienup and A.M. Kowalczyk, "Phase retrieval for a complex-valued
           # object by using a low-resolution image," J. Opt. Soc. Am. A 7, 450-458
           # (1990).

           # Citation for this algorithm:
           # Manuel Guizar-Sicairos, Samuel T. Thurman, and James R. Fienup,
           # "Efficient subpixel image registration algorithms," Opt. Lett. 33,
           # 156-158 (2008).

           # Inputs
           # buf1ft    Fourier transform of reference image,
           #           DC in (1,1)   [DO NOT FFTSHIFT]
           # buf2ft    Fourier transform of image to register,
           #           DC in (1,1) [DO NOT FFTSHIFT]
           # usfac     Upsampling factor (integer). Images will be registered to
           #           within 1/usfac of a pixel. For example usfac = 20 means the
           #           images will be registered within 1/20 of a pixel.
    (default = 1)

           # Outputs
           # output =  [error,diffphase,net_row_shift,net_col_shift]
           # error     Translation invariant normalized RMS error between f and g
           # diffphase     Global phase difference between the two images (should be
           #               zero if images are non-negative).
           # net_row_shift net_col_shift   Pixel shifts between images
           # Greg      (Optional) Fourier transform of registered version of buf2ft,
           #           the global phase difference is compensated for.
    """

    # Compute error for no pixel shift
    if usfac == 0:
        CCmax = np.sum(buf1ft * np.conj(buf2ft))
        rfzero = np.sum(abs(buf1ft) ** 2)
        rgzero = np.sum(abs(buf2ft) ** 2)
        error = 1.0 - CCmax * np.conj(CCmax) / (rgzero * rfzero)
        error = np.sqrt(np.abs(error))
        diffphase = np.arctan2(np.imag(CCmax), np.real(CCmax))
        return error, diffphase

    # Whole-pixel shift - Compute crosscorrelation by an IFFT and locate the
    # peak
    elif usfac == 1:
        ndim = np.shape(buf1ft)
        m = ndim[0]
        n = ndim[1]
        CC = sf.ifft2(buf1ft * np.conj(buf2ft))
        max1, loc1 = idxmax(CC)
        rloc = loc1[0]
        cloc = loc1[1]
        CCmax = CC[rloc, cloc]
        rfzero = np.sum(np.abs(buf1ft) ** 2) / (m * n)
        rgzero = np.sum(np.abs(buf2ft) ** 2) / (m * n)
        error = 1.0 - CCmax * np.conj(CCmax) / (rgzero * rfzero)
        error = np.sqrt(np.abs(error))
        diffphase = np.arctan2(np.imag(CCmax), np.real(CCmax))
        md2 = np.fix(m / 2)
        nd2 = np.fix(n / 2)
        if rloc > md2:
            row_shift = rloc - m
        else:
            row_shift = rloc

        if cloc > nd2:
            col_shift = cloc - n
        else:
            col_shift = cloc

        ndim = np.shape(buf2ft)
        nr = int(round(ndim[0]))
        nc = int(round(ndim[1]))
        Nr = sf.ifftshift(np.arange(-np.fix(1.0 * nr / 2), np.ceil(1.0 * nr / 2)))
        Nc = sf.ifftshift(np.arange(-np.fix(1.0 * nc / 2), np.ceil(1.0 * nc / 2)))
        Nc, Nr = np.meshgrid(Nc, Nr)
        Greg = buf2ft * np.exp(
            1j * 2 * np.pi * (-1.0 * row_shift * Nr / nr - 1.0 * col_shift * Nc / nc)
        )
        Greg = Greg * np.exp(1j * diffphase)
        image_reg = sf.ifft2(Greg) * np.sqrt(nr * nc)

        # return error,diffphase,row_shift,col_shift
        return error, diffphase, row_shift, col_shift, image_reg

    # Partial-pixel shift
    else:

        # First upsample by a factor of 2 to obtain initial estimate
        # Embed Fourier data in a 2x larger array
        ndim = np.shape(buf1ft)
        m = int(round(ndim[0]))
        n = int(round(ndim[1]))
        mlarge = m * 2
        nlarge = n * 2
        CC = np.zeros([mlarge, nlarge], dtype=np.complex128)

        CC[
            int(m - np.fix(m / 2)) : int(m + 1 + np.fix((m - 1) / 2)),
            int(n - np.fix(n / 2)) : int(n + 1 + np.fix((n - 1) / 2)),
        ] = (sf.fftshift(buf1ft) * np.conj(sf.fftshift(buf2ft)))[:, :]

        # Compute crosscorrelation and locate the peak
        CC = sf.ifft2(sf.ifftshift(CC))  # Calculate cross-correlation
        max1, loc1 = idxmax(np.abs(CC))

        rloc = int(round(loc1[0]))
        cloc = int(round(loc1[1]))
        CCmax = CC[rloc, cloc]

        # Obtain shift in original pixel grid from the position of the
        # crosscorrelation peak
        ndim = np.shape(CC)
        m = ndim[0]
        n = ndim[1]

        md2 = np.fix(m / 2)
        nd2 = np.fix(n / 2)
        if rloc > md2:
            row_shift = rloc - m
        else:
            row_shift = rloc

        if cloc > nd2:
            col_shift = cloc - n
        else:
            col_shift = cloc

        row_shift = row_shift / 2
        col_shift = col_shift / 2

        # If upsampling > 2, then refine estimate with matrix multiply DFT
        if usfac > 2:
            ### DFT computation ###
            # Initial shift estimate in upsampled grid
            row_shift = 1.0 * np.round(row_shift * usfac) / usfac
            col_shift = 1.0 * np.round(col_shift * usfac) / usfac
            dftshift = np.fix(np.ceil(usfac * 1.5) / 2)
            ## Center of output array at dftshift+1
            # Matrix multiply DFT around the current shift estimate
            CC = np.conj(
                dftups(
                    buf2ft * np.conj(buf1ft),
                    np.ceil(usfac * 1.5),
                    np.ceil(usfac * 1.5),
                    usfac,
                    dftshift - row_shift * usfac,
                    dftshift - col_shift * usfac,
                )
            ) / (md2 * nd2 * usfac**2)
            # Locate maximum and map back to original pixel grid
            max1, loc1 = idxmax(np.abs(CC))
            rloc = int(round(loc1[0]))
            cloc = int(round(loc1[1]))

            CCmax = CC[rloc, cloc]
            rg00 = dftups(buf1ft * np.conj(buf1ft), 1, 1, usfac) / (
                md2 * nd2 * usfac**2
            )
            rf00 = dftups(buf2ft * np.conj(buf2ft), 1, 1, usfac) / (
                md2 * nd2 * usfac**2
            )
            rloc = rloc - dftshift
            cloc = cloc - dftshift
            row_shift = 1.0 * row_shift + 1.0 * rloc / usfac
            col_shift = 1.0 * col_shift + 1.0 * cloc / usfac

        # If upsampling = 2, no additional pixel shift refinement
        else:
            rg00 = np.sum(buf1ft * np.conj(buf1ft)) / m / n
            rf00 = np.sum(buf2ft * np.conj(buf2ft)) / m / n

        error = 1.0 - CCmax * np.conj(CCmax) / (rg00 * rf00)
        error = np.sqrt(np.abs(error))
        diffphase = np.arctan2(np.imag(CCmax), np.real(CCmax))
        # If its only one row or column the shift along that dimension has no
        # effect. We set to zero.
        if md2 == 1:
            row_shift = 0

        if nd2 == 1:
            col_shift = 0

        # Compute registered version of buf2ft
        if usfac > 0:
            ndim = np.shape(buf2ft)
            nr = ndim[0]
            nc = ndim[1]
            Nr = sf.ifftshift(np.arange(-np.fix(1.0 * nr / 2), np.ceil(1.0 * nr / 2)))
            Nc = sf.ifftshift(np.arange(-np.fix(1.0 * nc / 2), np.ceil(1.0 * nc / 2)))
            Nc, Nr = np.meshgrid(Nc, Nr)
            Greg = buf2ft * np.exp(
                1j
                * 2
                * np.pi
                * (-1.0 * row_shift * Nr / nr - 1.0 * col_shift * Nc / nc)
            )
            Greg = Greg * np.exp(1j * diffphase)
        elif (nargout > 1) & (usfac == 0):
            Greg = np.dot(buf2ft, exp(1j * diffphase))

        # mplp.figure(3)
        image_reg = sf.ifft2(Greg) * np.sqrt(nr * nc)
        # imgplot = mplp.imshow(np.abs(image_reg))

        # a_ini = np.zeros((100,100))
        # a_ini[40:59,40:59] = 1.
        # a = a_ini * np.exp(1j*15.)
        # mplp.figure(6)
        # imgplot = mplp.imshow(np.abs(a))
        # mplp.figure(3)
        # imgplot = mplp.imshow(np.abs(a)-np.abs(image_reg))
        # mplp.colorbar()

        # return error,diffphase,row_shift,col_shift,Greg
        return error, diffphase, row_shift, col_shift, image_reg


def dftups(inp, nor, noc, usfac=1, roff=0, coff=0):
    """
           # function out=dftups(in,nor,noc,usfac,roff,coff);
           # Upsampled DFT by matrix multiplies, can compute an upsampled
    DFT in just
           # a small region.
           # usfac         Upsampling factor (default usfac = 1)
           # [nor,noc]     Number of pixels in the output upsampled DFT, in
           #               units of upsampled pixels (default = size(in))
           # roff, coff    Row and column offsets, allow to shift the
    output array to
           #               a region of interest on the DFT (default = 0)
           # Recieves DC in upper left corner, image center must be in (1,1)
           # Manuel Guizar - Dec 13, 2007
           # Modified from dftus, by J.R. Fienup 7/31/06

           # This code is intended to provide the same result as if the following
           # operations were performed
           #   - Embed the array "in" in an array that is usfac times larger in each
           #     dimension. ifftshift to bring the center of the image to (1,1).
           #   - Take the FFT of the larger array
           #   - Extract an [nor, noc] region of the result. Starting with the
           #     [roff+1 coff+1] element.

           # It achieves this result by computing the DFT in the output
    array without
           # the need to zeropad. Much faster and memory efficient than the
           # zero-padded FFT approach if [nor noc] are much smaller than
    [nr*usfac nc*usfac]
    """

    ndim = np.shape(inp)
    nr = int(round(ndim[0]))
    nc = int(round(ndim[1]))
    noc = int(round(noc))
    nor = int(round(nor))

    # Compute kernels and obtain DFT by matrix products
    a = np.zeros([nc, 1])
    a[:, 0] = ((sf.ifftshift(np.arange(nc))) - np.floor(1.0 * nc / 2))[:]
    b = np.zeros([1, noc])
    b[0, :] = (np.arange(noc) - coff)[:]
    kernc = np.exp((-1j * 2 * np.pi / (nc * usfac)) * np.dot(a, b))
    nndim = kernc.shape
    # print nndim

    a = np.zeros([nor, 1])
    a[:, 0] = (np.arange(nor) - roff)[:]
    b = np.zeros([1, nr])
    b[0, :] = (sf.ifftshift(np.arange(nr)) - np.floor(1.0 * nr / 2))[:]
    kernr = np.exp((-1j * 2 * np.pi / (nr * usfac)) * np.dot(a, b))
    nndim = kernr.shape
    # print nndim

    return np.dot(np.dot(kernr, inp), kernc)

def idxmax(data):
    ndim = np.shape(data)
    # maxd = np.max(data)
    maxd = np.max(np.abs(data))
    # t1 = mplp.mlab.find(np.abs(data) == maxd)
    t1 = np.argmin(np.abs(np.abs(data) - maxd))
    idx = np.zeros(
        [
            len(ndim),
        ]
    )
    for ii in range(len(ndim) - 1):
        t1, t2 = np.modf(1.0 * t1 / np.prod(ndim[(ii + 1) :]))
        idx[ii] = t2
        t1 *= np.prod(ndim[(ii + 1) :])
    idx[np.size(ndim) - 1] = t1

    return maxd, idx


def flip_conj(tmp):
    # ndims = np.shape(tmp)
    # nx = ndims[0]
    # ny = ndims[1]
    # nz = ndims[2]
    # tmp_twin = np.zeros([nx,ny,nz]).astype(complex)
    # for i in range(0,nx):
    #   for j in range(0,ny):
    #      for k in range(0,nz):
    #         i_tmp = nx - 1 - i
    #         j_tmp = ny - 1 - j
    #         k_tmp = nz - 1 - k
    #         tmp_twin[i,j,k] = tmp[i_tmp,j_tmp,k_tmp].conj()
    # return tmp_twin

    tmp_fft = sf.ifftshift(sf.ifftn(sf.fftshift(tmp)))
    return sf.ifftshift(sf.fftn(sf.fftshift(np.conj(tmp_fft))))


def check_conj(ref, tmp, threshold_flag, threshold, subpixel_flag):
    ndims = np.shape(ref)
    nx = ndims[0]
    ny = ndims[1]
    nz = ndims[2]

    if threshold_flag == 1:
        ref_tmp = np.zeros((nx, ny, nz))
        index = np.where(np.abs(ref) >= threshold * np.max(np.abs(ref)))
        ref_tmp[index] = 1.0
        tmp_tmp = np.zeros((nx, ny, nz))
        index = np.where(np.abs(tmp) >= threshold * np.max(np.abs(tmp)))
        tmp_tmp[index] = 1.0
        tmp_conj = flip_conj(tmp_tmp)
    else:
        ref_tmp = ref
        tmp_tmp = tmp
        tmp_conj = flip_conj(tmp)

    tmp_tmp = subpixel_align(ref_tmp, tmp_tmp, threshold_flag, threshold, subpixel_flag)
    tmp_conj = subpixel_align(
        ref_tmp, tmp_conj, threshold_flag, threshold, subpixel_flag
    )

    cc_1 = sf.ifftn(ref_tmp * np.conj(tmp_tmp))
    cc1 = np.max(cc_1.real)
    # cc1 = np.max(np.abs(cc_1))
    cc_2 = sf.ifftn(ref_tmp * np.conj(tmp_conj))
    cc2 = np.max(cc_2.real)
    # cc2 = np.max(np.abs(cc_2))
    print("{0}, {1}".format(cc1, cc2))
    if cc1 > cc2:
        return 0
    else:
        return 1


def subpixel_align(ref, tmp, threshold_flag, threshold, subpixel_flag):
    ndims = np.shape(ref)
    if np.size(ndims) == 3:
        nx = ndims[0]
        ny = ndims[1]
        nz = ndims[2]

        if threshold_flag == 1:
            ref_tmp = np.zeros((nx, ny, nz))
            index = np.where(np.abs(ref) >= threshold * np.max(np.abs(ref)))
            ref_tmp[index] = 1.0
            tmp_tmp = np.zeros((nx, ny, nz))
            index = np.where(np.abs(tmp) >= threshold * np.max(np.abs(tmp)))
            tmp_tmp[index] = 1.0
            ref_fft = sf.ifftn(sf.fftshift(ref_tmp))
            tmp_fft = sf.ifftn(sf.fftshift(tmp_tmp))
            real_fft = sf.ifftn(sf.fftshift(tmp))
        else:
            ref_fft = sf.ifftn(sf.fftshift(ref))
            tmp_fft = sf.ifftn(sf.fftshift(tmp))

        nest = np.mgrid[0:nx, 0:ny, 0:nz]

        result = dftregistration(ref_fft[:, :, 0], tmp_fft[:, :, 0], usfac=100)
        e, p, cl, r, array_shift = result
        x_shift_1 = cl
        y_shift_1 = r
        result = dftregistration(
            ref_fft[:, :, nz - 1], tmp_fft[:, :, nz - 1], usfac=100
        )
        e, p, cl, r, array_shift = result
        x_shift_2 = cl
        y_shift_2 = r

        result = dftregistration(ref_fft[:, 0, :], tmp_fft[:, 0, :], usfac=100)
        e, p, cl, r, array_shift = result
        x_shift_3 = cl
        z_shift_1 = r
        result = dftregistration(
            ref_fft[:, ny - 1, :], tmp_fft[:, ny - 1, :], usfac=100
        )
        e, p, cl, r, array_shift = result
        x_shift_4 = cl
        z_shift_2 = r

        result = dftregistration(ref_fft[0, :, :], tmp_fft[0, :, :], usfac=100)
        e, p, cl, r, array_shift = result
        y_shift_3 = cl
        z_shift_3 = r
        result = dftregistration(
            ref_fft[nx - 1, :, :], tmp_fft[nx - 1, :, :], usfac=100
        )
        e, p, cl, r, array_shift = result
        y_shift_4 = cl
        z_shift_4 = r

        if subpixel_flag == 1:
            x_shift = (x_shift_1 + x_shift_2 + x_shift_3 + x_shift_4) / 4.0
            y_shift = (y_shift_1 + y_shift_2 + y_shift_3 + y_shift_4) / 4.0
            z_shift = (z_shift_1 + z_shift_2 + z_shift_3 + z_shift_4) / 4.0
        else:
            x_shift = np.floor(
                (x_shift_1 + x_shift_2 + x_shift_3 + x_shift_4) / 4.0 + 0.5
            )
            y_shift = np.floor(
                (y_shift_1 + y_shift_2 + y_shift_3 + y_shift_4) / 4.0 + 0.5
            )
            z_shift = np.floor(
                (z_shift_1 + z_shift_2 + z_shift_3 + z_shift_4) / 4.0 + 0.5
            )

        print("x, y, z shift: {0}, {1}, {2}".format(x_shift, y_shift, z_shift))

        if threshold_flag == 1:
            tmp_fft_new = sf.ifftshift(real_fft) * np.exp(
                1j
                * 2
                * np.pi
                * (
                    -1.0 * x_shift * (nest[0, :, :, :] - nx / 2.0) / (nx)
                    - y_shift * (nest[1, :, :, :] - ny / 2.0) / (ny)
                    - z_shift * (nest[2, :, :, :] - nz / 2.0) / (nz)
                )
            )
        else:
            tmp_fft_new = sf.ifftshift(tmp_fft) * np.exp(
                1j
                * 2
                * np.pi
                * (
                    -1.0 * x_shift * (nest[0, :, :, :] - nx / 2.0) / (nx)
                    - y_shift * (nest[1, :, :, :] - ny / 2.0) / (ny)
                    - z_shift * (nest[2, :, :, :] - nz / 2.0) / (nz)
                )
            )

    if np.size(ndims) == 2:
        nx = ndims[0]
        ny = ndims[1]

        if threshold_flag == 1:
            ref_tmp = np.zeros((nx, ny))
            index = np.where(np.abs(ref) >= threshold * np.max(np.abs(ref)))
            ref_tmp[index] = 1.0
            tmp_tmp = np.zeros((nx, ny))
            index = np.where(np.abs(tmp) >= threshold * np.max(np.abs(tmp)))
            tmp_tmp[index] = 1.0

            ref_fft = sf.ifftn(sf.fftshift(ref_tmp))
            mp_fft = sf.ifftn(sf.fftshift(tmp_tmp))
            real_fft = sf.ifftn(sf.fftshift(tmp))
        else:
            ref_fft = sf.ifftn(sf.fftshift(ref))
            tmp_fft = sf.ifftn(sf.fftshift(tmp))

        nest = np.mgrid[0:nx, 0:ny]

        result = dftregistration(ref_fft[:, :], tmp_fft[:, :], usfac=100)
        e, p, cl, r, array_shift = result
        x_shift = cl
        y_shift = r

        if subpixel_flag == 1:
            x_shift = x_shift
            y_shift = y_shift
        else:
            x_shift = np.floor(x_shift + 0.5)
            y_shift = np.floor(y_shift + 0.5)

        print("x, y shift: {0}, {1}".format(x_shift, y_shift))

        if threshold_flag == 1:
            tmp_fft_new = sf.ifftshift(real_fft) * np.exp(
                1j
                * 2
                * np.pi
                * (
                    -1.0 * x_shift * (nest[0, :, :] - nx / 2.0) / (nx)
                    - y_shift * (nest[1, :, :] - ny / 2.0) / (ny)
                )
            )
        else:
            tmp_fft_new = sf.ifftshift(tmp_fft) * np.exp(
                1j
                * 2
                * np.pi
                * (
                    -1.0 * x_shift * (nest[0, :, :] - nx / 2.0) / (nx)
                    - y_shift * (nest[1, :, :] - ny / 2.0) / (ny)
                )
            )

    return sf.ifftshift(sf.fftn(sf.fftshift(tmp_fft_new))), x_shift, y_shift


def remove_phase_ramp(tmp, threshold_flag, threshold, subpixel_flag):
    tmp_tmp, x_shift, y_shift = subpixel_align(
        sf.ifftshift(sf.ifftn(sf.fftshift(np.abs(tmp)))),
        sf.ifftshift(sf.ifftn(sf.fftshift(tmp))),
        threshold_flag,
        threshold,
        subpixel_flag,
    )
    tmp_new = sf.ifftshift(sf.fftn(sf.fftshift(tmp_tmp)))
    phase_tmp = np.angle(tmp_new)
    ph_offset = np.mean(phase_tmp[np.where(np.abs(tmp) >= threshold)])
    phase_tmp = np.angle(tmp_new) - ph_offset
    return np.abs(tmp) * np.exp(1j * phase_tmp)


def pixel_shift(array, x_shift, y_shift, z_shift):
    nx, ny, nz = np.shape(array)
    tmp = sf.ifftshift(sf.ifftn(sf.fftshift(array)))
    nest = np.mgrid[0:nx, 0:ny, 0:nz]
    tmp = tmp * np.exp(
        1j
        * 2
        * np.pi
        * (
            -1.0 * x_shift * (nest[0, :, :, :] - nx / 2.0) / (nx)
            - y_shift * (nest[1, :, :, :] - ny / 2.0) / (ny)
            - z_shift * (nest[2, :, :, :] - nz / 2.0) / (nz)
        )
    )
    return sf.ifftshift(sf.fftn(sf.fftshift(tmp)))


def pixel_shift_2d(array, x_shift, y_shift):
    nx, ny = np.shape(array)
    tmp = sf.ifftshift(sf.ifftn(sf.fftshift(array)))
    nest = np.mgrid[0:nx, 0:ny]
    tmp = tmp * np.exp(
        1j
        * 2
        * np.pi
        * (
            -1.0 * x_shift * (nest[0, :, :] - nx / 2.0) / (nx)
            - y_shift * (nest[1, :, :] - ny / 2.0) / (ny)
        )
    )
    return sf.ifftshift(sf.fftn(sf.fftshift(tmp)))
