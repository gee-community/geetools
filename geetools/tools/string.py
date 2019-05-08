# coding=utf-8
""" Tools for Earth Engine ee.List objects """

import ee


def eq(string, to_compare):
    """ Compare two ee.String and return 1 if equal else 0 """
    string = ee.String(string)
    to_compare = ee.String(to_compare)
    return string.compareTo(to_compare).Not()