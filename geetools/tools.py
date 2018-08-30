# coding=utf-8
"""
This file contains a set of useful functions to use in Google Earth Engine
"""
from __future__ import print_function, absolute_import
import time
import traceback
import functools
import requests
import os
from collections import OrderedDict
import json
import multiprocessing
from . import tools_list, tools_image, tools_collection, tools_segmentation,\
              tools_dictionary, tools_number, batch

import ee
from ee import serializer, deserializer

import ee.data
if not ee.data._initialized: ee.Initialize()

_execli_trace = False
_execli_times = 10
_execli_wait = 0

# Imported Classes
Mapping = tools_image.Mapping
FeatureCollection = tools_collection.FeatureCollection
SNIC = tools_segmentation.SNIC

# batch functions
col2drive = batch.Collection.toDrive
col2asset = batch.Collection.toAsset
image2asset = batch.Image.toAsset
image2local = batch.Image.toLocal
exportByFeat = batch.Image.toDriveByFeat

# Image functions
empty_image = tools_image.empty
addConstantBands = tools_image.addConstantBands
addMultiBands = tools_image.addMultiBands
rename_bands = tools_image.renameDict
parametrize = tools_image.parametrize
minscale = tools_image.minscale
sumBands = tools_image.sumBands
replace = tools_image.replace
get_value = tools_image.get_value
compute_bits = tools_image.compute_bits
pass_prop = tools_image.passProperty

# ImageCollection functions
get_values = tools_collection.get_values
fill_with_last = tools_collection.fill_with_last

# FeatureCollection functions
shape2collection = FeatureCollection.fromShapefile

# List functions
get_from_dict = tools_list.get_from_dict
replace_many = tools_list.replace_many
difference = tools_list.difference
intersection = tools_list.intersection

# Number functions
trim_decimals = tools_number.trim_decimals

# Dictionary
sort_dict = tools_dictionary.sort


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

    def encode(self, cat):
        """ Given a category, return the encoded value (only) """
        info = self.info[cat]
        lshift = info['lshift']
        decoded = info['shifted']

        shifted = decoded<<lshift
        return shifted

    def encode_band(self, category, mask, name=None):
        """ Make an image in which all pixels have the value for the given
        category

        :param category: the category to encode
        :type category: str
        :param mask: the mask that indicates which pixels encode
        :type mask: ee.Image
        :param name: name of the resulting band. If None it'll be the same as
            'mask'
        :type name: str

        :return: A one band image
        :rtype: ee.Image
        """
        encoded = self.encode(category)

        if not name:
            name = mask.bandNames().get(0)

        image = empty_image(encoded, [name])
        return image.updateMask(mask)


    def encode_and(self, *args):
        """ decodes a comination of the given categories. returns a list of
        possible values """
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
        """ decodes a comination of the given categories. returns a list of
        possible values """
        first = args[0]
        values_first = self.encode_one(first)

        for cat in args[1:]:
            values = self.encode_one(cat)
            for value in values:
                if value not in values_first:
                    values_first.append(value)

        return values_first

    def encode_not(self, *args):
        """ Given a set of categories return a list of values that DO NOT
        match with any """
        result = []
        match = self.encode_or(*args)
        for bit in range(self.max):
            if bit not in match:
                result.append(bit)
        return result

    def encode_one(self, cat):
        """ Given a category, return a list of values that match it """
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
        """ given a value return a list with all categories """
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
        """ given a value and a category return True if the value includes
        that category, else False """
        encoded = self.decode(value)
        return category in encoded


class Execli(object):
    """ Class to hold the methods to retry calls to Earth Engine """
    TRACE = False
    TIMES = 5
    WAIT = 0
    ACTIVE = True

    def execli(self, function):
        """ This function tries to excecute a client side Earth Engine function
            and retry as many times as needed. It is meant to use in cases when you
            cannot access to the original function. See example.

        :param function: the function to call TIMES
        :return: the return of function
        """
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
    """ Saves any EE object to a file with extension .gee

        The file has to be opened with `eopen`
    """
    obj = serializer.encode(eeobject)

    path = path if path else os.getcwd()

    with open(os.path.join(path, filename+'.gee'), 'w') as js:
        json.dump(obj, js)

def eopen(file, path=None):
    """ Opens a files saved with `esave` method

    :return: the EE object """

    path = path if path else os.getcwd()

    try:
        with open(os.path.join(path, file), 'r') as gee:
            thefile = json.load(gee)
    except IOError:
        with open(os.path.join(path, file+'.gee'), 'r') as gee:
            thefile = json.load(gee)

    return deserializer.decode(thefile)


def get_projection(filename):
    """ Get EPSG from a shapefile using ogr

    :param filename: an ESRI shapefile (.shp)
    :type filename: str
    """
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
