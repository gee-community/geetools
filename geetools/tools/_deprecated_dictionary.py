"""Legacy methods for the Dictionary class."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Dictionary.geetools.fromPairs instead")
def fromList(alist):
    """Create a ee.Dictionary from a list of [[key, val], [key2, val2]...]."""
    return ee.Dictionary.geetools.fromPairs(alist)
