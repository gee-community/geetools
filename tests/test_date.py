# -*- coding: utf-8 -*-

import ee
ee.Initialize()
from geetools import tools


def test_daterange_list():
    start_date = ee.Date('2010-01-01')
    end_date = ee.Date('2015-01-01')
    unit = 'year'
    interval = 1

    expected = ee.List([
        ee.DateRange('2010-01-01', '2011-01-01'),
        ee.DateRange('2011-01-01', '2012-01-01'),
        ee.DateRange('2012-01-01', '2013-01-01'),
        ee.DateRange('2013-01-01', '2014-01-01'),
        ee.DateRange('2014-01-01', '2015-01-01')
    ])

    daterange_list = tools.date.daterangeList(start_date, end_date,
                                              interval, unit)

    assert expected == daterange_list
