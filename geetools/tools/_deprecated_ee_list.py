"""Legacy tools for the ee.List class."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.List.geetools.complement instead")
def difference(list1, list2):
    """Return the difference between two lists."""
    return ee.List(list1).geetools.complement(list2)


@deprecated(version="1.0.0", reason="Use ee.List.geetools.product instead")
def intersection(list1, list2):
    """Return the intersection between two lists."""
    return ee.List(list1).geetools.intersection(list2)
