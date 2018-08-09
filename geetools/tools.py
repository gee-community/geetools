# coding=utf-8
"""
This file contains a set of useful functions to use in Google Earth Engine
"""
from __future__ import print_function
import time
import traceback
import functools
import requests
import os
from collections import OrderedDict
import json
import multiprocessing
import shapefile

import ee
from ee import serializer, deserializer

import ee.data
if not ee.data._initialized: ee.Initialize()

from datetime import datetime, timedelta

_execli_trace = False
_execli_times = 10
_execli_wait = 0


class BitReader(object):
    ''' Bit Reader.

    Initializes with parameter `options`, which must be a dictionary with
    the following format:

    keys must be a str with the bits places, example: '0-1' means bit 0
    and bit 1

    values must be a dictionary with the bit value as the key and the category
    (str) as value. Categories must be unique.

    - Encode: given a category/categories return a list of possible values
    - Decode: given a value return a list of categories

    Example:
        MOD09 (http://modis-sr.ltdri.org/guide/MOD09_UserGuide_v1_3.pdf)
        (page 28, state1km, 16 bits):

        ```
        options = {
         '0-1': {0:'clear', 1:'cloud', 2:'mix'},
         '2-2': {1:'shadow'},
         '8-9': {1:'small_cirrus', 2:'average_cirrus', 3:'high_cirrus'}
         }

        reader = BitReader(options, 16)

        print(reader.decode(204))
        ```
        >>['shadow', 'clear']
        ```
        print(reader.match(204, 'cloud')
        ```
        >>False

    '''

    @staticmethod
    def get_bin(bit, nbits=None, shift=0):
        ''' from https://stackoverflow.com/questions/699866/python-int-to-binary '''
        pure = bin(bit)[2:]

        if not nbits:
            nbits = len(pure)

        lpure = len(pure)
        admited_shift = nbits-lpure
        if admited_shift < 0:
            mje = 'the number of bits must be more than the bits'\
                  ' representation of the number. {} ({}) cant be'\
                  ' represented in {} bits'
            raise ValueError(mje.format(pure, bit, nbits))

        if shift > admited_shift:
            mje = 'cant shift {} places for bit {} ({})'
            raise ValueError(mje.format(shift, pure, bit))

        if shift:
            shifted = bin(int(pure, 2)<<shift)[2:]
        else:
            shifted = pure
        return shifted.zfill(nbits)

    @staticmethod
    def decode_key(key):
        ''' decodes an option's key into a list '''
        bits = key.split('-')

        try:
            ini = int(bits[0])
            if len(bits) == 1:
                end = ini
            else:
                end = int(bits[1])
        except:
            mje = 'keys must be with the following format "bit-bit", ' \
                  'example "0-1" (found {})'
            raise ValueError(mje.format(key))

        bits_list = range(ini, end+1)
        return bits_list

    def __init__(self, options, bit_length=None):
        self.options = options

        def all_bits():
            ''' get a list of all bits and check consistance '''
            all_values  = [x for key in options.keys() for x in self.decode_key(key)]
            for val in all_values:
                n = all_values.count(val)
                if n>1:
                    mje = "bits must not overlap. Example: {'0-1':.., " \
                          "'2-3':..} and NOT {'0-1':.., '1-3':..}"
                    raise ValueError(mje)
            return all_values

        ## Check if categories repeat and create property all_categories
        # TODO: reformat categories if find spaces or uppercases
        all_cat = []
        for key, val in self.options.items():
            for i, cat in val.items():
                if cat in all_cat:
                    msg = 'Classes must be unique, found "{}" twice'
                    raise ValueError(msg.format(cat))
                all_cat.append(cat)

        self.all_categories = all_cat
        ###

        all_values = all_bits()

        self.bit_length = len(range(min(all_values), max(all_values)+1))\
                          if not bit_length else bit_length

        self.max = 2**self.bit_length

        info = {}
        for key, val in options.items():
            bits_list = self.decode_key(key)
            bit_length_cat = len(bits_list)
            for i, cat in val.items():
                info[cat] = {'bit_length':bit_length_cat,
                             'lshift':bits_list[0],
                             'shifted': i
                             }
        self.info = info

    def encode_and(self, *args):
        ''' decodes a comination of the given categories. returns a list of
        possible values '''
        first = args[0]
        values_first = self.encode_one(first)

        def get_match(list1, list2):
            return [val for val in list2 if val in list1]

        result = values_first

        for cat in args[1:]:
            values = self.encode_one(cat)
            result = get_match(result, values)
        return result

    def encode_or(self, *args):
        ''' decodes a comination of the given categories. returns a list of
        possible values '''
        first = args[0]
        values_first = self.encode_one(first)

        for cat in args[1:]:
            values = self.encode_one(cat)
            for value in values:
                if value not in values_first:
                    values_first.append(value)

        return values_first

    def encode_not(self, *args):
        ''' Given a set of categories return a list of values that DO NOT
        match with any '''
        result = []
        match = self.encode_or(*args)
        for bit in range(self.max):
            if bit not in match:
                result.append(bit)
        return result

    def encode_one(self, cat):
        ''' Given a category, return a list of values that match it '''
        info = self.info[cat]
        lshift = info['lshift']
        length = info['bit_length']
        decoded = info['shifted']

        result = []
        for bit in range(self.max):
            move = lshift+length
            rest = bit>>move<<move
            norest = bit-rest
            to_compare = norest>>lshift
            if to_compare == decoded:
                result.append(bit)
        return result

    def decode(self, value):
        ''' given a value return a list with all categories '''
        result = []
        for cat in self.all_categories:
            data = self.info[cat]
            lshift = data['lshift']
            length = data['bit_length']
            decoded = data['shifted']
            move = lshift+length
            rest = value>>move<<move
            norest = value-rest
            to_compare = norest>>lshift
            if to_compare == decoded:
                result.append(cat)
        return result

    def match(self, value, category):
        ''' given a value and a category return True if the value includes
        that category, else False '''
        encoded = self.decode(value)
        return category in encoded


class Date(ee.ee_date.Date):

    epoch = datetime(1970, 1, 1, 0, 0, 0)

    def __init__(self, date):
        if isinstance(date, ee.Date):
            date = date.millis()
        super(Date, self).__init__(date)

    def to_datetime(self):
        ''' convert a `ee.Date` into a `datetime` object'''
        formatted = self.format('yyyy,MM,dd,HH,mm,ss').getInfo()
        args = formatted.split(',')
        intargs = [int(arg) for arg in args]
        return datetime(*intargs)

    @staticmethod
    def millis2datetime(millis):
        ''' Converts milliseconds from 1970-01-01T00:00:00 to a
        datetime object '''
        seconds = millis/1000
        dt = timedelta(seconds=seconds)
        return Date.epoch + dt


class Execli(object):
    ''' Class to hold the methods to retry calls to Earth Engine '''
    TRACE = False
    TIMES = 5
    WAIT = 0
    ACTIVE = True

    def execli(self, function):
        ''' This function tries to excecute a client side Earth Engine function
            and retry as many times as needed. It is meant to use in cases when you
            cannot access to the original function. See example.

        :param function: the function to call TIMES
        :return: the return of function
        '''
        try:
            times = int(self.TIMES)
            wait = int(self.WAIT)
        except:
            print(type(self.TIMES))
            print(type(self.WAIT))
            raise ValueError("'times' and 'wait' parameters must be numbers")

        def wrap(f):
            def wrapper(*args, **kwargs):
                r = range(times)
                for i in r:
                    try:
                        result = f(*args, **kwargs)
                    except Exception as e:
                        print("try n°", i, "ERROR:", e)
                        if self.TRACE:
                            traceback.print_exc()
                        if i < r[-1] and wait > 0:
                            print("waiting {} seconds...".format(str(wait)))
                            time.sleep(wait)
                        elif i == r[-1]:
                            msg = "An error occured tring to excecute " \
                                  "the function '{}'"
                            raise RuntimeError(msg.format(f.__name__))
                    else:
                        return result

            return wrapper
        return wrap(function)

    @staticmethod
    def execli_deco():
        """ This is a decorating function to excecute a client side Earth Engine
        function and retry as many times as needed.
        Parameters can be set by modifing module's variables `_execli_trace`,
        `_execli_times` and `_execli_wait`

        :Example:
        .. code:: python

            from geetools.tools import execli_deco
            import ee


            # TRY TO GET THE INFO OF AN IMAGE WITH DEFAULT PARAMETERS

            @execli_deco()
            def info():
                # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
                img = ee.Image("wrongparam")

                return img.getInfo()

            # TRY WITH CUSTOM PARAM (2 times 5 seconds and traceback)

            @execli_deco(2, 5, True)
            def info():
                # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
                img = ee.Image("wrongparam")

                return img.getInfo()

        :param times: number of times it will try to excecute the function
        :type times: int
        :param wait: waiting time to excetue the function again
        :type wait: int
        :param trace: print the traceback
        :type trace: bool
        """
        def wrap(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):

                trace = Execli.TRACE
                times = Execli.TIMES
                wait = Execli.WAIT

                r = range(times)
                for i in r:
                    try:
                        result = f(*args, **kwargs)
                    except Exception as e:
                        print("try n°", i, "ERROR:", e)
                        if trace:
                            traceback.print_exc()
                        if i < r[-1] and wait > 0:
                            print("waiting {} seconds...".format(str(wait)))
                            time.sleep(wait)
                        elif i == r[-1]:
                            msg = "An error occured tring to excecute" \
                                  " the function '{}'"
                            raise RuntimeError(msg.format(f.__name__))
                    else:
                        return result

            return wrapper
        if Execli.ACTIVE:
            return wrap
        else:
            def wrap(f):
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapper
            return wrap

def convert_data_type(newtype):
    """ Convert an image to the specified data type

    :param newtype: the data type. One of 'float', 'int', 'byte', 'double',
        'Uint8','int8','Uint16', 'int16', 'Uint32','int32'
    :type newtype: str
    :return: a function to map over a collection
    :rtype: function
    """
    def wrap(image):
        TYPES = {'float': image.toFloat,
                 'int': image.toInt,
                 'byte': image.toByte,
                 'double': image.toDouble,
                 'Uint8': image.toUint8,
                 'int8': image.toInt8,
                 'Uint16': image.toUint16,
                 'int16': image.toInt16,
                 'Uint32': image.toUint32,
                 'int32': image.toInt32}
        return TYPES[newtype]()
    return wrap

# DECORATOR
# def execli_deco(times=None, wait=None, trace=None):
def execli_deco():
    """ This is a decorating function to excecute a client side Earth Engine
    function and retry as many times as needed.
    Parameters can be set by modifing module's variables `_execli_trace`,
    `_execli_times` and `_execli_wait`

    :Example:
    .. code:: python

        from geetools.tools import execli_deco
        import ee


        # TRY TO GET THE INFO OF AN IMAGE WITH DEFAULT PARAMETERS

        @execli_deco()
        def info():
            # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
            img = ee.Image("wrongparam")

            return img.getInfo()

        # TRY WITH CUSTOM PARAM (2 times 5 seconds and traceback)

        @execli_deco(2, 5, True)
        def info():
            # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
            img = ee.Image("wrongparam")

            return img.getInfo()

    :param times: number of times it will try to excecute the function
    :type times: int
    :param wait: waiting time to excetue the function again
    :type wait: int
    :param trace: print the traceback
    :type trace: bool
    """
    def wrap(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):

            trace = _execli_trace
            times = _execli_times
            wait = _execli_wait

            r = range(times)
            for i in r:
                try:
                    result = f(*args, **kwargs)
                except Exception as e:
                    print("try n°", i, "ERROR:", e)
                    if trace:
                        traceback.print_exc()
                    if i < r[-1] and wait > 0:
                        print("waiting {} seconds...".format(str(wait)))
                        time.sleep(wait)
                    elif i == r[-1]:
                        raise RuntimeError("An error occured tring to excecute"\
                                           " the function '{}'".format(f.__name__))
                else:
                    return result

        return wrapper
    return wrap

def execli(function, times=None, wait=None, trace=None):
    """ This function tries to excecute a client side Earth Engine function
    and retry as many times as needed. It is meant to use in cases when you
    cannot access to the original function. See example.

    :Example:
    .. code:: python

        from geetools.tools import execli
        import ee

        # THIS IMAGE DOESN'E EXISTE SO IT WILL THROW AN ERROR
        img = ee.Image("wrongparam")

        # try to get the info with default parameters (10 times, wait 0 sec)
        info = execli(img.getInfo)()
        print info

        # try with custom param (2 times 5 seconds with traceback)
        info2 = execli(img.getInfo, 2, 5, True)
        print info2


    :param times: number of times it will try to excecute the function
    :type times: int
    :param wait: waiting time to excetue the function again
    :type wait: int
    :param trace: print the traceback
    :type trace: bool
    """
    if trace is None:
        trace = _execli_trace
    if times is None:
        times = _execli_times
    if wait is None:
        wait = _execli_wait

    try:
        times = int(times)
        wait = int(wait)
    except:
        print(type(times))
        print(type(wait))
        raise ValueError("'times' and 'wait' parameters must be numbers")

    def wrap(f):
        def wrapper(*args, **kwargs):
            r = range(times)
            for i in r:
                try:
                    result = f(*args, **kwargs)
                except Exception as e:
                    print("try n°", i, "ERROR:", e)
                    if trace:
                        traceback.print_exc()
                    if i < r[-1] and wait > 0:
                        print("waiting {} seconds...".format(str(wait)))
                        time.sleep(wait)
                    elif i == r[-1]:
                        raise RuntimeError("An error occured tring to excecute" \
                                           "the funcion '{0}'".format(f.__name__))
                else:
                    return result

        return wrapper
    return wrap(function)

# INITIALIZE EARTH ENGINE USING EXECLI FUNCTION
#try:
#    ee.Initialize()
#except:
#    pass

def minscale(image):
    """ Get the minimal scale of an Image, looking at all Image's bands.
    For example if:
        B1 = 30
        B2 = 60
        B3 = 10
    the function will return 10

    :param image: the Image
    :type image: ee.Image
    :return: the minimal scale
    :rtype: ee.Number
    """
    bands = image.bandNames()

    first = image.select([ee.String(bands.get(0))])
    ini = ee.Number(first.projection().nominalScale())

    def wrap(name, i):
        i = ee.Number(i)
        scale = ee.Number(image.select([name]).projection().nominalScale())
        condition = scale.lte(i)
        newscale = ee.Algorithms.If(condition, scale, i)
        return newscale

    return ee.Number(bands.slice(1).iterate(wrap, ini))

# @execli_deco()
def getRegion(eeobject, bounds=False):
    """ Gets the region of a given geometry to use in exporting tasks. The
    argument can be a Geometry, Feature or Image

    :param eeobject: geometry to get region of
    :type eeobject: ee.Feature, ee.Geometry, ee.Image
    :return: region coordinates ready to use in a client-side EE function
    :rtype: json
    """
    if isinstance(eeobject, ee.Geometry):
        eeobject = eeobject.bounds() if bounds else eeobject
        region = eeobject.getInfo()["coordinates"]
    elif isinstance(eeobject, (ee.Feature, ee.Image,
                               ee.FeatureCollection, ee.ImageCollection)):
        eeobject = eeobject.geometry().bounds() if bounds else eeobject.geometry()
        region = eeobject.getInfo()["coordinates"]
    elif isinstance(eeobject, list):
        condition = all([type(item) == list for item in eeobject])
        if condition:
            region = eeobject
    else:
        region = eeobject
    return region

def mask2zero(img):
    """ Converts masked pixels into zeros

    :param img: Image contained in the Collection
    :type img: ee.Image
    """
    theMask = img.mask()
    return theMask.where(1, img)

def mask2number(number):
    """ Converts masked pixels into the specified number in each image of
    the collection. As *number* has to be a float, the resulting Image will
    have all bands converted to Float.

    :param number: number to fill masked pixels
    :type number: float
    :return: the function for mapping
    :rtype: function
    """
    # TODO: let the user choose the type of the output

    def mapping(img):
        mask = img.mask()
        test = mask.Not()
        img = mask2zero(img)
        return img.where(test, number)

    return mapping

def create_assets(asset_ids, asset_type, mk_parents):
    """Creates the specified assets if they do not exist.
    This is a fork of the original function in 'ee.data' module with the
    difference that

    - If the asset already exists but the type is different that the one we
      want, raise an error
    - Starts the creation of folders since 'user/username/'

    Will be here until I can pull requests to the original repo

    :param asset_ids: list of paths
    :type asset_ids: list
    :param asset_type: the type of the assets. Options: "ImageCollection" or
        "Folder"
    :type asset_type: str
    :param mk_parents: make the parents?
    :type mk_parents: bool
    :return: A description of the saved asset, including a generated ID

    """
    for asset_id in asset_ids:
        already = ee.data.getInfo(asset_id)
        if already:
            ty = already['type']
            if ty != asset_type:
                raise ValueError("{} is a {}. Can't create asset".format(asset_id, ty))
            print('Asset %s already exists' % asset_id)
            continue
        if mk_parents:
            parts = asset_id.split('/')
            root = "/".join(parts[:2])
            root += "/"
            for part in parts[2:-1]:
                root += part
                if ee.data.getInfo(root) is None:
                    ee.data.createAsset({'type': 'Folder'}, root)
                root += '/'
        return ee.data.createAsset({'type': asset_type}, asset_id)

@Execli.execli_deco()
def exportByFeat(img, fc, prop, folder, scale=1000, dataType="float", **kwargs):
    """ Export an image clipped by features (Polygons). You can use the same
    arguments as the original function ee.batch.export.image.toDrive

    :Parameters:
    :param img: image to clip
    :type img: ee.Image
    :param fc: feature collection
    :type fc: ee.FeatureCollection
    :param prop: name of the property of the features to paste in the image
    :type prop: str
    :param folder: same as ee.Export
    :type folder: str
    :param scale: same as ee.Export. Default to 1000
    :type scale: int
    :param dataType: as downloaded images **must** have the same data type in all
        bands, you have to set it here. Can be one of: "float", "double", "int",
        "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
    :type dataType: str

    :return: a list of all tasks (for further processing/checking)
    :rtype: list
    """

    featlist = fc.getInfo()["features"]
    name = img.getInfo()["id"].split("/")[-1]

    if dataType in TYPES:
        typefunc = TYPES[dataType]
        img = typefunc(img)
    elif dataType in dir(ee.Image):
        img = dataType(img)

    def unpack(thelist):
        unpacked = []
        for i in thelist:
            unpacked.append(i[0])
            unpacked.append(i[1])
        return unpacked

    tasklist = []

    for f in featlist:
        geomlist = unpack(f["geometry"]["coordinates"][0])
        geom = ee.Geometry.Polygon(geomlist)

        feat = ee.Feature(geom)
        dis = f["properties"][prop]

        if type(dis) is float:
            disS = str(int(dis))
        elif type(dis) is int:
            disS = str(dis)
        elif type(dis) is str:
            disS = dis
        else:
            print("unknown property's type")
            break

        finalname = "{0}_{1}_{2}".format(name, prop, disS)

        task = ee.batch.Export.image.toDrive(
            image=img,
            description=finalname,
            folder=folder,
            fileNamePrefix=finalname,
            region=feat.geometry().bounds().getInfo()["coordinates"],
            scale=scale, **kwargs)

        task.start()
        print("exporting", finalname)
        tasklist.append(task)

    return tasklist

@Execli.execli_deco()
def col2drive(col, folder, scale=30, dataType="float", region=None, **kwargs):
    """ Upload all images from one collection to Google Drive. You can use the
    same arguments as the original function ee.batch.export.image.toDrive

    :param col: Collection to upload
    :type col: ee.ImageCollection
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
        (Landsat resolution)
    :type scale: int
    :param maxImgs: maximum number of images inside the collection
    :type maxImgs: int
    :param dataType: as downloaded images **must** have the same data type in all
        bands, you have to set it here. Can be one of: "float", "double", "int",
        "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
    :type dataType: str
    :return: list of tasks
    :rtype: list
    """
    size = col.size().getInfo()
    alist = col.toList(size)
    tasklist = []

    if region is None:
        region = ee.Image(alist.get(0)).geometry().getInfo()["coordinates"]
    else:
        region = getRegion(region)

    for idx in range(0, size):
        img = alist.get(idx)
        img = ee.Image(img)
        name = img.id().getInfo().split("/")[-1]

        if dataType in TYPES:
            typefunc = TYPES[dataType]
            img = typefunc(img)
        elif dataType in dir(ee.Image):
            img = dataType(img)
        else:
            raise ValueError("specified data type is not found")

        task = ee.batch.Export.image.toDrive(image=img,
                                             description=name,
                                             folder=folder,
                                             fileNamePrefix=name,
                                             region=region,
                                             scale=scale, **kwargs)
        task.start()
        tasklist.append(task)

    return tasklist

@Execli.execli_deco()
def col2asset(col, assetPath, scale=30, region=None, create=True, **kwargs):
    """ Upload all images from one collection to a Earth Engine Asset. You can
    use the same arguments as the original function ee.batch.export.image.toDrive

    :param col: Collection to upload
    :type col: ee.ImageCollection
    :param assetPath: path of the asset where images will go
    :type assetPath: str
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
        (Landsat resolution)
    :type scale: int
    :param maxImgs: maximum number of images inside the collection
    :type maxImgs: int
    :param dataType: as downloaded images **must** have the same data type in all
        bands, you have to set it here. Can be one of: "float", "double", "int",
        "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
    :type dataType: str
    :return: list of tasks
    :rtype: list
    """
    size = col.size().getInfo()
    alist = col.toList(size)
    tasklist = []

    if create:
        create_assets([assetPath], 'ImageCollection', True)

    if region is None:
        first_img = ee.Image(alist.get(0))
        region = getRegion(first_img)
        # print(region)
        # region = ee.Image(alist.get(0)).geometry().getInfo()["coordinates"]
    else:
        region = getRegion(region)

    for idx in range(0, size):
        img = alist.get(idx)
        img = ee.Image(img)
        name = img.id().getInfo().split("/")[-1]

        assetId = assetPath+"/"+name

        task = ee.batch.Export.image.toAsset(image=img,
                                             assetId=assetId,
                                             description=name,
                                             region=region,
                                             scale=scale, **kwargs)
        task.start()
        tasklist.append(task)

    return tasklist

@Execli.execli_deco()
def image2asset(image, assetPath, name=None, to='Folder', scale=None,
                region=None, create=True, dataType='float', **kwargs):
    """ Upload an Image to an Asset. Similar to Export.image.toAsset but this
    function can create folders and ImageCollections on the fly. You can pass
    the same params as the original function

    :param image: the image to upload
    :type image: ee.Image
    :param assetPath: path to upload the image (only PATH, without filename)
    :type assetPath: str
    :param name: filename for the image (AssetID will be assetPath + name)
    :type name: str
    :param to: where to save the image. Options: 'Folder' or 'ImageCollection'
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel)
        (Landsat resolution)
    :type scale: int
    :param dataType: as downloaded images **must** have the same data type in all
        bands, you have to set it here. Can be one of: "float", "double", "int",
        "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
    :type dataType: str
    :return: the tasks
    :rtype: ee.batch.Task
    """
    # Convert data type
    image = convert_data_type(dataType)(image)

    # Check if the user is specified in the asset path
    is_user = (assetPath.split('/')[0] == 'users')
    if not is_user:
        user = ee.batch.data.getAssetRoots()[0]['id']
        assetPath = "{}/{}".format(user, assetPath)

    # description = kwargs.get('description', image.id().getInfo())
    # Set scale
    scale = scale if scale else int(minscale(image).getInfo())

    if create:
        # Recrusive create path
        path2create = assetPath #  '/'.join(assetPath.split('/')[:-1])
        create_assets([path2create], to, True)

    # Region
    region = getRegion(region)
    # Name
    name = name if name else image.id().getInfo()
    # Asset ID (Path + name)
    assetId = '/'.join([assetPath, name])
    # Init task
    task = ee.batch.Export.image.toAsset(image, assetId=assetId,
                                         region=region, scale=scale,
                                         description=name,
                                         **kwargs)
    task.start()
    return task

@Execli.execli_deco()
def image2local(image, path=None, name=None, scale=None, region=None,
                dimensions=None, toFolder=True, checkExist=True):
    ''' Download an Image to your hard drive

    :param image: the image to download
    :type image: ee.Image
    :param path: the path to download the image. If None, it will be downloaded
        to the same folder as the script is
    :type path: str
    :param scale: scale of the image to download. If None, tries to get it.
    :type scale: int
    :param region: region to from where to download the image. If None, will be
        the image region
    :type region: ee.Geometry
    :param
    '''
    # make some imports
    import glob

    try:
        import zipfile
    except:
        raise ValueError(
            'zipfile module not found, install it using `pip install zipfile`')

    try:
        from osgeo import gdal
    except ImportError:
        try:
            import gdal
        except:
            raise

    # Reproject image
    # image = image.reproject(ee.Projection('EPSG:4326'))

    name = name if name else image.id().getInfo()

    scale = scale if scale else int(minscale(image).getInfo())

    if region:
        region = getRegion(region)
    else:
        region = getRegion(image)

    params = {'region': region,
              'scale': scale}

    params = params.update({'dimensions': dimensions}) if dimensions else params

    url = image.getDownloadURL(params)

    ext = 'zip'

    downloadFile(url, name, ext)

    filename = '{}.{}'.format(name, ext)

    original_filepath = os.path.join(os.getcwd(), filename)

    if path:
        filepath = os.path.join(path, filename)
        os.rename(original_filepath, filepath)
    else:
        path = os.getcwd()
        filepath = os.path.join(path, filename)

    try:
        zip_ref = zipfile.ZipFile(filepath, 'r')

        if toFolder:
            finalpath = os.path.join(path, name)
        else:
            finalpath = path

        zip_ref.extractall(finalpath)
        zip_ref.close()
    except:
        raise

    # Merge TIFF
    # alltif = glob.glob(os.path.join(finalpath, '.tif'))
    # outvrt = '/vsimem/stacked.vrt' #/vsimem is special in-memory virtual "directory"
    # outtif = os.path.join(finalpath, name+'.tif')
    #
    # outds = gdal.BuildVRT(outvrt, alltif, separate=True)
    # gdal.Translate(outtif, outds)

def addConstantBands(value=None, *names, **pairs):
    """ Adds bands with a constant value

    :param names: final names for the additional bands
    :type names: list
    :param value: constant value
    :type value: int or float
    :param pairs: keywords for the bands (see example)
    :type pairs: dict
    :return: the function for ee.ImageCollection.map()
    :rtype: function

    :Example:

    .. code:: python

        from geetools.tools import addConstantBands
        import ee

        col = ee.ImageCollection(ID)

        # Option 1 - arguments
        addC = addConstantBands(0, "a", "b", "c")
        newcol = col.map(addC)

        # Option 2 - keyword arguments
        addC = addConstantBands(a=0, b=1, c=2)
        newcol = col.map(addC)

        # Option 3 - Combining
        addC = addC = addConstantBands(0, "a", "b", "c", d=1, e=2)
        newcol = col.map(addC)
    """
    is_val_n = type(value) is int or type(value) is float

    if is_val_n and names:
        list1 = [ee.Image.constant(value).select([0], [n]) for n in names]
    else:
        list1 = []

    if pairs:
        list2 = [ee.Image.constant(val).select([0], [key]) for key, val in pairs.iteritems()]
    else:
        list2 = []

    if list1 or list2:
        lista_img = list1 + list2
    elif value is None:
        raise ValueError("Parameter 'value' must be a number")
    else:
        return addConstantBands(value, "constant")

    img_final = reduce(lambda x, y: x.addBands(y), lista_img)

    def apply(img):
        return ee.Image(img).addBands(ee.Image(img_final))

    return apply

def replace(img, to_replace, to_add):
    """ Replace one band of the image with a provided band

    :param img: Image containing the band to replace
    :type img: ee.Image
    :param to_replace: name of the band to replace. If the image hasn't got
        that band, it will be added to the image.
    :type to_replace: str
    :param to_add: Image (one band) containing the band to add. If an Image
        with more than one band is provided, it uses the first band.
    :type to_add: ee.Image
    :return: Same Image provided with the band replaced
    :rtype: ee.Image
    """
    band = to_add.select([0])
    bands = img.bandNames()
    # band = band.select([0], [to_replace])
    resto = bands.remove(to_replace)
    img_resto = img.select(resto)
    img_final = img_resto.addBands(band)
    return img_final

# @execli_deco()
def get_value(img, point, scale=None, side="server"):
    """ Return the value of all bands of the image in the specified point

    :param img: Image to get the info from
    :type img: ee.Image
    :param point: Point from where to get the info
    :type point: ee.Geometry.Point
    :param scale: The scale to use in the reducer. It defaults to 10 due to the
        minimum scale available in EE (Sentinel 10m)
    :type scale: int
    :param side: 'server' or 'client' side
    :type side: str
    :return: Values of all bands in the ponit
    :rtype: ee.Dictionary or dict
    """
    if scale:
        scale = int(scale)
    else:
        # scale = minscale(img)
        scale = 1

    type = point.getInfo()["type"]
    if type != "Point":
        raise ValueError("Point must be ee.Geometry.Point")

    result = img.reduceRegion(ee.Reducer.first(), point, scale)

    if side == 'server':
        return result
    elif side == 'client':
        return result.getInfo()
    else:
        raise ValueError("side parameter must be 'server' or 'client'")

# @execli_deco()
def get_values(col, geometry, reducer=ee.Reducer.mean(), scale=None,
               id='system:index', properties=None, side='server'):
    """ Return all values of all bands of an image collection in the specified
    geometry

    :param col: ImageCollection to get the info from
    :type col: ee.ImageCollection
    :param geometry: Point from where to get the info
    :type geometry: ee.Geometry
    :param scale: The scale to use in the reducer. It defaults to 10 due to the
    minimum scale available in EE (Sentinel 10m)
    :type scale: int
    :param id: image property that will be the key in the result dict
    :type id: str
    :param properties: image properties that will be added to the resulting
        dict
    :type properties: list
    :param side: 'server' or 'client' side
    :type side: str
    :return: Values of all bands in the ponit
    :rtype: dict
    """
    # ty = geometry.getInfo()["type"]
    # if ty != "Point":
    #     raise ValueError("Point must be ee.Geometry.Point")

    if not scale:
        # scale = minscale(ee.Image(col.first()))
        scale = 1
    else:
        scale = int(scale)

    propid = ee.Image(col.first()).get(id).getInfo()
    def transform(eeobject):
        if isinstance(propid, (int, float)):
            return ee.Number(eeobject).format()
        elif isinstance(propid, (str, unicode)):
            return ee.String(eeobject)
        else:
            msg = 'property must be a number or string, found {}'
            raise ValueError(msg.format(type(propid)))

    if not properties:
        properties = []
    properties = ee.List(properties)

    def listval(img, it):
        theid = ee.String(transform(img.get(id)))
        values = img.reduceRegion(reducer, geometry, scale)
        values = ee.Dictionary(values)

        def add_properties(prop, ini):
            ini = ee.Dictionary(ini)
            value = img.get(prop)
            return ini.set(prop, value)

        with_prop = ee.Dictionary(properties.iterate(add_properties, values))
        return ee.Dictionary(it).set(theid, with_prop)

    result = col.iterate(listval, ee.Dictionary({}))
    result = ee.Dictionary(result)

    if side == 'server':
        return result
    elif side == 'client':
        return result.getInfo()
    else:
        raise ValueError("side parameter must be 'server' or 'client'")

def sumBands(name="sum", bands=None):
    """ Adds all *bands* values and puts the result on *name*.

    There are 2 ways to use it:

    :ONE IMAGE:

    .. code:: python

        img = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013344LGN00")
        fsum = sumBands("added_bands", ("B1", "B2", "B3"))
        newimg = fsum(img)

    :COLLECTION:

    .. code:: python

        col = ee.ImageCollection("LANDSAT/LC8_L1T_TOA_FMASK")
        fsum = sumBands("added_bands", ("B1", "B2", "B3"))
        newcol = col.map(fsum)

    :param name: name for the band that contains the added values of bands
    :type name: str
    :param bands: names of the bands to be added. If None (default) it sums
        all bands
    :type bands: tuple
    :return: The function to use in ee.ImageCollection.map()
    :rtype: function
    """
    def wrap(image):
        band_names = image.bandNames()
        if bands is None:
            bn = band_names
        else:
            bn = ee.List(list(bands))

        nim = ee.Image(0).select([0], [name])

        # TODO: check if passed band names are in band names # DONE
        def sum_bands(n, ini):
            condition = ee.List(band_names).contains(n)
            return ee.Algorithms.If(condition,
                                    ee.Image(ini).add(image.select([n])),
                                    ee.Image(ini))

        newimg = ee.Image(bn.iterate(sum_bands, nim))

        return image.addBands(newimg)
    return wrap

def replace_many(listEE, replace):
    """ Replace many elements of a Earth Engine List object

    :param listEE: list
    :type listEE: ee.List
    :param toreplace: values to replace
    :type toreplace: dict
    :return: list with replaced values
    :rtype: ee.List

    :EXAMPLE:

    .. code:: python

        list = ee.List(["one", "two", "three", 4])
        newlist = replace_many(list, {"one": 1, 4:"four"})

        print newlist.getInfo()

    >> [1, "two", "three", "four"]

    """
    for key, val in replace.iteritems():
        if val:
            listEE = listEE.replace(key, val)
    return listEE

def rename_bands(names):
    """ Renames bands of images. Can be used in one image or in a collection

    :param names: matching names where key is original name and values the
        new name
    :type names: dict
    :return: a function to rename images
    :rtype: function

    :EXAMPLE:

    .. code:: python

        image = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013344LGN00")
        p = ee.Geometry.Point(-71.72029495239258, -42.78997046797438)

        i = rename_bands({"B1":"BLUE", "B2":"GREEN"})(image)

        print get_value(image, p)
        print get_value(i, p)

    >> {u'B1': 0.10094200074672699, u'B2': 0.07873955368995667, u'B3': 0.057160500437021255}
    >> {u'BLUE': 0.10094200074672699, u'GREEN': 0.07873955368995667, u'B3': 0.057160500437021255}
    """
    def wrap(img):
        bandnames = img.bandNames()
        newnames = replace_many(bandnames, names)
        return img.select(bandnames, newnames)
    return wrap

def pass_prop(img_with, img_without, properties):
    """ Pass properties from one image to another

    :param img_with: image that has the properties to tranpass
    :type img_with: ee.Image
    :param img_without: image that will recieve the properties
    :type img_without: ee.Image
    :param properties: properies to transpass
    :type properties: list
    :return: the image with the new properties
    :rtype: ee.Image
    """
    for prop in properties:
        p = img_with.get(prop)
        img_without = img_without.set(prop, p)
    return img_without

def pass_date(img_with, img_without):
    """ Pass date property from one image to another """
    return pass_prop(img_with, img_without, "system:time_start")

def list_intersection(listEE1, listEE2):
    """ Find matching values. If listEE1 has duplicated values that are present
    on listEE2, all values from listEE1 will apear in the result

    :param listEE1: one Earth Engine List
    :param listEE2: the other Earth Engine List
    :return: list with the intersection (matching values)
    :rtype: ee.List
    """
    newlist = ee.List([])
    def wrap(element, first):
        first = ee.List(first)

        return ee.Algorithms.If(listEE2.contains(element), first.add(element), first)

    return ee.List(listEE1.iterate(wrap, newlist))

def list_diff(listEE1, listEE2):
    """ Difference between two earth engine lists

    :param listEE1: one list
    :param listEE2: the other list
    :return: list with the values of the difference
    :rtype: ee.List
    """
    return listEE1.removeAll(listEE2).add(listEE2.removeAll(listEE1)).flatten()

def parametrize(range_from, range_to, bands=None):
    """ Parametrize from a original known range to a fixed new range

    :Parameters:
    :param range_from: Original range. example: (0, 5000)
    :type range_from: tuple
    :param range_to: Fixed new range. example: (500, 1000)
    :type range_to: tuple
    :param bands: bands to parametrize. If *None* all bands will be
    parametrized.
    :type bands: list

    :return: Function to use in map() or alone
    :rtype: function
    """

    rango_orig = range_from if isinstance(range_from, ee.List) else ee.List(
        range_from)
    rango_final = range_to if isinstance(range_to, ee.List) else ee.List(range_to)

    # Imagenes del min y max originales
    min0 = ee.Image.constant(rango_orig.get(0))
    max0 = ee.Image.constant(rango_orig.get(1))

    # Rango de min a max
    rango0 = max0.subtract(min0)

    # Imagenes del min y max final
    min1 = ee.Image.constant(rango_final.get(0))
    max1 = ee.Image.constant(rango_final.get(1))

    # Rango final
    rango1 = max1.subtract(min1)

    def wrap(img):
        # todas las bandas
        todas = img.bandNames()

        # bandas a parametrizar. Si no se especifica se usan todas
        if bands:
            bandasEE = ee.List(bands)
        else:
            bandasEE = img.bandNames()

        inter = list_intersection(bandasEE, todas)
        diff = list_diff(todas, inter)
        imagen = img.select(inter)

        # Porcentaje del valor actual de la banda en el rango de valores
        porcent = imagen.subtract(min0).divide(rango0)

        # Teniendo en cuenta el porcentaje en el que se encuentra el valor
        # real en el rango real, calculo el valor en el que se encuentra segun
        # el rango final. Porcentaje*rango_final + min_final

        final = porcent.multiply(rango1).add(min1)

        # Agrego el resto de las bandas que no se parametrizaron
        final = img.select(diff).addBands(final)

        return pass_date(img, final)
    return wrap

# Compute Bits
def compute_bits(start, end, newName):
    """ Compute the bits of an image

    :param start: start bit
    :type start: int
    :param end: end bit
    :type end: int
    :param newName: new name for the band
    :type newName: str
    :return: A function which single argument is the image and returns a single
        band image of the extracted bits, giving the band a new name
    :rtype: function
    """
    pattern = ee.Number(0)
    start = ee.Number(start).toInt()
    end = ee.Number(end).toInt()
    newName = ee.String(newName)

    seq = ee.List.sequence(start, end)

    def toiterate(element, ini):
        ini = ee.Number(ini)
        bit = ee.Number(2).pow(ee.Number(element))
        return ini.add(bit)

    patt = seq.iterate(toiterate, pattern)

    patt = ee.Number(patt).toInt()

    def wrap(image):
        good_pix = image.select([0], [newName]).toInt()\
                        .bitwiseAnd(patt).rightShift(start)
        return good_pix.toInt()

    return wrap

def compute_bits_client(image, start, end, newName):
    """ Compute the bits of an image

    :param image: image that contains the band with the bit information
    :type image: ee.Image
    :param start: start bit
    :type start: int
    :param end: end bit
    :type end: int
    :param newName: new name for the band
    :type newName: str
    :return: a single band image of the extracted bits, giving the band
        a new name
    :rtype: ee.Image
    """
    pattern = 0

    for i in range(start, end + 1):
        pattern += 2**i

    return image.select([0], [newName]).bitwiseAnd(pattern).rightShift(start)

def downloadFile(url, name, ext):
    """ Download a file from a given url

    :param url: full url
    :type url: str
    :param name: name for the file (can contain a path)
    :type name: str
    :param ext: extension for the file
    :type ext: str
    :return: the created file (closed)
    :rtype: file
    """
    response = requests.get(url, stream=True)
    code = response.status_code

    while code != 200:
        if code == 400:
            return None
        response = requests.get(url, stream=True)
        code = response.status_code
        size = response.headers.get('content-length',0)
        if size: print('size:', size)

    with open(name + "." + ext, "wb") as handle:
        for data in response.iter_content():
            handle.write(data)

    return handle

def empty_image(value=0, bandnames=None, bands=None):
    ''' Create an empty image with the given bandnames and value, or from
     a dictionary of {name: value}. If you use `bandnames` parameter, `bands`
     parameter will be omitted

    :param bandnames: list of bandnames
    :type bandnames: ee.List or list
    :param value: value for every band of the resulting image
    :type value: int or float
    :param bands: if this is specified, other params will be ignored and the
        image will be created with values from `bands` dict: {name: value}
    :type bands: dict
    '''
    if bandnames:
        bandnames = bandnames if isinstance(bandnames, ee.List) else ee.List(bandnames)
        ini = ee.Image(0)
        def bn(name, img):
            img = ee.Image(img)
            newi = ee.Image(value).select([0], [name])
            return img.addBands(newi)
        finali = ee.Image(bandnames.iterate(bn, ini))

        # return finali.select(bandnames)
    elif bands:
        bandnames = ee.List(bands.keys())
        finali = ee.Image(0)
        for name, value in bands.iteritems():
            i = ee.Image(value).select([0], [name])
            finali = finali.addBands(i)

        # return finali.select(bandnames)
    else:
        bandnames = ['constant']
        finali = ee.Image.constant(value)

    return finali.select(bandnames)

def list_remove_duplicates(listEE):
    """ Remove duplicated values from a EE list object """
    newlist = ee.List([])
    def wrap(element, init):
        init = ee.List(init)
        contained = init.contains(element)
        return ee.Algorithms.If(contained, init, init.add(element))
    return ee.List(listEE.iterate(wrap, newlist))

def get_from_dict(a_list, a_dict):
    """ Get a list of Dict's values from a list object. Keys must be unique

    :param a_list: list of keys
    :type a_list: ee.List
    :param a_dict: dict to get the values for list's keys
    :type a_dict: ee.Dictionary
    :return: a list of values
    :rtype: ee.List
    """
    a_list = ee.List(a_list) if isinstance(a_list, list) else a_list
    a_dict = ee.Dictionary(a_dict) if isinstance(a_dict, dict) else a_dict

    empty = ee.List([])

    def wrap(el, first):
        f = ee.List(first)
        cond = a_dict.contains(el)
        return ee.Algorithms.If(cond, f.add(a_dict.get(el)), f)

    values = ee.List(a_list.iterate(wrap, empty))
    return values

def trim_decimals(places=2):
    """ Decrease the number of decimals in a ee.Number

    :param places: number of decimal places to leave
    :return: a function to map over a list
    """
    factor = ee.Number(10).pow(ee.Number(places).toInt())

    def wrap(number):
        n = ee.Number(number)

        floor = n.floor()
        decimals = n.subtract(floor)
        take = decimals.multiply(factor).toInt()
        newdecimals = take.toFloat().divide(factor)
        return floor.add(newdecimals).toFloat()

    return wrap

def sort_dict(dictionary):
    """ Sort a dictionary. Can be a `dict` or a `ee.Dictionary`

    :param dictionary: the dictionary to sort
    :type dictionary: dict or ee.Dictionary
    """
    if isinstance(dictionary, dict):
        sorted = OrderedDict()
        keys = dictionary.keys()
        keys.sort()
        for key in keys:
            sorted[key] = dictionary[key]
        return sorted
    elif isinstance(dictionary, ee.Dictionary):
        keys = dictionary.keys()
        ordered = keys.sort()
        newdict = ee.Dictionary()
        def iteration(key, first):
            new = ee.Dictionary(first)
            val = dictionary.get(key)
            return new.set(key, val)
        return ee.Dictionary(ordered.iterate(iteration, newdict))
    else:
        return dictionary

def getInfo(eeobject, async=False):
    ''' Proxy to getInfo with async possibility. If async is True, it returns a
    list like object (multiprocessing ListProxy) '''
    if not async:
        return eeobject.getInfo()
    else:
        def worker(obj, share):
            '''worker function'''
            info = obj.getInfo()
            share.value = info

        manager = multiprocessing.Manager()
        share = manager.Value()
        p = multiprocessing.Process(target=worker, args=(eeobject, share))
        p.start()

        return share

def eprint(eeobject, indent=2, notebook=False, async=False):
    """ Print an EE Object. Same as `print(object.getInfo())`

    :param eeobject: object to print
    :type eeobject: ee.ComputedObject
    :param notebook: if True, prints the object as an Accordion Widget for
        the Jupyter Notebook
    :type notebook: bool
    :param indent: indentation of the print output
    :type indent: int
    :param async: call getInfo() asynchronously
    :type async: bool
    """

    import pprint
    pp = pprint.PrettyPrinter(indent=indent)

    def get_async(eeobject, result):
        obj = deserializer.decode(eeobject)
        try:
            result['result'] = obj.getInfo()
        except:
            raise

    def get_async2(eeobject, result):
        info = eeobject.getInfo()
        result.append(info)

    try:
        if async:
            manager = multiprocessing.Manager()
            info = manager.list()
            proxy = serializer.encode(eeobject)
            process = multiprocessing.Process(target=get_async2, args=(eeobject, info))
            process.start()
            # process.join()
        else:
            info = eeobject.getInfo()

    except Exception as e:
        print(str(e))
        info = eeobject

    if not notebook:
        if async:
            def finalwait():
                isinfo = len(info) > 0
                while not isinfo:
                    isinfo = len(info) > 0
                pp.pprint(info[0])
            p = multiprocessing.Process(target=finalwait, args=())
            p.start()
        else:
            pp.pprint(info)
    else:
        from .ipytools import create_accordion
        from IPython.display import display
        output = create_accordion(info)
        display(output)


def esave(eeobject, filename, path=None):
    ''' Saves any EE object to a file with extension .gee

        The file has to be opened with `eopen`
    '''
    obj = serializer.encode(eeobject)

    path = path if path else os.getcwd()

    with open(os.path.join(path, filename+'.gee'), 'w') as js:
        json.dump(obj, js)

def eopen(file, path=None):
    ''' Opens a files saved with `esave` method

    :return: the EE object '''

    path = path if path else os.getcwd()

    try:
        with open(os.path.join(path, file), 'r') as gee:
            thefile = json.load(gee)
    except IOError:
        with open(os.path.join(path, file+'.gee'), 'r') as gee:
            thefile = json.load(gee)

    return deserializer.decode(thefile)

def recrusive_delete_asset(assetId):
    try:
        content = ee.data.getList({'id':assetId})
    except Exception as e:
        print(str(e))
        return

    if content == 0:
        # delete empty colletion and/or folder
        ee.data.deleteAsset(assetId)
    else:
        for asset in content:
            path = asset['id']
            ty = asset['type']
            if ty == 'Image':
                # print('deleting {}'.format(path))
                ee.data.deleteAsset(path)
            else:
                recrusive_delete_asset(path)
        # delete empty collection and/or folder
        ee.data.deleteAsset(assetId)

def get_projection(filename):
    ''' Get EPSG from a shapefile using ogr

    :param filename: an ESRI shapefile (.shp)
    :type filename: str
    '''
    try:
        from osgeo import ogr
    except:
        import ogr

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(filename)

    # from Layer
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()

    return spatialRef.GetAttrValue("AUTHORITY", 1)

def shp2collection(filename):
    ''' Convert an ESRI file (.shp and .dbf must be present) to a
    ee.FeatureCollection

    At the moment only works for shapes with less than 3000 records

    :param filename: the name of the filename. If the shape is not in the
        same path than the script, specify a path instead.
    :type filename: str
    :return: the FeatureCollection
    :rtype: ee.FeatureCollection
    '''
    wgs84 = ee.Projection('EPSG:4326')
    # read the filename
    reader = shapefile.Reader(filename)
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]
    field_types = [field[1] for field in fields]
    types = dict(zip(field_names, field_types))
    features = []
    for sr in reader.shapeRecords():
        # atr = dict(zip(field_names, sr.record))
        atr = {}
        for fld, rec in zip(field_names, sr.record):
            fld_type = types[fld]
            if fld_type == 'D':
                value = ee.Date(rec.isoformat()).millis().getInfo()
            elif fld_type in ['C', 'N', 'F']:
                value = rec
            else:
                continue
            atr[fld] = value
        geom = sr.shape.__geo_interface__
        geometry = ee.Geometry(geom, 'EPSG:' + get_projection(filename))\
                     .transform(wgs84, 1)
        feat = ee.Feature(geometry, atr)
        features.append(feat)

    return ee.FeatureCollection(features)