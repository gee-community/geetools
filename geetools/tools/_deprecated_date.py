"""Legacy tools for ``ee.Date``."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Date.geetools.toDateTime instead")
def toDatetime(date):
    """Convert from ee to ``datetime.datetime``."""
    return ee.Date(date).geetools.toDatetime()
