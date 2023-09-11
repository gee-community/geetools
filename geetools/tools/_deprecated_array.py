"""Legacy array methods."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Array.geetools.full instead")
def constant2DArray(width, height, value):
    """Create an array of width x height with a fixed value."""
    return ee.Array.geetools.full(width, height, value)
