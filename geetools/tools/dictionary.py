# coding=utf-8
""" Module holding tools for ee.ImageCollections and ee.FeatueCollections """
import ee
import ee.data
from collections import OrderedDict


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


def extractList(dict, list):
    """ Extract values from a list of keys """
    empty = ee.List([])
    list = ee.List(list)
    dict = ee.Dictionary(dict)
    def iteration(el, first):
        f = ee.List(first)
        cond = dict.contains(el)
        return ee.Algorithms.If(cond, f.add(dict.get(el)), f)
    values = ee.List(list.iterate(iteration, empty))
    return values