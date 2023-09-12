import ee

from .geometry import *


def GeometryCollection_to_FeatureCollection(feature):
    """Convert a Feature with a Geometry of type `GeometryCollection`
    into a `FeatureCollection`
    .
    """
    geom = feature.geometry()
    geom.geometries()
    features = ee.List([])

    poly = GeometryCollection_to_MultiPolygon(geom)
    features = ee.List(
        ee.Algorithms.If(
            poly.coordinates().size().gt(0),
            features.add(feature.setGeometry(poly)),
            features,
        )
    )

    point = GeometryCollection_to_MultiPoint(geom)
    features = ee.List(
        ee.Algorithms.If(
            point.coordinates().size().gt(0),
            features.add(feature.setGeometry(point)),
            features,
        )
    )

    ls = GeometryCollection_to_MultiLineString(geom)
    features = ee.List(
        ee.Algorithms.If(
            ls.coordinates().size().gt(0),
            features.add(feature.setGeometry(ls)),
            features,
        )
    )

    return ee.FeatureCollection(features)
