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


def isUnbounded(geometry):
    """ Check if the geometry is unbounded using the module's definition of
    unboundness. It's a client-side function. For server-side function use

    `ee.Geometry.isUnbounded()`
    """
    bounds = geometry.getInfo()['coordinates']
    check1 = bounds == UNBOUNDED
    check2 = bounds == UNBOUNDED_2

    if (check1 or check2):
        return True
    else:
        return False

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

    # Geometry
    if isinstance(eeobject, ee.Geometry):
        geometry = eeobject.bounds() if bounds else eeobject
        region = dispatch(geometry)
    # Feature and Image
    elif isinstance(eeobject, (ee.Feature, ee.Image)):
        geometry = eeobject.geometry().bounds() if bounds else eeobject.geometry()
        region = dispatch(geometry)
    # FeatureCollection and ImageCollection
    elif isinstance(eeobject, (ee.FeatureCollection, ee.ImageCollection)):
        if bounds:
            geometry = eeobject.geometry().bounds()
        else:
            geometry = eeobject.geometry().dissolve()
        region = dispatch(geometry)
    # List
    elif isinstance(eeobject, list):
        condition = all([type(item) == list for item in eeobject])
        if condition:
            region = eeobject
    else:
        region = eeobject

    return region
