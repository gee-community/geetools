# coding=utf-8
""" Module holding tools for ee.Geometry """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


UNBOUNDED = [[[-180.0, -90.0], [180.0, -90.0],
              [180.0, 90.0], [-180.0, 90.0],
              [-180.0, -90.0]]]

UNBOUNDED_2 = [[[None, None], [None, None],
                [None, None], [None, None],
                [None, None]]]


def getRegion(eeobject, bounds=False):
    """ Gets the region of a given geometry to use in exporting tasks. The
    argument can be a Geometry, Feature or Image

    :param eeobject: geometry to get region of
    :type eeobject: ee.Feature, ee.Geometry, ee.Image
    :return: region coordinates ready to use in a client-side EE function
    :rtype: json
    """
    def dispatch(geometry):
        info = geometry.getInfo()
        geomtype = info['type']
        if geomtype == 'GeometryCollection':
            geometries = info['geometries']
            region = []
            for geom in geometries:
                this_type = geom['type']
                if this_type in ['Polygon', 'MultiPolygon', 'Rectangle']:
                    region.append(geom['coordinates'])
        else:
            region = info['coordinates']

        return region

    if isinstance(eeobject, ee.Geometry):
        geometry = eeobject.bounds() if bounds else eeobject
        region = dispatch(geometry)
    elif isinstance(eeobject, (ee.Feature, ee.Image,
                               ee.FeatureCollection, ee.ImageCollection)):
        geometry = eeobject.geometry().bounds() if bounds else eeobject.geometry()
        region = dispatch(geometry)
    elif isinstance(eeobject, list):
        condition = all([type(item) == list for item in eeobject])
        if condition:
            region = eeobject
    else:
        region = eeobject

    return region
