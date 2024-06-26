import statmorph

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from astropy.visualization import simple_norm
from astropy.modeling.models import Sersic2D
from astropy.convolution import convolve, Gaussian2DKernel
import time

#### imports for making galaxy img cutouts
import astropy.units as units
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.table import Table, Column, join
from astropy.nddata import Cutout2D
from astropy.io import fits,ascii
from astropy.stats import sigma_clipped_stats
import warnings

from import_data import get_GS,get_GN,get_sources

### imports for making the segmentation map (if need be)
from photutils.segmentation import detect_threshold, detect_sources, deblend_sources
from photutils.background import Background2D, MedianBackground
from statmorph.utils.image_diagnostics import make_figure
from photutils.segmentation import make_2dgaussian_kernel
from astropy.stats import SigmaClip
#sigma_clipping = SigmaClip(sigma=sigma)

# for finding the psf
import webbpsf

from astropy.utils.exceptions import AstropyWarning
#warnings.simplefilter('ignore', category=AstropyWarning)
# following https://statmorph.readthedocs.io/en/latest/notebooks/tutorial.html
## to learn it


def test_in_jades():
    ###############################
    """
    Try to get statmorph fit for a jades source
    """
    ###############################
    ## making a sample image that is going to be analyzed (with sersic 2d)
    '''
    ny, nx = 240,240
    y,x = np.mgrid[0:ny, 0:nx]
    sersic = Sersic2D(amplitude=1, r_eff=20, n=2.5, x_0=120.5, y_0=96.5, ellip=0.5, theta=0.5)

    image = sersic(x,y)
    #plt.imshow(image, cmap='gray', origin='lower', norm=simple_norm(image,stretch='log',log_a=10000))
    #plt.show()

    ### now make a sample PSF (these are only used for parametric fitting, and we can use WebbPSF to generate one if needed)

    kernel = Gaussian2DKernel(2)
    kernel.normalize()
    psf = kernel.array
    #plt.imshow(psf,origin='lower',cmap='gray')
    #plt.show()


    ### now combine the image with the PSF
    image = convolve(image, psf)
    #plt.imshow(image, origin='lower',norm=simple_norm(image,stretch='log',log_a=10000))
    #plt.show()

    ### applying noise
    np.random.seed(3)
    gain = 1e5
    image = np.random.poisson(image*gain)/gain
    snp = 100.0
    sky_sigma = 1.0/snp
    image+=sky_sigma * np.random.standard_normal(size=(ny,nx))
    #plt.imshow(image,origin='lower',cmap='gray',norm=simple_norm(image,stretch='log',log_a=10000))
    #plt.show()


    #########################################



    ##########################
    """
    Creating the segmentation map from the image
    Use libraries like SExtractor or photutils(use this one)
    """
    ##########################

    # count anything >1.5 sigma as a detection
    threshold = detect_threshold(image, 1.5)
    npixels = 5 # min number of connected pixels
    convolved_image = convolve(image,psf)
    segmap = detect_sources(convolved_image,threshold,npixels)
    #plt.imshow(segmap,origin='lower',cmap='gray')
    #plt.show()
    '''
    ## here value of 0 is the background, and 1 is for the labeled source
    # but statmorph can take in a variety of values for this

    ##########################

    """
    Actually running statmorph

    """
    ##########################

    '''
    start = time.time()
    source_morphs = statmorph.source_morphology(image,segmap, gain=5.8, psf=psf)
    print(f'Time: {time.time()-start}')
    morph = source_morphs[0]


    #### Getting properties from statmorph

    print('Basic measurements (non-parametric)')
    print(f'concentration \t(C): {morph.concentration} ')
    print(f'asymmetry \t(A): {morph.asymmetry} ')
    print(f'smoothness\t(S): {morph.smoothness} ')
    print(f'Gini/M20: {morph.gini}/{morph.m20}')
    print(f'S/N (per pixel): {morph.sn_per_pixel}')


    print('Parametric measurements (Sersic Model)')
    print(f'Sersic amplitude: {morph.sersic_amplitude}')
    print(f'Sersic rhalf: {morph.sersic_rhalf}')
    print(f'Sersic n: {morph.sersic_n}')


    #####################
    """
    Visualizing the fit
    """
    #####################
    #from statmorph.utils.image_diagnostics import make_figure

    #fig = make_figure(morph)

    ### this not working?? why?
    #fig.savefig('tutorial.png')
    #plt.close(fig)

    '''


    #####################################
    """
    Importing a JADES fits file for testing 
    """
    #####################################

    ### It looks like the CAS, Gini/M20 values are the same from statmorph
    ### regardless of gain and psf values
    ### only values to change under this change are SN and parameteric values like sersic


    ### importing fits files

    # starting with f444 because it should have the clearest source (maybe not clear detail though)
    #hdul = fits.open('JADES_Fits_Maps/hlsp_jades_jwst_nircam_goods-s-deep_f444w_v2.0_drz.fits')
    hdul = fits.open('/home/robbler/research/JADES_Fits_Maps/GS/hlsp_jades_jwst_nircam_goods-s-deep_f277w_v2.0_drz.fits')

    # catalog file
    tmp = fits.open('research/JADES catalog/hlsp_jades_jwst_nircam_goods-s-deep_photometry_v2.0_catalog.fits')

    # segmentation map
    jades_seg = fits.getdata('/home/robbler/research/JADES_Fits_Maps/GS/hlsp_jades_jwst_nircam_goods-s-deep_segmentation_v2.0_drz.fits')

    # generate PSF for current filter
    # nc = webbpsf.NIRCam()
    # nc.filter = 'F444W'
    # psf = nc.calc_psf(oversample=4,display=True)
    # print(psf)
    # exit()

    # .fits file (image version)
    sci = hdul[1].data # for getting the science image
    wcs_coords = WCS(hdul[1].header) # getting wcs from header
    #print(f'wcs_header_info: {hdul[1].header}')
    hdul.close()

    # catalog file
    jades_catalog = Table(tmp['FLAG'].data) # extension #2 "FLAG" data
    tmp.close()

    # maybe this is the weight value we're looking for for statmorph (one value for each entry, so how would I convert this to an image to be used with statmorph though?)
    #print(jades_catalog[3]['F444W_WHT'])


    ###################
    """
    Now take the cutout images for a specific galaxy (eventually all of them in a loop)
    """
    ###################
    

    sources = get_sources()
    
    # source_names, jades_names, source_coords = get_GS()
    # source_names = np.array(source_names)

    kirk_id = 'GS_IRS21' # look at a high agn spheroid-like source for testing
    # ind = np.where(source_names==kirk_id)[0][0]
    # detection radius ~ 1" for Kirkpatrick data, so we want anything within a ~3" box
    # maybe change this later to reflect the light distribution (20%, 80% radii)
    # size = 3
    
    # jades_id = jades_names[ind]
    # get jades id counterpart coordinates
    '''
    #source = jades_catalog[jades_catalog['ID']==jades_id]
    #print(source['ID'])
    position = SkyCoord(source_coords[ind,0],source_coords[ind,1],unit='deg')
    #position = SkyCoord(source['RA'],source['DEC'],unit='deg')
    img = Cutout2D(sci,position,size*units.arcsec,wcs=wcs_coords).data
    source_seg = Cutout2D(jades_seg,position,size*units.arcsec,wcs=wcs_coords).data
    #source_gain = source['F444W_WHT'] # this seems wrong, need to figure out weightmap issue
    source_gain = 100.
    morph = statmorph.source_morphology(img,source_seg,gain=source_gain)[0]

    ################# ^^^^^^^^^^^^^^^^ ###################
    ## the value of gain=source_gain might not be right, need to check with Alex or Sam to see if that's what I should be doing here...


    print(f'Values for JADES:{jades_id}')
    print(f'concentration \t(C): {morph.concentration} ')
    print(f'asymmetry \t(A): {morph.asymmetry} ')
    print(f'smoothness(clumpiness) \t(S): {morph.smoothness} ')
    print(f'Gini: {morph.gini}')
    print(f'M20: {morph.m20}')
    print(f'S/N (per pixel): {morph.sn_per_pixel}')
    print(f'Flag: {morph.flag}')


    # then maybe show the source to see
    fig = make_figure(morph)
    plt.show()
    '''    

    ### for testing with a specific ID
    search_one_id = np.array([kirk_id])
    for id in search_one_id:
    # for id in search_ids:
        data_source = sources[(sources['ID'].str.contains(id))]
        search_id = id
        # ind = np.where(source_names==id)[0][0]
        # jades_id = int(jades_names[ind])
        #hdul = fits.open('/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam10_f200w_dr0.6_i2d.fits.gz')
        # segmentation map
        # don't have the segmentation map available so need to use something like WebbPSF to find psf then create a segmentation map 
        # from this with anything that has a SNR of >2.5 (standard) or sigma of ??? 
        #seg = fits.getdata('/home/robbler/research/CEERS_statmorph_testing/ceers5_f200w_segm.fits.gz')
        # importing psf from testing fits file first (f444w)
        psf = fits.getdata('/home/robbler/research/JADES catalog/PSF_NIRCam_in_flight_opd_filter_F444W.fits')
        #sci = hdul[1].data # for getting the science image
        # wcs_coords = WCS(hdul[1].header) # getting wcs from header
        # hdul.close()
        size = 3.0 # cutout size in arcsec, might need to tweak depending on the source size
        jades_id = int(data_source['JADES ID'].values[0])
        source = jades_catalog[jades_catalog['ID']==jades_id] # make sure jades_id is an integer, otherwise it just returns the first item NOT AN ERROR??
        print(f'[---] Searching for ID: {search_id}')
        position = SkyCoord(source['RA'],source['DEC'],unit='deg')
        img = Cutout2D(sci,position,size*units.arcsec,wcs=wcs_coords,copy=True).data
        seg = Cutout2D(jades_seg,position,size*units.arcsec,wcs=wcs_coords,copy=True).data
        m = np.mean(img)
        s = np.std(img)
        sigma = 2.0 # detection threshold =1.5*sigma
        fwhm = 2.222
        # ^ as described in https://jwst-docs.stsci.edu/jwst-near-infrared-camera/nircam-performance/nircam-point-spread-functions#gsc.tab=0
        # fwhm = .145
        # making a 2d gaussian kernel with fwhm 3 pixels (Ren paper uses 0.2 Petrosian Radius)
        # then getting a sample of the background and using that as the threshold for detection 
        # instead of just sigma ##################
        npix = 10 # min pixels for connection
        # from astropy.stats import SigmaClip
        # sigma_clip = SigmaClip(sigma=3.5)
        bkg_estimator = MedianBackground()
        bkg = Background2D(img, (9,9), filter_size=(13,13), bkg_estimator=bkg_estimator)
        # bkg = Background2D(img,(20,20),filter_size=(9,9),bkg_estimator=bkg_estimator)
        img -= bkg.background  # subtract the background
        kernel = make_2dgaussian_kernel(fwhm, size=5)
        convolved_data = convolve(img, kernel)
        # convolved_image = convolve(img,psf[0:100][0:100])
        # convolved_image = convolve(img,psf)
        #threshold = detect_threshold(convolved_data,sigma)
        threshold = detect_threshold(img,sigma)
        #mean,_,std = sigma_clipped_stats(img)
        #threshold = sigma*std
        # make the segmentation map using the bg subtracted image, threshold, & number of required connected pixels
        segmap = detect_sources(convolved_data,threshold,npix)
        # then separate connected segmentation sources by deblending them
        deblended_segmap = deblend_sources(convolved_data,segmap,npixels=npix,nlevels=32,contrast=0.01)
        #segmap_final = convolve(deblended_segmap,seg)
        # deblended_segmap = seg # testing with no deblending
        # plt.imshow(segmap,origin='lower')
        # plt.show()
        # plt.imshow(deblended_segmap,origin='lower')
        # plt.show()

        # plt.imshow(img, origin='lower',norm=colors.PowerNorm(gamma=0.5,vmin=(m-s),vmax=(m+8*s)),cmap='gray_r')
        # plt.show()

        ## attempt to find the biggest segmap part, and fit that within the cutout
        areas = np.zeros([len(deblended_segmap.labels)])
        for i in deblended_segmap.labels:
            areas[i-1] = deblended_segmap.get_area(i)
        seg_id = np.where(areas==np.max(areas))[0][0]
        #################################################

        source_gain = source['F444W_WHT'] # this seems wrong, need to figure out weightmap issue
        # source_gain = 1e7 # used in example (apparently fairly high though)
        ### ^^^^ maybe useful later for all nircam data gain map
        ### https://jwst-pipeline.readthedocs.io/en/latest/jwst/gain_scale/description.html
        # morph_full = statmorph.source_morphology(img,deblended_segmap,gain=source_gain,psf=psf,cutout_extent=2,verbose=True) # maybe cutout_extent=1?
        print(f'Cutout size being inputted: {img.shape}')
        morph_full = statmorph.source_morphology(img,segmap,gain=source_gain,verbose=True) # maybe cutout_extent=1?
        morph = morph_full[seg_id]
        
        ###### ^ so it's fitting multiple of them depending on which label in the segmentation map it is ^^^^^^
        print(f'morph label (from segmap): {morph.label}, total # of morphs:{len(morph_full)}')
        ## https://github.com/vrodgom/statmorph/blob/master/docs/description.rst
        ################# ^^^^^^^^^^^^^^^^ ###################
        ## the value of gain=source_gain might not be right, need to check with Alex or Sam to see if that's what I should be doing here...
        '''
        stat_rows[c,0] = id #id
        stat_rows[c,1] = position # position (skycoord)
        stat_rows[c,2] = morph.flag # flag (error, 0=great, 1=ok, 2=bad)
        stat_rows[c,3] = morph.concentration # concentration
        stat_rows[c,4] = morph.asymmetry # asymmetry
        stat_rows[c,5] = morph.outer_asymmetry # outer asymmetry
        stat_rows[c,6] = morph.deviation # deviation (not sure if this is total or just outer?)
        stat_rows[c,7] = morph.smoothness # smoothness (clumpiness)
        stat_rows[c,8] = morph.gini # gini
        stat_rows[c,9] = morph.m20 # m20
        stat_rows[c,10] = morph.gini_m20_merger # gini/m20 for mergers
        stat_rows[c,11] = morph.sn_per_pixel # s/n ratio (per pixel?)
        stat_rows[c,12] = (f'({morph.xmax_stamp-morph.xmin_stamp},{morph.ymax_stamp-morph.ymin_stamp})') # size of cutout
        c+=1
        '''

        print(f'Kirk ID:{search_id}')
        print(f'JADES ID:{jades_id}')
        print(f'Source location: {position}')
        print(f'Flag: {morph.flag}')
        print(f'concentration \t(C): {morph.concentration} ')
        print(f'asymmetry (under-estimate) (A): {morph.asymmetry} ')
        print(f'outer asymmetry\t (A0): {morph.outer_asymmetry}')
        print(f'smoothness(depends on psf heavily) (S): {morph.smoothness} ')
        print(f'Gini: {morph.gini}')
        print(f'M20: {morph.m20}')
        print(f'Gini-M20 merger stat: {morph.gini_m20_merger}')
        print(f'S/N (per pixel): {morph.sn_per_pixel}')
        
        fig = make_figure(morph)
        plt.show()

##################
"""
::: NEXT STEPS ::::

Confirm this is working properly by looking at the values from other data(?)
Confirm we're getting all the values we want from this (ensure that we don't want reff or n or other parametric values)
Then run this for all sources in the sample
and find a way to save all this to a pandas database or maybe a astropy table
"""
##################

def test_in_ceers():
    '''test it in the ceers survey to reference results with this paper: https://arxiv.org/pdf/2404.16686'''
    #catalog_filename = '/home/robbler/research/CEERS_statmorph_testing/ceers5_f200w_cat.ecsv'
    catalog_filename = '/home/robbler/research/CEERS_statmorph_testing/hlsp_candels_hst_wfc3_egs_multi_v1_mass-cat.fits'
    table = Table()
    with fits.open(catalog_filename) as hdul:
        # this way it closes automatically when with: ends
        hdr = hdul[0].header
        flag_data = Table(hdul[1].data)
        table = flag_data['ID','RAdeg','DECdeg']
        search_ids = np.array([13447,21320,19427,6944,6611,31265,19511,13206,2705,14053,20998,918,31485,3747,11689,20248,11790,23584,23419,13219,16315,12403,2985])
        #search_id = 21320
        c=0

        ###############################################
        #### creating a table just to get practice ####
        ###############################################
        rows = np.zeros((len(search_ids),3))


        for i in search_ids:
            mask = table['ID']==i
            rows[c,1] = table[mask]['RAdeg']
            rows[c,0] = i
            rows[c,2] = table[mask]['DECdeg']
            c+=1


        table = Table(rows=rows, names=['id', 'ra','dec'])
        #make_circles(table,1.0)
        #exit()
        # data['dec'] = 
        
    

    #### now import the fits file and seg map for statmorph

    #hdul = fits.open('JADES_Fits_Maps/hlsp_jades_jwst_nircam_goods-s-deep_f444w_v2.0_drz.fits')
    #search_id = 6611

    search_ids = np.array([23419,21320,31265,31485,23584,13447,19511,13219,16315,11689,12403,11790,13206,19427,20248,20998,14053,6944,3747,2705,2985,6611,918])
    fits_loc = np.array([1,2,2,3,3,4,4,4,4,4,5,6,6,6,6,6,6,8,8,8,10,10,7])
    fits_dict = {
        1: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam1_f200w_v0.5_i2d.fits.gz",
        2: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam2_f200w_v0.5_i2d.fits.gz",
        3: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam3_f200w_v0.5_i2d.fits.gz",
        4: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam4_f200w_dr0.6_i2d.fits.gz",
        5: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam5_f200w_dr0.6_i2d.fits.gz",
        6: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam6_f200w_v0.5_i2d.fits.gz",
        7: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam7_f200w_dr0.6_i2d.fits.gz",
        8: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam8_f200w_dr0.6_i2d.fits.gz",
        9: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam9_f200w_dr0.6_i2d.fits.gz",
        10: "/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam10_f200w_dr0.6_i2d.fits.gz"
    }

    ##### run loop on all them ######
    statmorph_table = Table()
    stat_rows = np.zeros((len(search_ids),13),dtype=object)
    c=0

    ### for testing with a specific ID
    search_one_id = np.array([11689])
    for id in search_one_id:
    # for id in search_ids:
        search_id = id
        fits_path = fits_dict[fits_loc[np.where(search_ids == id)[0][0]]]
        hdul = fits.open(fits_path)
        #hdul = fits.open('/home/robbler/research/CEERS_statmorph_testing/hlsp_ceers_jwst_nircam_nircam10_f200w_dr0.6_i2d.fits.gz')
        # segmentation map
        # don't have the segmentation map available so need to use something like WebbPSF to find psf then create a segmentation map 
        # from this with anything that has a SNR of >2.5 (standard) or sigma of ??? 
        #seg = fits.getdata('/home/robbler/research/CEERS_statmorph_testing/ceers5_f200w_segm.fits.gz')
        # importing psf
        psf = fits.getdata('/home/robbler/research/CEERS_statmorph_testing/ceers-full-grizli-v6.0-f200w-clear_drc_sci.gz_psf.fits')
        sci = hdul[1].data # for getting the science image
        wcs_coords = WCS(hdul[1].header) # getting wcs from header
        hdul.close()
        size = 3.0 # cutout size in arcsec, might need to tweak depending on the source size
        mask = table['id']==search_id
        print(f'searching for id: {search_id}')
        position = SkyCoord(table[mask]['ra'],table[mask]['dec'],unit='deg')
        img = Cutout2D(sci,position,size*units.arcsec,wcs=wcs_coords,copy=True).data
        #source_seg = Cutout2D(seg,position,size*units.arcsec,wcs=wcs_coords,copy=True).data
        m = np.mean(img)
        s = np.std(img)
        sigma = 1.5
        fwhm = 10.0
        # making a 2d gaussian kernel with fwhm 3 pixels (Ren paper uses 0.2 Petrosian Radius)
        # then getting a sample of the background and using that as the threshold for detection 
        # instead of just sigma ##################
        npix = 5 # min pixels for connection
        #bkg_estimator = MedianBackground()
        # from astropy.stats import SigmaClip
        # sigma_clip = SigmaClip(sigma=3.5)
        #bkg = Background2D(img, (9,9), filter_size=(21,21), bkg_estimator=bkg_estimator)
        #img -= bkg.background  # subtract the background
        #kernel = make_2dgaussian_kernel(fwhm, size=5)
        #convolved_data = convolve(img, kernel)
        # convolved_image = convolve(convolved_data,psf)
        convolved_image = convolve(img,psf)
        #threshold = detect_threshold(convolved_image,sigma)
        from astropy.stats import sigma_clipped_stats
        mean,_,std = sigma_clipped_stats(img)
        threshold = sigma*std
        # make the segmentation map using the bg subtracted image, threshold, & number of required connected pixels
        segmap = detect_sources(convolved_image,threshold,npix)
        
        # then separate connected segmentation sources by deblending them
        deblended_segmap = deblend_sources(convolved_image, segmap,npixels=npix,nlevels=32,contrast=0.01)
        # deblended_segmap = segmap # testing with no deblending
        plt.imshow(deblended_segmap,origin='lower')
        plt.show()
        # plt.imshow(img, origin='lower',norm=colors.PowerNorm(gamma=0.5,vmin=(m-s),vmax=(m+8*s)),cmap='gray_r')
        # plt.show()

        ## attempt to find the biggest segmap part, and fit that within the cutout
        areas = np.zeros([len(deblended_segmap.labels)])
        for i in deblended_segmap.labels:
            areas[i-1] = deblended_segmap.get_area(i)
        seg_id = np.where(areas==np.max(areas))[0][0]
        #################################################

        #source_gain = source['F444W_WHT'] # this seems wrong, need to figure out weightmap issue
        source_gain = 1e5 # used in example (apparently fairly high though)
        ### ^^^^ maybe useful later for all nircam data gain map
        ### https://jwst-pipeline.readthedocs.io/en/latest/jwst/gain_scale/description.html
        print(f'Cutout size: {img.shape}')
        morph_full = statmorph.source_morphology(img,deblended_segmap,gain=source_gain,psf=psf,cutout_extent=1.5,verbose=True) # maybe cutout_extent=1?
        morph = morph_full[seg_id]
        
        ###### ^ so it's fitting multiple of them depending on which label in the segmentation map it is ^^^^^^
        print(f'morph label (from segmap): {morph.label}, total # of morphs:{len(morph_full)}')
        ## https://github.com/vrodgom/statmorph/blob/master/docs/description.rst
        ################# ^^^^^^^^^^^^^^^^ ###################
        ## the value of gain=source_gain might not be right, need to check with Alex or Sam to see if that's what I should be doing here...
        stat_rows[c,0] = id #id
        stat_rows[c,1] = position # position (skycoord)
        stat_rows[c,2] = morph.flag # flag (error, 0=great, 1=ok, 2=bad)
        stat_rows[c,3] = morph.concentration # concentration
        stat_rows[c,4] = morph.asymmetry # asymmetry
        stat_rows[c,5] = morph.outer_asymmetry # outer asymmetry
        stat_rows[c,6] = morph.deviation # deviation (not sure if this is total or just outer?)
        stat_rows[c,7] = morph.smoothness # smoothness (clumpiness)
        stat_rows[c,8] = morph.gini # gini
        stat_rows[c,9] = morph.m20 # m20
        stat_rows[c,10] = morph.gini_m20_merger # gini/m20 for mergers
        stat_rows[c,11] = morph.sn_per_pixel # s/n ratio (per pixel?)
        stat_rows[c,12] = (f'({morph.xmax_stamp-morph.xmin_stamp},{morph.ymax_stamp-morph.ymin_stamp})') # size of cutout
        c+=1

        '''
        print(f'Values for CANDELS(EGS):{search_id}')
        print(f'Source location: {position}')
        print(f'Flag (0=great,1=ok,2=bad): {morph.flag}')
        print(f'concentration \t(C): {morph.concentration} ')
        print(f'asymmetry (under-estimate) (A): {morph.asymmetry} ')
        print(f'outer asymmetry\t (A0): {morph.outer_asymmetry}')
        print(f'Deviation (not outer?) (D): {morph.deviation}')
        print(f'smoothness(depends on psf heavily) (S): {morph.smoothness} ')
        print(f'Gini: {morph.gini}')
        print(f'M20: {morph.m20}')
        print(f'Gini-M20 merger stat: {morph.gini_m20_merger}')
        print(f'S/N (per pixel): {morph.sn_per_pixel}')
        print(f'Size of sample cutout (WCS): ({morph.xmax_stamp-morph.xmin_stamp},{morph.ymax_stamp-morph.ymin_stamp})')
        '''
        
        fig = make_figure(morph)
        plt.show()
        # plt.savefig(f'/home/robbler/research/CEERS_statmorph_testing/statmorph_fits/{id}.png')
        # plt.close()
    statmorph_table = Table(rows=stat_rows, names=['id', 'position','flag','concentration (C)','asymmetry (A)','outer asymmetry (Ao)','deviation','smoothness','gini','m20','gini/m20 merger','s/n ratio','cutout size'])
    table_output = statmorph_table.to_pandas()
    table_output.to_csv("/home/robbler/research/CEERS_statmorph_testing/statmorph_measurements.csv", encoding='utf-8', index=False)



# test_in_ceers()
test_in_jades()





def make_circles(table,radius):
    '''function to make regions file given equal size ra,dec,label arrays with size radius.
        ra & dec can be in (") or (deg)
        radius in arcseconds(")'''
    c = 0
    print("""# Region file format: DS9 version 4.1
global color=cyan dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
fk5""")
    for i in table:
        label = i['id']
        ra = i['ra']
        dec = i['dec']
        print(f'circle({ra}, {dec}, {radius}")  # text={{{label}}}')
        c+=1
