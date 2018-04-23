# !/usr/bin/env python
# coding=utf-8

from __future__ import print_function
from . import tools
from . import decision_tree
import ee

import ee.data
if not ee.data._initialized: ee.Initialize()

def compute(image, mask_band, bits, options=None, name_all='all_masks'):
    """ Compute bits using a specified band, a bit's relation and a list of
    options

    :param image: the image that holds the bit mask band
    :type image: ee.Image
    :param mask_band: the name of the band that holds the bits mask
    :type mask_band: str
    :param bits: relation between name and bit
    :type bits: dict
    :param options: list of 'bits' to compute. Example: ['cloud', 'snow']. If
        None, will use all keys of the relation's dict
    :type options: list
    :param name_all: name for the band that holds the final mask. Default:
        'all_masks'
    :type name_all: str
    :return: The computed mask
    :rtype: ee.Image
    """
    # cast params in case they are not EE objects
    bits_dict = ee.Dictionary(bits)
    opt = ee.List(options) if options else bits_dict.keys()
    image = ee.Image(image).select(mask_band)

    first = ee.Image.constant(0).select([0], [name_all]) # init image

    # function for iterate over the options
    def for_iterate(option, ini):
        i = ee.Image(ini) # cast ini
        all = i.select([name_all])

        # bits relation dict contains the option?
        cond = bits_dict.contains(option)

        def for_true():
            ''' function to execute if condition == True '''
            # get the mask for the option
            mask = tools.compute_bits(bits_dict.get(option),
                                      bits_dict.get(option),
                                      option)(image)

            # name the mask
            # mask = ee.Image(mask).select([0], [option])
            newmask = all.Or(mask)

            # return ee.Image(all.Or(mask)).addBands(mask)
            return tools.replace(i, name_all, newmask).addBands(mask)

        return ee.Image(ee.Algorithms.If(cond, for_true(), i))

    good_pix = ee.Image(opt.iterate(for_iterate, first))

    # return good_pix.Not()
    return good_pix

### DEPRECATED FUNCTIONS ###
# GENERIC APPLICATION OF MASKS
def apply_masks(masks):
    """
    Get a single mask from many

    :param masks: list of ee.Image
    :type masks: list | ee.List
    :return: the resulting mask
    :rtype: ee.Image
    """
    masks = ee.List(masks) if isinstance(masks, list) else masks
    first = ee.Image.constant(0)

    def compute(mask, first):
        first = ee.Image(first)
        return first.Or(mask)

    bad_pixels = ee.Image(masks.iterate(compute, first))
    good_pixels = bad_pixels.Not()

    return good_pixels

# MODIS
def modis_(img):
    """ DEPRECATED

    Function to use in MODIS Collection

    Use:

    `masked = collection.map(cloud_mask.modis)`
    """
    cmask = img.select("state_1km")
    cloud = tools.compute_bits_client(cmask, 0, 0, "cloud")
    mix = tools.compute_bits_client(cmask, 1, 1, "mix")
    shadow = tools.compute_bits_client(cmask, 2, 2, "shadow")
    cloud2 = tools.compute_bits_client(cmask, 10, 10, "cloud2")
    snow = tools.compute_bits_client(cmask, 12, 12, "snow")

    mask = (cloud
            .Or(mix)
            # .Or(shadow)  # Cloud shadow seems to be miscomputed (MODIS/MYD09GA/MYD09GA_005_2015_09_18)
            .Or(cloud2)
            .Or(snow)
            )

    return img.updateMask(mask.Not())

# SENTINEL 2
def sentinel2_(image):
    """ DEPRECATED

    Function to use in SENTINEL2 Collection

    Use:
    `masked = collection.map(cloud_mask.sentinel2)`
    """
    nubes = image.select("QA60")
    opaque = tools.compute_bits_client(nubes, 10, 10, "opaque")
    cirrus = tools.compute_bits_client(nubes, 11, 11, "cirrus")
    mask = opaque.Or(cirrus)
    result = image.updateMask(mask.Not())
    return result

# FMASK
def fmask(bandname="fmask"):
    """ DEPRECATED

    Function to use in Collections that have a quality band computed with
    fmask algorithm

    The use of this function is a little different from the other because it
    is a function that returns a function, so you must call it to return the
    function to use in map:

    `masked = collection.map(cloud_mask.fmask())`

    :param bandname: name of the band that holds the fmask information
    :type bandname: str
    :return: a function to use in map
    :rtype: function
    """

    def fmask(image):
        imgFmask = image.select(bandname)
        shadow = imgFmask.eq(3)
        snow = imgFmask.eq(4)
        cloud = imgFmask.eq(5)

        mask = shadow.Or(snow).Or(cloud)

        imgMask = image.updateMask(mask.Not())
        return imgMask
    return fmask

def usgs(image):
    """ DEPRECATED

    Function to use in Surface Reflectance Collections computed by USGS

    Use:

    `masked = collection.map(cloud_mask.usgs)`
    """
    image = fmask("cfmask")(image)
    cloud = image.select("sr_cloud_qa").neq(255)
    shad = image.select("sr_cloud_shadow_qa").neq(255)
    return image.updateMask(cloud).updateMask(shad)

def cfmask_bits(image):
    """ DEPRECATED

    Function to use in Landsat Surface Reflectance Collections:
    LANDSAT/LT04/C01/T1_SR, LANDSAT/LT05/C01/T1_SR, LANDSAT/LE07/C01/T1_SR,
    LANDSAT/LC08/C01/T1_SR

    Use:

    `masked = collection.map(cloud_mask.cfmask_bits)`
    """
    bands = image.bandNames()
    contains_sr = bands.contains('sr_cloud_qa')

    def sr():
        mask = image.select('sr_cloud_qa')
        cloud_mask = tools.compute_bits(mask, 1, 1, 'cloud')
        shadow_mask = tools.compute_bits(mask, 2, 2, 'shadow')
        adjacent_mask = tools.compute_bits(mask, 3, 3, 'adjacent')
        snow_mask = tools.compute_bits(mask, 4, 4, 'snow')

        good_pix = cloud_mask.eq(0).And(shadow_mask.eq(0)).And(snow_mask.eq(0)).And(adjacent_mask.eq(0))
        return good_pix

    def pix():
        mask = image.select('pixel_qa')
        cloud_mask = tools.compute_bits(mask, 5, 5, 'cloud')
        shadow_mask = tools.compute_bits(mask, 3, 3, 'shadow')
        snow_mask = tools.compute_bits(mask, 4, 4, 'snow')

        good_pix = cloud_mask.eq(0).And(shadow_mask.eq(0)).And(snow_mask.eq(0))
        return good_pix

    good_pix = ee.Algorithms.If(contains_sr, sr(), pix())

    result = image.updateMask(good_pix)

    return result

def landsatTOA_(masks=['cloud', 'shadow', 'snow']):
    ''' DEPRECATED

    Function to mask out clouds, shadows and snow in Landsat 4 5 7 8 TOA:
    LANDSAT/LT04/C01/T1_TOA, LANDSAT/LT05/C01/T1_TOA, LANDSAT/LE07/C01/T1_TOA
    and LANDSAT/LC08/C01/T1_TOA

    :param masks: list of mask to compute
    :type masks: list
    :return: the funtion to apply in a map algorithm
    :rtype: function
    '''
    options = ee.List(masks)

    def wrap(img):
        mask = img.select('BQA')
        cloud_mask = tools.compute_bits_client(mask, 4, 4, 'cloud')
        shadow_mask = tools.compute_bits_client(mask, 8, 8, 'shadow')
        snow_mask = tools.compute_bits_client(mask, 10, 10, 'snow')

        relation = ee.Dictionary({
            'cloud': cloud_mask,
            'shadow': shadow_mask,
            'snow': snow_mask
        })

        masks_list = tools.get_from_dict(options, relation)  # make a list of masks
        good_pix = apply_masks(masks_list)

        return img.updateMask(good_pix)

    return wrap
#############################

def modis(options=['cloud', 'mix', 'shadow', 'cloud2', 'snow'], name='modis_mask',
          addBands=False, updateMask=True):
    bits = {
        'cloud': 0,
        'mix': 1,
        'shadow': 2,
        'cloud2':10,
        'snow':12}

    mask_band = 'state_1km'

    options = ee.List(options)
    def wrap(image):
        good_pix = compute(image, mask_band, bits, options, name_all=name)

        mask = good_pix.select([name]).Not()

        if addBands and updateMask:
            return image.updateMask(mask).addBands(good_pix)
        elif addBands:
            return image.addBands(good_pix)
        elif updateMask:
            return image.updateMask(mask)
        else:
            return image

    return wrap

def sentinel2(options=['opaque', 'cirrus'], name='esa_mask',
              addBands=False, updateMask=True):
    """ ESA Cloud cover assessment

    :param options: category to mask out. Can be: 'opaque' or/and 'cirrus'
    :type options: list
    :return: the function to mask out clouds
    """

    rel = {'opaque': 10, 'cirrus':11}
    band = 'QA60'

    def wrap(img):
        good_pix = compute(img, band, rel, options, name_all=name)
        mask = good_pix.select([name]).Not()

        if addBands and updateMask:
            return img.updateMask(mask).addBands(good_pix)
        elif addBands:
            return img.addBands(good_pix)
        elif updateMask:
            return img.updateMask(mask)
        else:
            return img

    return wrap

# LEDAPS
def ledaps(image):
    """ Function to use in Surface Reflectance Collections computed by
    LEDAPS

    Use:

    `masked = collection.map(cloud_mask.ledaps)`
    """
    cmask = image.select('QA')

    valid_data_mask = tools.compute_bits(cmask, 1, 1, 'valid_data')
    cloud_mask = tools.compute_bits(cmask, 2, 2, 'cloud')
    snow_mask = tools.compute_bits(cmask, 4, 4, 'snow')

    good_pix = cloud_mask.eq(0).And(valid_data_mask.eq(0)).And(snow_mask.eq(0))
    result = image.updateMask(good_pix)

    return result

def landsatSR(options=['cloud', 'shadow', 'adjacent', 'snow'], name='sr_mask',
              addBands=False, updateMask=True):
    """ Function to use in Landsat Surface Reflectance Collections:
    LANDSAT/LT04/C01/T1_SR, LANDSAT/LT05/C01/T1_SR, LANDSAT/LE07/C01/T1_SR,
    LANDSAT/LC08/C01/T1_SR

    :param options: masks to apply. Options: 'cloud', 'shadow', 'adjacent',
        'snow'
    :type options: list
    :param name: name of the band that will hold the final mask. Default: 'toa_mask'
    :type name: str
    :param addBands: add all bands to the image. Default: False
    :type addBands: bool
    :param updateMask: update the mask of the Image. Default: True
    :type updateMask: bool
    :return: a function for applying the mask
    :rtype: function
    """
    sr = {'bits': ee.Dictionary({'cloud': 1, 'shadow': 2, 'adjacent': 3, 'snow': 4}),
          'band': 'sr_cloud_qa'}

    pix = {'bits': ee.Dictionary({'cloud': 5, 'shadow': 3, 'snow': 4}),
           'band': 'pixel_qa'}

    # Parameters
    options = ee.List(options)

    def wrap(image):
        bands = image.bandNames()
        contains_sr = bands.contains('sr_cloud_qa')
        good_pix = ee.Image(ee.Algorithms.If(contains_sr,
                   compute(image, sr['band'], sr['bits'], options, name_all=name),
                   compute(image, pix['band'], pix['bits'], options, name_all=name)))

        mask = good_pix.select([name]).Not()

        if addBands and updateMask:
            return image.updateMask(mask).addBands(good_pix)
        elif addBands:
            return image.addBands(good_pix)
        elif updateMask:
            return image.updateMask(mask)
        else:
            return image

    return wrap

def landsatTOA(options=['cloud', 'shadow', 'snow'], name='toa_mask',
               addBands=False, updateMask=True):
    """ Function to mask out clouds, shadows and snow in Landsat 4 5 7 8 TOA:
    LANDSAT/LT04/C01/T1_TOA, LANDSAT/LT05/C01/T1_TOA, LANDSAT/LE07/C01/T1_TOA
    and LANDSAT/LC08/C01/T1_TOA

    :param options: masks to apply. Options: 'cloud', 'shadow', 'snow'
    :type options: list
    :param name: name of the band that will hold the final mask. Default: 'toa_mask'
    :type name: str
    :param addBands: add all bands to the image. Default: False
    :type addBands: bool
    :param updateMask: update the mask of the Image. Default: True
    :type updateMask: bool
    :return: a function for applying the mask
    :rtype: function
    """
    bits = ee.Dictionary({'cloud': 4, 'shadow': 8, 'snow': 10})
    mask_band = 'BQA'

    # Parameters
    opt = options if options else bits.keys()
    options = ee.List(opt)

    def wrap(image):
        good_pix = compute(image, mask_band, bits, options, name_all=name)

        mask = good_pix.select([name]).Not()

        if addBands and updateMask:
            return image.updateMask(mask).addBands(good_pix)
        elif addBands:
            return image.addBands(good_pix)
        elif updateMask:
            return image.updateMask(mask)
        else:
            return image

    return wrap

def hollstein_S2(options=['cloud', 'snow', 'shadow', 'water', 'cirrus'],
                 name='hollstein', addBands=False, updateMask=True):
    """

    :param options: masks to apply. Options: 'cloud', 'shadow', 'snow',
        'cirrus', 'water'
    :type options: list
    :param name: name of the band that will hold the final mask. Default: 'hollstein'
    :type name: str
    :param addBands: add all bands to the image. Default: False
    :type addBands: bool
    :param updateMask: update the mask of the Image. Default: True
    :type updateMask: bool
    :return: a function for applying the mask
    :rtype: function
    """

    def difference(a, b):
        def wrap(img):
            return img.select(a).subtract(img.select(b))
        return wrap

    def ratio(a, b):
        def wrap(img):
            return img.select(a).divide(img.select(b))
        return wrap

    def compute_dt(img):

        # 1
        b3 = img.select('B3').lt(3190)

        # 2
        b8a = img.select('B8A').lt(1660)
        r511 = ratio('B5', 'B11')(img).lt(4.33)

        # 3
        s1110 = difference('B11', 'B10')(img).lt(2550)
        b3_3 = img.select('B3').lt(5250)
        r210 = ratio('B2','B10')(img).lt(14.689)
        s37 = difference('B3', 'B7')(img).lt(270)

        # 4
        r15 = ratio('B1', 'B5')(img).lt(1.184)
        s67 = difference('B6', 'B7')(img).lt(-160)
        b1 = img.select('B1').lt(3000)
        r29 =  ratio('B2', 'B9')(img).lt(0.788)
        s911 = difference('B9', 'B11')(img).lt(210)
        s911_2 = difference('B9', 'B11')(img).lt(-970)

        snow = {'snow':[['1',0], ['22',0], ['34',0]]}
        cloud = {'cloud-1':[['1',0], ['22',1],['33',1],['44',1]],
                 'cloud-2':[['1',0], ['22',1],['33',0],['45',0]]}
        cirrus = {'cirrus-1':[['1',0], ['22',1],['33',1],['44',0]],
                  'cirrus-2':[['1',1], ['21',0],['32',1],['43',0]]}
        shadow = {'shadow-1':[['1',1], ['21',1],['31',1],['41',0]],
                  'shadow-2':[['1',1], ['21',1],['31',0],['42',0]],
                  'shadow-3':[['1',0], ['22',0],['34',1],['46',0]]}
        water = {'water':[['1',1], ['21',1],['31',0],['42',1]]}

        all = {'cloud':cloud,
               'snow': snow,
               'shadow':shadow,
               'water':water,
               'cirrus':cirrus}

        final = {}

        for option in options:
            final.update(all[option])

        dtf = decision_tree.binary(
                        {'1':b3,
                         '21':b8a, '22':r511,
                         '31':s37, '32':r210, '33':s1110, '34':b3_3,
                         '41': s911_2, '42':s911, '43':r29, '44':s67, '45':b1, '46':r15
                         }, final, name)

        results = dtf

        if updateMask and addBands:
            return img.addBands(results).updateMask(results.select(name))
        elif addBands:
            return img.addBands(results)
        elif updateMask:
            return img.updateMask(results.select(name))

    return compute_dt