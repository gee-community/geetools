"""Legacy ``ee.Collection`` methods."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use map without indices instead.")
def enumerate(collection):
    """Create a list of lists in which each element of the list is: [index, element]."""
    raise NotImplementedError("Use map without indices instead.")


@deprecated(version="1.0.0", reason="Use map ee.join.byProperty instead.")
def joinByProperty(primary, secondary, field, outer=False):
    return ee.Join.geetools.byProperty(primary, secondary, field, outer)
