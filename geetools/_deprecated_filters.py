"""Legacy filter methods."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Filter.dateRange instead")
def dateRange(range):
    """Filter by ``ee.DateRange``."""
    return ee.Filter.geetools.dateRange(range)
