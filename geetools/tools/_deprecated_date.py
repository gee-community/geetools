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
