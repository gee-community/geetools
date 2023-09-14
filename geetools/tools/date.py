# coding=utf-8
"""Module holding tools for ee.Date."""
from datetime import datetime

import ee

EE_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


def makeDateBand(image, format="YMMdd", bandname="date"):
    """Make a date band using a formatter. Format pattern.

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

    Use the image first band for setting the resulting band projection
    """
    f = ee.String(format)
    # catch string formats for month
    pattern = f.replace("(MMM+)", "MM")

    proj = image.select(0).projection()

    footprint = image.geometry()

    idate = image.date().format(pattern)
    idate_number = ee.Number.parse(idate)
    date_band = ee.Image.constant(idate_number).rename(bandname)
    date_band = date_band.toInt()  # force to be an Integer
    final = ee.Image(
        ee.Algorithms.If(footprint.isUnbounded(), date_band, date_band.clip(footprint))
    )

    return final.setDefaultProjection(proj)


def regularIntervals(
    start_date,
    end_date,
    interval=1,
    unit="month",
    date_range=(1, 1),
    date_range_unit="day",
    direction="backward",
):
    """Make date ranges at regular intervals.

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

    if direction == "forward":
        dates = proxy.map(
            lambda i: start_date.advance(ee.Number(i).multiply(interval), unit)
        )
    else:
        dates = proxy.map(
            lambda i: end_date.advance(ee.Number(i).multiply(-interval), unit)
        )

    def make_drange(date):
        date = ee.Date(date)
        return ee.DateRange(
            date.advance(-date_range[0], date_range_unit),
            date.advance(date_range[1], date_range_unit),
        )

    return dates.map(lambda d: make_drange(d))
