# coding=utf-8
""" Module holding tools for ee.Geometry """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


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