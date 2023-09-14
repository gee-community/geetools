"""Legacy tools for the ee.Image class."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.addSuffix instead")
def addSuffix(image, suffix, bands=None):
    """Add a suffix to the selected bands of an image."""
    return ee.Image(image).geetools.addSuffix(suffix, bands)
