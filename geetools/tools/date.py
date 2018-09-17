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


def daterange_list(start_date, end_date, interval=1, unit='month'):
    """ Divide a range that goes from start_date to end_date into many
        ee.DateRange, each one holding as many units as the interval.
        For example, for a range from

    :param start_date: the start date. For the second DateRange and the
        following, it'll be one second after the end of the previus DateRange
    :param end_date: the end date
    :param interval: range of the DateRange in units
    :param unit: can be 'year', 'month' 'week', 'day', 'hour', 'minute',
        or 'second'
    :return: a list holding ee.DateRange
    :rtype: list
    """
    units = ['year', 'month' 'week', 'day', 'hour', 'minute', 'second']
    if unit not in units:
        raise ValueError('unit param must be one of {}'.format(units))

    def callback(interval, unit):
        def wrap(n, ini):
            ini = ee.List(ini)
            last_range = ee.DateRange(ini.get(-1))
            last_date = last_range.end()
            next_date = last_date.advance(1, 'second')
            next_interval = next_date.advance(interval, unit)
            return ini.add(ee.DateRange(next_date, next_interval))
        return wrap

    total_days = end_date.difference(start_date, unit)
    total_dateranges = total_days.divide(interval).toInt()
    dateranges_list = ee.List.sequence(1, total_dateranges)

    # first daterange
    first = ee.DateRange(start_date, start_date.advance(interval, unit))

    return ee.List(dateranges_list.iterate(callback(interval, unit),
                                           ee.List([first])))