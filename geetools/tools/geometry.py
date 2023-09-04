# coding=utf-8
""" Module holding tools for ee.Geometry """
import ee
import ee.data


UNBOUNDED = [
    [[-180.0, -90.0], [180.0, -90.0], [180.0, 90.0], [-180.0, 90.0], [-180.0, -90.0]]
]

UNBOUNDED_2 = [[[None, None], [None, None], [None, None], [None, None], [None, None]]]


def isUnbounded(geometry):
    """Check if the geometry is unbounded using the module's definition of
    unboundness. It's a client-side function. For server-side function use

    `ee.Geometry.isUnbounded()`
    """
    bounds = geometry.getInfo()["coordinates"]
    check1 = bounds == UNBOUNDED
    check2 = bounds == UNBOUNDED_2

    if check1 or check2:
        return True
    else:
        return False


UNBOUNDED = [
    [[-180.0, -90.0], [180.0, -90.0], [180.0, 90.0], [-180.0, 90.0], [-180.0, -90.0]]
]

UNBOUNDED_2 = [[[None, None], [None, None], [None, None], [None, None], [None, None]]]


def isUnbounded(geometry):
    """Check if the geometry is unbounded using the module's definition of
    unboundness. It's a client-side function. For server-side function use

    `ee.Geometry.isUnbounded()`
    """
    bounds = geometry.getInfo()["coordinates"]
    check1 = bounds == UNBOUNDED
    check2 = bounds == UNBOUNDED_2

    if check1 or check2:
        return True
    else:
        return False


def unpack(iterable):
    """Helper function to unpack an iterable"""
    unpacked = []
    for tt in iterable:
        for t in tt:
            unpacked.append(t)
    return unpacked


def getRegion(eeobject, bounds=False, error=1):
    """Gets the region of a given geometry to use in exporting tasks. The
    argument can be a Geometry, Feature or Image

    :param eeobject: geometry to get region of
    :type eeobject: ee.Feature, ee.Geometry, ee.Image
    :param error: error parameter of ee.Element.geometry
    :return: region coordinates ready to use in a client-side EE function
    :rtype: json
    """

    def dispatch(geometry):
        info = geometry.getInfo()
        geomtype = info["type"]
        if geomtype == "GeometryCollection":
            geometries = info["geometries"]
            region = []
            for geom in geometries:
                this_type = geom["type"]
                if this_type in ["Polygon", "Rectangle"]:
                    region.append(geom["coordinates"][0])
                elif this_type in ["MultiPolygon"]:
                    geometries2 = geom["coordinates"]
                    region.append(unpack(geometries2))

        elif geomtype == "MultiPolygon":
            subregion = info["coordinates"]
            region = unpack(subregion)
        else:
            region = info["coordinates"]

        return region

    # Geometry
    if isinstance(eeobject, ee.Geometry):
        geometry = eeobject.bounds() if bounds else eeobject
        region = dispatch(geometry)
    # Feature and Image
    elif isinstance(eeobject, (ee.Feature, ee.Image)):
        geometry = (
            eeobject.geometry(error).bounds() if bounds else eeobject.geometry(error)
        )
        region = dispatch(geometry)
    # FeatureCollection and ImageCollection
    elif isinstance(eeobject, (ee.FeatureCollection, ee.ImageCollection)):
        if bounds:
            geometry = eeobject.geometry(error).bounds()
        else:
            geometry = eeobject.geometry(error).dissolve()
        region = dispatch(geometry)
    # List
    elif isinstance(eeobject, list):
        condition = all([type(item) == list for item in eeobject])
        if condition:
            region = eeobject
    else:
        region = eeobject

    return region


def GeometryCollection_to_MultiPolygon(geom):
    """Convert a Geometry of type `GeometryCollection` into a Geometry of type
    `MultiPolygon` which will include Polygons, MultiPolygons and LinearRings"""
    geometries = ee.List(geom.geometries())  # list of dicts

    def over_geom(geomdict, polygons):
        geomdict = ee.Geometry(geomdict)
        polygons = ee.List(polygons)
        ty = ee.String(geomdict.type())
        coords = ee.List(geomdict.coordinates())
        isPolygon = ty.compareTo("Polygon").Not()
        isMulti = ty.compareTo("MultiPolygon").Not()
        isRing = ty.compareTo("LinearRing").Not()
        return ee.List(
            ee.Algorithms.If(
                isPolygon.Or(isRing),
                polygons.add(coords),
                ee.List(ee.Algorithms.If(isMulti, polygons.cat(coords), polygons)),
            )
        )

    geomlist = ee.List(geometries.iterate(over_geom, ee.List([])))
    multipol = ee.Geometry.MultiPolygon(geomlist)
    return multipol


def GeometryCollection_to_MultiLineString(geom):
    """Convert a Geometry of type `GeometryCollection` into a Geometry of type
    `MultiLineString` which will include LineString and MultiLineString"""
    geometries = ee.List(geom.geometries())  # list of dicts

    def over_geom(geomdict, strings):
        geomdict = ee.Geometry(geomdict)
        strings = ee.List(strings)
        ty = ee.String(geomdict.type())
        coords = ee.List(geomdict.coordinates())
        isLineString = ty.compareTo("LineString").Not()
        isMulti = ty.compareTo("MultiLineString").Not()
        return ee.List(
            ee.Algorithms.If(
                isLineString,
                strings.add(coords),
                ee.List(ee.Algorithms.If(isMulti, strings.cat(coords), strings)),
            )
        )

    geomlist = ee.List(geometries.iterate(over_geom, ee.List([])))
    multils = ee.Geometry.MultiLineString(geomlist)
    return multils


def GeometryCollection_to_MultiPoint(geom):
    """Convert a Geometry of type `GeometryCollection` into a Geometry of type
    `MultiPoint` which will include Point and MultiPoint"""
    geometries = ee.List(geom.geometries())  # list of dicts

    def over_geom(geomdict, points):
        geomdict = ee.Geometry(geomdict)
        points = ee.List(points)
        ty = ee.String(geomdict.type())
        coords = ee.List(geomdict.coordinates())
        isPoint = ty.compareTo("Point").Not()
        isMulti = ty.compareTo("MultiPoint").Not()
        return ee.List(
            ee.Algorithms.If(
                isPoint,
                points.add(coords),
                ee.List(ee.Algorithms.If(isMulti, points.cat(coords), points)),
            )
        )

    geomlist = ee.List(geometries.iterate(over_geom, ee.List([])))
    multip = ee.Geometry.MultiPoint(geomlist)
    return multip
