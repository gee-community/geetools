# coding=utf-8
""" Module holding tools for ee.Date """
import ee
from datetime import datetime, timedelta

EE_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


def toDatetime(date):
    """ convert a `ee.Date` into a `datetime` object """
    formatted = date.format('yyyy,MM,dd,HH,mm,ss').getInfo()
    args = formatted.split(',')
    intargs = [int(arg) for arg in args]
    return datetime(*intargs)


def millisToDatetime(millis):
    """ Converts milliseconds from 1970-01-01T00:00:00 to a
    datetime object """
    seconds = millis/1000
    dt = timedelta(seconds=seconds)
    return EE_EPOCH + dt


def daterangeList(start_date, end_date, interval=1, unit='month'):
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
    units = ['year', 'month', 'week', 'day', 'hour', 'minute', 'second']
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


def daterangeIntervals(start_date, end_date, interval=1, unit='month',
                       date_range=(1, 1), date_range_unit='day',
                       direction='backward'):
    """ Make Date Ranges in equal intervals

    :param interval: the amount of the interval in `unit`
    :param unit: the unit of the interval
    :param date_range: the amount of `date_range_unit` to go
        backwards (item 0) and forward (item 1)
    :param date_range_unit: the unit for date_range
    :param direction: the direction to advance
    """
    start_date = ee.Date(start_date)
    end_date = ee.Date(end_date)
    amplitude = end_date.difference(start_date, unit).round()
    intervals = amplitude.divide(interval).toInt()
    proxy = ee.List.sequence(0, intervals)

    if direction == 'forward':
        dates = proxy.map(
            lambda i: start_date.advance(
                ee.Number(i).multiply(interval), unit))
    else:
        dates = proxy.map(
            lambda i: end_date.advance(
                ee.Number(i).multiply(-interval), unit))

    def make_drange(date):
        date = ee.Date(date)
        return ee.DateRange(
            date.advance(-date_range[0], date_range_unit),
            date.advance(date_range[1], date_range_unit))

    return dates.map(lambda d: make_drange(d))


def unitSinceEpoch(date, unit='day'):
    """ Return the number of units since the epoch (1970-1-1)

    :param date: the date
    :type date: ee.Date
    :param unit: one of 'year', 'month' 'week', 'day', 'hour', 'minute',
        or 'second'
    :return: the corresponding units from the epoch
    :rtype: ee.Number
    """
    epoch = ee.Date(EE_EPOCH.isoformat())
    return date.difference(epoch, unit).toInt()


def getDateBand(img, unit='day', bandname='date', property_name=None):
    """ Get a date band from an image representing units since epoch

    :param img: the Image
    :param unit: one of 'year', 'month' 'week', 'day', 'hour', 'minute',
        or 'second'
    :param bandname: the name of the resulting band
    :return: a single band image with the date as the value for each pixel
        and also as an attribute
    :rtype: ee.Image
    """
    date = img.date()
    diff = unitSinceEpoch(date, unit)
    datei = ee.Image.constant(diff).rename(bandname)
    if not property_name:
        property_name = '{}_since_epoch'.format(unit)

    datei_attr = datei.set(property_name, diff).toInt()

    return datei_attr.copyProperties(img, ['system:footprint'])


def makeDateBand(image, format='YMMdd', bandname='date'):
    """ Make a date band using a formatter. Format pattern:

    C       century of era (>=0)         number        20
    Y       year of era (>=0)            year          1996

    x       weekyear                     year          1996
    w       week of weekyear             number        8
    ww      week of weekyear             number        08
    e       day of week                  number        2
    ee      day of week                  number        02

    y       year                         year          1996
    D       day of year                  number        5
    DD      day of year                  number        05
    DDD     day of year                  number        005
    M       month of year                month         7
    MM      month of year                month         07
    d       day of month                 number        5
    dd      day of month                 number        05

    K       hour of halfday (0~11)       number        0
    h       clockhour of halfday (1~12)  number        12

    H       hour of day (0~23)           number        0
    k       clockhour of day (1~24)      number        24
    m       minute of hour               number        30
    s       second of minute             number        55
    S       fraction of second           number        978
    """
    f = ee.String(format)
    # catch string formats for month
    pattern = f.replace('(MMM+)', 'MM')

    idate = image.date().format(pattern)
    idate_number = ee.Number.parse(idate)
    return ee.Image.constant(idate_number).rename(bandname)


def regularIntervals(start_date, end_date, interval=1, unit='month',
                     date_range=(1, 1), date_range_unit='day',
                     direction='backward'):
    """ Make date ranges at regular intervals

    :param start_date: if `direction` is forward the intervals will
        start from this date
    :type start_date: str or ee.Date
    :param end_date: if `direction` is backward the intervals will
        start from this date
    :type end_date: str or ee.Date
    :param interval: the interval
    :type interval: int
    :param unit: the unit for the interval
    :type unit: str
    :param date_range: the interval for the date range. It has to be a
        tuple or list in which the first item is for going backwards in
        `date_range_unit` and the second item for going forward
    :type date_range: tuple or list
    :param date_range_unit: the unit for each date range
    :type date_range_unit: str
    :param direction: it can be 'forward' or 'backward'
    :type direction: str
    :return: a list of date ranges
    :rtype: ee.List
    """
    start_date = ee.Date(start_date)
    end_date = ee.Date(end_date)
    amplitude = end_date.difference(start_date, unit).round()
    intervals = amplitude.divide(interval).toInt()
    proxy = ee.List.sequence(0, intervals)

    if direction == 'forward':
        dates = proxy.map(lambda i: start_date.advance(ee.Number(i).multiply(interval), unit))
    else:
        dates = proxy.map(lambda i: end_date.advance(ee.Number(i).multiply(-interval), unit))

    def make_drange(date):
        date = ee.Date(date)
        return ee.DateRange(date.advance(-date_range[0], date_range_unit),
                            date.advance(date_range[1], date_range_unit))

    return dates.map(lambda d: make_drange(d))


def dateSinceEpoch(date, unit='day'):
    """ Get the date for the specified date in unit

    :param date: the date in the specified unit
    :type date: int
    :param unit: one of 'year', 'month' 'week', 'day', 'hour', 'minute',
        or 'second'
    :return: the corresponding date
    :rtype: ee.Date
    """
    epoch = ee.Date(EE_EPOCH.isoformat())
    return epoch.advance(date, unit)