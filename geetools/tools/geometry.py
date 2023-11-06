# coding=utf-8
"""Module holding tools for ee.Geometry."""
import ee
import ee.data


def GeometryCollection_to_MultiPolygon(geom):
    """Convert a Geometry of type `GeometryCollection` into a Geometry of type.

    `MultiPolygon` which will include Polygons, MultiPolygons and LinearRings
    .
    """
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
    """Convert a Geometry of type `GeometryCollection` into a Geometry of type.

    `MultiLineString` which will include LineString and MultiLineString
    .
    """
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
    """Convert a Geometry of type `GeometryCollection` into a Geometry of type.

    `MultiPoint` which will include Point and MultiPoint
    .
    """
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
