# coding=utf-8
"""Module holding tools for ee.FeatueCollections."""
import ee

from . import collection as eecollection


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
