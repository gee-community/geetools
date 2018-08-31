# !/usr/bin/env python
# coding=utf-8

from __future__ import print_function
from . import tools
from . import decision_tree
import ee
from . import __version__
from .bitreader import BitReader

import ee.data
if not ee.data._initialized: ee.Initialize()

# options for BitReaders for known collections

# 16 bits
BITS_MODIS09GA = {
    '0-1': {0:'clear', 1:'cloud', 2:'mix'},
    '2':   {1:'shadow'},
    '8-9': {1:'small_cirrus', 2:'average_cirrus', 3:'high_cirrus'},
    '13':  {1:'adjacent'},
    '15':  {1:'snow'}
}

# 16 bits
BITS_MODIS13Q1 = {
    '0-1': {0:'good_qa'},
    '2-5': {0:'highest_qa'},
    '8':   {1:'adjacent'},
    '10':  {1:'cloud'},
    '14':  {1:'snow'},
    '15':  {1:'shadow'}
}

# USGS SURFACE REFLECTANCE
# 8 bits
BITS_LANDSAT_CLOUD_QA = {
    '0': {1:'ddv'},
    '1': {1:'cloud'},
    '2': {1:'shadow'},
    '3': {1:'adjacent'},
    '4': {1:'snow'},
    '5': {1:'water'}
}

# USGS SURFACE REFLECTANCE
# 16 bits
BITS_LANDSAT_PIXEL_QA = {
    '1': {1:'clear'},
    '2': {1:'water'},
    '3': {1:'shadow'},
    '4': {1:'snow'},
    '5': {1:'cloud'},
    '6-7':{3:'high_confidence_cloud'}
}

# USGS SURFACE REFLECTANCE L8
BITS_LANDSAT_PIXEL_QA_L8 = {
    '1': {1:'clear'},
    '2': {1:'water'},
    '3': {1:'shadow'},
    '4': {1:'snow'},
    '5': {1:'cloud'},
    '6-7':{3:'high_confidence_cloud'},
    '8-9':{3:'cirrus'},
    '10': {1:'occlusion'}
}

# USGS TOA
BITS_LANDSAT_BQA = {
    '4': {1:'cloud'},
    '5-6': {3:'high_confidence_cloud'},
    '7-8': {3:'shadow'},
    '9-10': {3:'snow'}
}

# USGS TOA L8
BITS_LANDSAT_BQA_L8 = {
    '4': {1:'cloud'},
    '5-6': {3:'high_confidence_cloud'},
    '7-8': {3:'shadow'},
    '9-10': {3:'snow'},
    '11-12': {3:'cirrus'}
}

# SENTINEL 2
BITS_SENTINEL2 = {
    '10':{1:'cloud'},
    '11':{1:'cirrus'}
}


def decode_bits_ee(bit_reader, qa_band):
    """
    :param bit_reader: the bit reader
    :type bit_reader: BitReader
    :param qa_band: name of the band that holds the bit information
    :type qa_band: str
    :return: a function to map over a collection. The function adds all
        categories masks as new bands
    """
    options = ee.Dictionary(bit_reader.info)
    categories = ee.List(bit_reader.all_categories)

    def wrap(image):
        def eachcat(cat, ini):
            ini = ee.Image(ini)
            qa = ini.select(qa_band)
            # get data for category
            data = ee.Dictionary(options.get(cat))
            lshift = ee.Number(data.get('lshift'))
            length = ee.Number(data.get('bit_length'))
            decoded = ee.Number(data.get('shifted'))
            # move = places to move bits right and left back
            move = lshift.add(length)
            # move bits right and left
            rest = qa.rightShift(move).leftShift(move)
            # subtract the rest
            norest = qa.subtract(rest)
            # right shift to compare with decoded data
            to_compare = norest.rightShift(lshift) ## Image
            # compare if is equal, return 0 if not equal, 1 if equal
            mask = to_compare.eq(decoded)
            # rename to the name of the category
            qa_mask = mask.select([0], [cat])

            return ini.addBands(qa_mask)
        return ee.Image(categories.iterate(eachcat, image))
    return wrap


def general_mask(options, reader, qa_band, update_mask=True,
                 add_mask_band=True, add_every_mask=False,
                 all_masks_name='mask'):
    """ General function to get a bit mask band given a set of options
    a bit reader and the name of the qa_band

    :param options: options to decode
    :param reader: the bit reader
    :param qa_band: the name of the qa band
    :param updateMask: whether to update the mask for all options or not
    :param addBands: whether to add the mask band for all options or not
    :return: a function to map over a collection
    """
    encoder = decode_bits_ee(reader, qa_band)
    opt = ee.List(options)
    clases = ("'{}', "*len(options))[:-2].format(*options)

    # Property when adding every band
    msg_eb = "Band called 'mask' is for {} and was computed by geetools" \
          " version {} (https://github.com/gee-community/gee_tools)"
    prop_eb = ee.String(msg_eb.format(clases, __version__))
    prop_name_eb = ee.String('{}_band'.format(all_masks_name))

    def add_every_bandF(image, encoded):
        return image.addBands(encoded).set(prop_name_eb, prop_eb)

    def get_all_mask(encoded):
        # TODO: put this function in tools
        initial = encoded.select([ee.String(opt.get(0))])
        rest = ee.List(opt.slice(1))
        def func(cat, ini):
            ini = ee.Image(ini)
            new = encoded.select([cat])
            return ee.Image(ini.Or(new))

        all_masks = ee.Image(rest.iterate(func, initial)) \
            .select([0], [all_masks_name])
        mask = all_masks.Not()
        return mask

    # 0 0 1
    if not add_every_mask and not update_mask and add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            mask = get_all_mask(encoded)
            return image.addBands(mask)

    # 0 1 0
    elif not add_every_mask and update_mask and not add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            mask = get_all_mask(encoded)
            return image.updateMask(mask)

    # 0 1 1
    elif not add_every_mask and update_mask and add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            mask = get_all_mask(encoded)
            return image.updateMask(mask).addBands(mask)

    # 1 0 0
    elif add_every_mask and not update_mask and not add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            return add_every_bandF(image, encoded)

    # 1 0 1
    elif add_every_mask and not update_mask and add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            mask = get_all_mask(encoded)
            return add_every_bandF(image, encoded).addBands(mask)

    # 1 1 0
    elif add_every_mask and update_mask and not add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            mask = get_all_mask(encoded)
            updated = image.updateMask(mask)
            with_bands = add_every_bandF(updated, encoded)
            return with_bands

    # 1 1 1
    elif add_every_mask and update_mask and add_mask_band:
        def wrap(image):
            encoded = encoder(image).select(opt)
            mask = get_all_mask(encoded)
            updated = image.updateMask(mask)
            with_bands = add_every_bandF(updated, encoded)
            return with_bands.addBands(mask)

    return wrap


def modis09ga(options=('cloud', 'mix', 'shadow', 'snow'), update_mask=True,
              add_mask_band=True, add_every_mask=False):
    """ Function for masking MOD09GA and MYD09GA collections

    :return: a function to use in a map function over a collection
    """
    reader = BitReader(BITS_MODIS09GA, 16)
    return general_mask(options, reader, 'state_1km',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def modis13q1(options=('cloud', 'adjacent', 'shadow', 'snow'),
              update_mask=True, add_mask_band=True, add_every_mask=False):
    """ Function for masking MOD13Q1 and MYD13Q1 collections

    :return: a function to use in a map function over a collection
    """
    reader = BitReader(BITS_MODIS13Q1, 16)
    return general_mask(options, reader, 'DetailedQA',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def landsat457SR_cloudQA(options=('cloud', 'adjacent', 'shadow', 'snow'),
                 update_mask=True, add_mask_band=True, add_every_mask=False):

    reader = BitReader(BITS_LANDSAT_CLOUD_QA, 8)
    return general_mask(options, reader, 'sr_cloud_qa',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def landsat457SR_pixelQA(options=('cloud', 'shadow', 'snow'),
                 update_mask=True, add_mask_band=True, add_every_mask=False):
    reader = BitReader(BITS_LANDSAT_PIXEL_QA, 16)
    return general_mask(options, reader, 'pixel_qa',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def landsat8SR_pixelQA(options=('cloud', 'shadow', 'snow', 'cirrus'),
                update_mask=True, add_mask_band=True, add_every_mask=False):
    reader = BitReader(BITS_LANDSAT_PIXEL_QA_L8, 16)
    return general_mask(options, reader, 'pixel_qa',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def landsat457TOA_BQA(options=('cloud', 'shadow', 'snow'),
                update_mask=True, add_mask_band=True, add_every_mask=False):
    reader = BitReader(BITS_LANDSAT_BQA, 16)
    return general_mask(options, reader, 'BQA',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def landsat8TOA_BQA(options=('cloud', 'shadow', 'snow', 'cirrus'),
                update_mask=True, add_mask_band=True, add_every_mask=False):
    reader = BitReader(BITS_LANDSAT_BQA_L8, 16)
    return general_mask(options, reader, 'BQA',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


def sentinel2(options=('cloud', 'cirrus'), update_mask=True,
              add_mask_band=True, add_every_mask=False):
    reader = BitReader(BITS_SENTINEL2, 16)
    return general_mask(options, reader, 'QA60',
                        update_mask=update_mask,
                        add_mask_band=add_mask_band,
                        add_every_mask=add_every_mask)


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
            """ function to execute if condition == True """
            # get the mask for the option
            mask = tools.image.compute_bits(image, bits_dict.get(option),
                                            bits_dict.get(option),
                                            option)

            # name the mask
            # mask = ee.Image(mask).select([0], [option])
            newmask = all.Or(mask)

            # return ee.Image(all.Or(mask)).addBands(mask)
            return tools.image.replace(i, name_all, newmask).addBands(mask)

        return ee.Image(ee.Algorithms.If(cond, for_true(), i))

    good_pix = ee.Image(opt.iterate(for_iterate, first))

    # return good_pix.Not()
    return good_pix


def hollstein_S2(options=('cloud', 'snow', 'shadow', 'water', 'cirrus'),
                 name='hollstein', addBands=False, updateMask=True):
    """ Compute Hollstein Decision tree for detecting clouds, clouds shadow,
    cirrus, snow and water in Sentinel 2 imagery

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


def dark_pixels(green, swir2, threshold=0.25):
    """ Detect dark pixels from green and swir2 band

    :param green: name of the green band
    :type green: str
    :param swir2: name of the swir2 band
    :type swir2: str
    :param threshold: threshold value from which are considered dark pixels
    :type threshold: float
    :return: a function
    """
    def wrap(img):
        return img.normalizedDifference([green, swir2]).gt(threshold)
    return wrap


### DEPRECATED FUNCTIONS ###
# GENERIC APPLICATION OF MASKS

# LEDAPS
def ledaps(image):
    """ Function to use in Surface Reflectance Collections computed by
    LEDAPS

    Use:

    `masked = collection.map(cloud_mask.ledaps)`
    """
    cmask = image.select('QA')

    valid_data_mask = tools.image.compute_bits(cmask, 1, 1, 'valid_data')
    cloud_mask = tools.image.compute_bits(cmask, 2, 2, 'cloud')
    snow_mask = tools.image.compute_bits(cmask, 4, 4, 'snow')

    good_pix = cloud_mask.eq(0).And(valid_data_mask.eq(0)).And(snow_mask.eq(0))
    result = image.updateMask(good_pix)

    return result


def landsatSR(options=('cloud', 'shadow', 'adjacent', 'snow'), name='sr_mask',
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

