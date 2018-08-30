# coding=utf-8
""" Module holding tools for ee.Date """
import ee
if not ee.data._initialized:
    ee.Initialize()

from datetime import datetime, timedelta

EE_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


def to_datetime(date):
    """ convert a `ee.Date` into a `datetime` object """
    formatted = date.format('yyyy,MM,dd,HH,mm,ss').getInfo()
    args = formatted.split(',')
    intargs = [int(arg) for arg in args]
    return datetime(*intargs)


def millis2datetime(millis):
    """ Converts milliseconds from 1970-01-01T00:00:00 to a
    datetime object """
    seconds = millis/1000
    dt = timedelta(seconds=seconds)
    return EE_EPOCH + dt
