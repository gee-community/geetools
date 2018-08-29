# coding=utf-8
""" Module holding tools for ee.Date """

import ee
from datetime import datetime, timedelta

class Date(ee.ee_date.Date):

    epoch = datetime(1970, 1, 1, 0, 0, 0)

    def __init__(self, date):
        if isinstance(date, ee.Date):
            date = date.millis()
        super(Date, self).__init__(date)

    def to_datetime(self):
        """ convert a `ee.Date` into a `datetime` object"""
        formatted = self.format('yyyy,MM,dd,HH,mm,ss').getInfo()
        args = formatted.split(',')
        intargs = [int(arg) for arg in args]
        return datetime(*intargs)

    @staticmethod
    def millis2datetime(millis):
        """ Converts milliseconds from 1970-01-01T00:00:00 to a
        datetime object """
        seconds = millis/1000
        dt = timedelta(seconds=seconds)
        return Date.epoch + dt
