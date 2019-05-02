# coding=utf-8
import unittest
import ee
from .. import tools
ee.Initialize()

class TestL4TOA(unittest.TestCase):
    def setUp(self):
        pass

    def test_to_datetime(self):
        pass

    def test_millis2datetime(self):
        pass

    def test_daterange_list(self):
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

        daterange_list = tools.date.daterange_list(start_date, end_date,
                                                   interval, unit)
        # self.assertEqual(expected, daterange_list)
        pass
