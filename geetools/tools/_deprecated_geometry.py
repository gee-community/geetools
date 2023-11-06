"""Legacy tools for ``ee.Geometry``."""
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Geometry.isUnbounded instead")
def isUnbounded(geometry):
    """Check if the geometry is unbounded."""
    return bool(geometry.isUnbounded().getInfo())
