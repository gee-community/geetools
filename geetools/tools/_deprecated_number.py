# coding=utf-8
"""Module holding tools for ee.Number."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Number.geetools.truncate instead")
def trimDecimals(number, places=2):
    """Decrease the number of decimals in a ee.Number."""
    return ee.Number(number).geetools.truncate(places)
