"""Legacy tools for ``ee.Date``."""
from datetime import datetime

import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.toDateTime instead")
def toDatetime(date):
    """Convert from ee to ``datetime.datetime``."""
    return ee.Date(date).geetools.toDatetime()


@deprecated(version="1.0.0", reason="Epoch is the same for ee and python")
def millisToDatetime(millis):
    """Convert from milliseconds to ``datetime.datetime``."""
    return datetime.fromtimestamp(millis / 1000.0)


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
