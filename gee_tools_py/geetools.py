# -*- coding: utf-8 -*-
"""
This file contains a bunch of useful functions to use in Google Earth Engine
"""
import time
import traceback

import ee

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

TYPES = {'float': ee.Image.toFloat,
         'int': ee.Image.toInt,
         'Uint8': ee.Image.toUint8,
         'int8': ee.Image.toInt8,
         'double': ee.Image.toDouble}

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
    value = ee.Image(number).toFloat()

    def mapping(img):
        mask = img.mask()
        test = mask.Not()
        return img.where(test, value)

    return mapping


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

        from geetools import addConstantBands
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
    band = band.select([0], [to_replace])
    resto = bands.remove(to_replace)
    img_resto = img.select(resto)
    img_final = img_resto.addBands(band)
    return img_final


def get_value(img, point, scale=10):
    """ Return the value of all bands of the image in the specified point

    :param img: Image to get the info from
    :type img: ee.Image
    :param point: Point from where to get the info
    :type point: ee.Geometry.Point
    :param scale: The scale to use in the reducer. It defaults to 10 due to the
        minimum scale available in EE (Sentinel 10m)
    :type scale: int
    :return: Values of all bands in the ponit
    :rtype: dict
    """
    scale = int(scale)
    type = point.getInfo()["type"]
    if type != "Point":
        raise ValueError("Point must be ee.Geometry.Point")

    return img.reduceRegion(ee.Reducer.first(), point, scale).getInfo()


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
    :param bands: names of the bands to be added
    :type bands: tuple
    :return: The function to use in ee.ImageCollection.map()
    :rtype: function
    """
    def wrap(image):
        if bands is None:
            bn = image.bandNames()
        else:
            bn = ee.List(list(bands))

        nim = ee.Image(0).select([0], [name])

        # TODO: check if passed band names are in band names
        def sumBandas(n, ini):
            return ee.Image(ini).add(image.select([n]))

        newimg = ee.Image(bn.iterate(sumBandas, nim))

        return image.addBands(newimg)
    return wrap


def replace_many(listEE, replace):
    """ Replace elements of a Earth Engine List object

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

        imagen = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013344LGN00")
        p = ee.Geometry.Point(-71.72029495239258, -42.78997046797438)

        i = rename_bands({"B1":"BLUE", "B2":"GREEN"})(imagen)

        print get_value(imagen, p)
        print get_value(i, p)

    >> {u'B1': 0.10094200074672699, u'B2': 0.07873955368995667, u'B3': 0.057160500437021255}
    >> {u'BLUE': 0.10094200074672699, u'GREEN': 0.07873955368995667, u'B3': 0.057160500437021255}
    """
    def wrap(img):
        bandnames = img.bandNames()
        newnames = replace_many(bandnames, names)
        return img.select(bandnames, newnames)
    return wrap