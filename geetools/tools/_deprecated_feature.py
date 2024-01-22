"""Legacy ``ee.Feature`` methods."""
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Feature.geetools.toFeatureCollection instead")
def GeometryCollection_to_FeatureCollection(feature):
    """Convert a Feature with a Geometry of type `GeometryCollection` into a `FeatureCollection`."""
    return feature.geetools.toFeatureCollection()
