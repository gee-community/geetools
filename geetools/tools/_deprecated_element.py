"""EE Element. Common methods between Feature and Image."""
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Don't use this method it's considered bad practice.")
def fillNull(Element, proxy=-999):
    """Fill null values of an Element's properties with a proxy value."""
    raise NotImplementedError("This method is deprecated. Use ee.FeatureCollection.fill() instead")
