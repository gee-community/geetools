# coding=utf-8
""" Module holding tools for ee.ImageCollections and ee.FeatueCollections """
import ee
import ee.data
from collections import OrderedDict

if not ee.data._initialized:
    ee.Initialize()


def sort(dictionary):
    """ Sort a dictionary. Can be a `dict` or a `ee.Dictionary`

    :param dictionary: the dictionary to sort
    :type dictionary: dict or ee.Dictionary
    :rtype: OrderedDict or ee.Dictionary
    """
    if isinstance(dictionary, dict):
        sorted = OrderedDict()
        keys = list(dictionary.keys())
        keys.sort()
        for key in keys:
            sorted[key] = dictionary[key]
        return sorted
    elif isinstance(dictionary, ee.Dictionary):
        keys = dictionary.keys()
        ordered = keys.sort()

        def iteration(key, first):
            new = ee.Dictionary(first)
            val = dictionary.get(key)
            return new.set(key, val)

        return ee.Dictionary(ordered.iterate(iteration, ee.Dictionary()))
    else:
        return dictionary