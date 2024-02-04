"""Legacy tools for ``ee.Date``."""
from datetime import datetime

import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.toDatetime instead")
def toDatetime(date):
    """Convert from ee to ``datetime.datetime``."""
    return ee.Date(date).geetools.to_datetime()


@deprecated(version="1.0.0", reason="Epoch is the same for ee and python")
def millisToDatetime(millis):
    """Convert from milliseconds to ``datetime.datetime``."""
    return datetime.utcfromtimestamp(millis / 1000.0)


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.getUnitSinceEpoch instead")
def unitSinceEpoch(date, unit="day"):
    """Get the number of units since epoch (1970-01-01)."""
    return ee.Date(date).geetools.getUnitSinceEpoch(unit)


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.fromEpoch instead")
def dateSinceEpoch(date, unit="day"):
    """Get the date for the specified date in unit.."""
    return ee.Date.geetools.fromEpoch(date, unit)


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.fromDOY instead")
def fromDOY(year, doy):
    """Get the date from year and day of year."""
    return ee.Date.geetools.fromDOY(year, doy)


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.isLeap instead")
def isLeap(date):
    """Check if a date is leap."""
    return ee.Date(date).geetools.isLeap()


@deprecated(version="1.0.0", reason="Use ee.DateRange.geetools.split instead")
def daterangeList(start, end, interval, unit):
    """Divide a range that goes from start_date to end_date into many."""
    return ee.DateRange(start, end).geetools.split(interval, unit)


@deprecated(version="1.0.0", reason="Use ee.DateRange.geetools.split instead")
def daterangeIntervals(
    start,
    end,
    interval=1,
    unit="month",
    date_range=(1, 1),
    date_range_unit="day",
    direction="backward",
):
    """Divide a range that goes from start_date to end_date into many."""
    return ee.DateRange(start, end).geetools.split(interval, unit)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.addDate instead")
def makeDateBand(image, format="YMMdd", bandname="date"):
    """Add a band name to the image."""
    return ee.Image(image).geetools.addDate()
