# coding=utf-8
"""Module holding tools for ee.ImageCollections and ee.FeatueCollections."""

import ee
import ee.data


def extractList(dict, list):
    """Extract values from a list of keys."""
    empty = ee.List([])
    list = ee.List(list)
    dict = ee.Dictionary(dict)

    def iteration(el, first):
        f = ee.List(first)
        cond = dict.contains(el)
        return ee.Algorithms.If(cond, f.add(dict.get(el)), f)

    values = ee.List(list.iterate(iteration, empty))
    return values
