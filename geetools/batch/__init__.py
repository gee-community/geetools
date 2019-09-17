# coding=utf-8

from . import featurecollection, imagecollection, utils
from . import image as batchimage
import ee


class Export(ee.batch.Export):
    class table(ee.batch.Export.table):
        toAsset = featurecollection.toAsset

    class imagecollection(object):
        toDrive = imagecollection.toDrive
        toAsset = imagecollection.toAsset

    class image(ee.batch.Export.image):
        toAsset = batchimage.toAsset  # overwrite original
        toDriveByFeature = batchimage.toDriveByFeature


class Download(object):
    class table(object):
        toGeoJSON = featurecollection.toGeoJSON
        toCSV = featurecollection.toCSV
        toLocal = featurecollection.toLocal

    class imagecollection(object):
        toQGIS = imagecollection.toQGIS

    class image(object):
        toLocal = batchimage.toLocal
        toQGIS = batchimage.toQGIS


class Convert(object):
    class table(object):
        toDict = featurecollection.toDict

    class imagecollection(object):
        pass

    class image(object):
        pass


class Import(object):
    class table(object):
        fromGeoJSON = featurecollection.fromGeoJSON
        fromShapefile = featurecollection.fromShapefile
        fromKML = featurecollection.fromKML

    class imagecollection(object):
        pass

    class image(object):
        pass