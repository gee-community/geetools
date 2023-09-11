"""Module holding tools for ``ee.String``."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.String.geetools.eq instead")
def eq(string, other):
    """Compare two ee.String and return 1 if equal else 0."""
    return ee.String(string).geetools.eq(other)
