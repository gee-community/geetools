# -*- coding: utf-8 -*-
"""
This file contains a bunch of useful functions to use in Google Earth Engine
"""
import time
import traceback

import ee

TYPES = {'float': ee.Image.toFloat,
         'int': ee.Image.toInt,
         'Uint8': ee.Image.toUint8,
         'int8': ee.Image.toInt8,
         'double': ee.Image.toDouble}

_execli_trace = False
_execli_times = 10
_execli_wait = 0

# DECORATORS
def execli_deco(times=None, wait=None, trace=None):
    """ This is a decorating function to excecute a client side Earth Engine
    function and retry as many times as needed

    :Example:
    .. code:: python

        from geetools import execli_deco
        import ee
        ee.Initialize()

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
        print type(times)
        print type(wait)
        raise ValueError("'times' and 'wait' parameters must be numbers")

    def wrap(f):
        def wrapper(*args, **kwargs):
            r = range(times)
            for i in r:
                try:
                    result = f(*args, **kwargs)
                except Exception as e:
                    print "try n°", i, "ERROR:", e
                    if trace:
                        traceback.print_exc()
                    if i < r[-1] and wait > 0:
                        print "waiting {} seconds...".format(str(wait))
                        time.sleep(wait)
                    elif i == r[-1]:
                        raise RuntimeError("An error occured tring to excecute"\
                                           "the funcion '{0}'".format(f.__name__))
                else:
                    return result

        return wrapper
    return wrap


def execli(function, times=None, wait=None, trace=None):
    """ This function tries to excecute a client side Earth Engine function
    and retry as many times as needed

    :Example:
    .. code:: python

        from geetools import execli
        import ee
        ee.Initialize()

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
        print type(times)
        print type(wait)
        raise ValueError("'times' and 'wait' parameters must be numbers")

    def wrap(f):
        def wrapper(*args, **kwargs):
            r = range(times)
            for i in r:
                try:
                    result = f(*args, **kwargs)
                except Exception as e:
                    print "try n°", i, "ERROR:", e
                    if trace:
                        traceback.print_exc()
                    if i < r[-1] and wait > 0:
                        print "waiting {} seconds...".format(str(wait))
                        time.sleep(wait)
                    elif i == r[-1]:
                        raise RuntimeError("An error occured tring to excecute" \
                                           "the funcion '{0}'".format(f.__name__))
                else:
                    return result

        return wrapper
    return wrap(function)

# INITIALIZE EARTH ENGINE USING EXECLI FUNCTION
execli(ee.Initialize)()

def mask2zero(img):
    """ Converts masked pixels into zeros

    :param img: Image contained in the Collection
    :type img: ee.Image
    """
    theMask = img.mask()
    return theMask.where(1, img)


def mask2number(col, number):
    """ Converts masked pixels into the specified number in each image of
    the collection. As *number* has to be a float, the resulting Image will
    have all bands converted to Float.

    :param col: Collection that contains the images to process
    :type col: ee.ImageCollection
    :param number: number to fill masked pixels
    :type number: float
    :return: the Collection containing all images converted
    """
    # TODO: let the user choose the type of the output
    value = ee.Image(number).toFloat()

    def mapping(img):
        mask = img.mask()
        test = mask.Not()
        return img.where(test, value)

    return col.map(mapping)


@execli_deco()
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
            print "unknown property's type"
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
        print "exporting", finalname
        tasklist.append(task)

    return tasklist


@execli_deco()
def col2drive(col, folder, scale=30, maxImgs=100, dataType="float",
                region=None, **kwargs):
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
    alist = col.toList(maxImgs)
    size = alist.size().getInfo()
    tasklist = []

    if region is None:
        region = ee.Image(alist.get(0)).geometry().getInfo()["coordinates"]

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


@execli_deco()
def col2asset(col, assetPath, scale=30, maxImgs=100, region=None, **kwargs):
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
    alist = col.toList(maxImgs)
    size = alist.size().getInfo()
    tasklist = []

    if region is None:
        region = ee.Image(alist.get(0)).geometry().getInfo()["coordinates"]

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
