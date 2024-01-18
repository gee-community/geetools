"""Module holding tools for ``ee.String``."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.String.geetools.eq instead")
def eq(string, other):
    """Compare two ee.String and return 1 if equal else 0."""
    return ee.String(string).geetools.eq(other)


@deprecated(version="1.0.0", reason="Use ee.List.geetools.product instead")
def mix(strings):
    """Mix a list of lists."""
    return ee.List(strings[0]).geetools.product(strings[1])


@deprecated(version="1.0.0", reason="Use ee.String.geetools.format instead")
def format(string, replacement):
    """Format a string using variables."""
    return ee.String(string).geetools.format(replacement)
