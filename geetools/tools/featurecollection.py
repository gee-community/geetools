# coding=utf-8
"""Module holding tools for ee.FeatueCollections."""
import ee

from . import collection as eecollection
from . import geometry as geometry_module


def clean(collection):
    """Convert Features that have a Geometry of type `GeometryCollection`.

    into the inner geometries
    .
    """
    withType = collection.map(
        lambda feat: feat.set("GTYPE", ee.String(feat.geometry().type()))
    )
    geomcol = withType.filter(ee.Filter.eq("GTYPE", "GeometryCollection"))
    notgeomcol = withType.filter(ee.Filter.neq("GTYPE", "GeometryCollection"))

    def wrap(feat, fc):
        feat = ee.Feature(feat)
        fc = ee.FeatureCollection(fc)
        newfc = geometry_module.GeometryCollection_to_FeatureCollection(feat)
        return fc.merge(newfc)

    newfc = ee.FeatureCollection(geomcol.iterate(wrap, ee.FeatureCollection([])))
    return notgeomcol.merge(newfc)


def enumerateProperty(col, name="enumeration"):
    """Create a list of lists in which each element of the list is.

    [index, element]. For example, if you parse a FeatureCollection with 3
    Features you'll get: [[0, feat0], [1, feat1], [2, feat2]].

    :param collection: the collection
    :return: ee.FeatureCollection
    """
    enumerated = eecollection.enumerate(col)

    def over_list(li):
        li = ee.List(li)
        index = ee.Number(li.get(0))
        element = li.get(1)
        return ee.Feature(element).set(name, index)

    featlist = enumerated.map(over_list)
    return ee.FeatureCollection(featlist)


def enumerateSimple(collection, name="ENUM"):
    """Simple enumeration of features inside a collection. Each feature stores.

    its enumeration, so if the order of features changes over time, the
    numbers will not be in order
    .
    """
    size = collection.size()
    collist = collection.toList(size)
    seq = ee.List.sequence(0, size.subtract(1))

    def wrap(n):
        n = ee.Number(n).toInt()
        feat = collist.get(n)
        return ee.Feature(feat).set(name, n)

    fc = ee.FeatureCollection(seq.map(wrap))

    return ee.FeatureCollection(fc.copyProperties(source=collection))
