# coding=utf-8
"""
Set of custom filters for Google Earth Engine.
"""
from __future__ import print_function
import ee

import ee.data
if not ee.data._initialized: ee.Initialize()

def date_range(range):
    """ Filter by DateRange

    :param range: date range
    :type range: ee.DateRange
    :return: the filter to apply to a collection
    :rtype: ee.Filter
    """
    ini = range.start()
    end = range.end()
    return ee.Filter.date(ini, end)