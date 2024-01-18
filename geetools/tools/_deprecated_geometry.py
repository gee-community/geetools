"""Legacy tools for ``ee.Geometry``."""
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Geometry.isUnbounded instead")
def isUnbounded(geometry):
    """Check if the geometry is unbounded."""
    return bool(geometry.isUnbounded().getInfo())


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.geometry() instead")
def getRegion(eeobject, bounds=False, error=1):
    """Gets the region of a given geometry to use in exporting tasks."""
    return eeobject.geometry()


@deprecated(version="1.0.0", reason="Use ee.Geometry.geetools.keepType instead")
def GeometryCollection_to_MultiPolygon(geom):
    """Convert a `GeometryCollection` into a ``MultiPolygon``."""
    return geom.geetools.keepType("Polygon")


@deprecated(version="1.0.0", reason="Use ee.Geometry.geetools.keepType instead")
def GeometryCollection_to_MultiLineString(geom):
    """Convert a `GeometryCollection` into a ``MultiLineString``."""
    return geom.geetools.keepType("LineString")


@deprecated(version="1.0.0", reason="Use ee.Geometry.geetools.keepType instead")
def GeometryCollection_to_MultiPoint(geom):
    """Convert a `GeometryCollection` into a ``MultiPoint``."""
    return geom.geetools.keepType("Point")
