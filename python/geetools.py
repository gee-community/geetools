# -*- coding: utf-8 -*-
"""
This file contains a bunch of useful functions to use in Google Earth Engine
"""
import ee
ee.Initialize()

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


def downloadCol(col, folder, scale=30, maxImgs=100, dataType="float",
                region=None, **kwargs):
    """ Download all images from one collection. You can use the same arguments
    as the original function ee.batch.export.image.toDrive

    :param col: Collection to download
    :type col: ee.ImageCollection
    :param region: area to download. Defualt to the footprint of the first
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

if __name__ == "__main__":
    # DEBUGGING
    img = ee.Image("UMD/hansen/global_forest_change_2015_v1_3")
    fc = ee.FeatureCollection("ft:1oIKpRmlPWgmuLyuJ38drHnYt1h0JWBXGFDTjpq07").filterMetadata("id_ft2","less_than",6)
    exportByFeat(img, fc, "id_ft2", "Pruebas_geetools", scale=30)