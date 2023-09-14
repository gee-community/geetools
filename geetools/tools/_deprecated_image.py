"""Legacy tools for the ee.Image class."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.addSuffix instead")
def addSuffix(image, suffix, bands=None):
    """Add a suffix to the selected bands of an image."""
    return ee.Image(image).geetools.addSuffix(suffix, bands)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.addPrefix instead")
def addPrefix(image, prefix, bands=None):
    """Add a prefix to the selected bands of the image."""
    return ee.Image(image).geetools.addPrefix(prefix, bands)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.getValues instead")
def getValue(image, point, scale=None):
    """Get the values of an image at a point."""
    scale = scale or 0
    return ee.Image(image).geetools.getValues(point, scale)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.minScale instead")
def minscale(image):
    """Get the minimum scale of an image."""
    return ee.Image(image).geetools.minScale()


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.merge instead")
def addMultiBands(imageList):
    """Merge images."""
    list = ee.List(imageList)
    return ee.Image(list.get(0)).geetools.merge(list.slice(1))


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.merge instead")
def mixBands(imageList):
    """Merge images."""
    list = ee.List(imageList)
    return ee.Image(list.get(0)).geetools.merge(list.slice(1))


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.rename instead")
def renameDict(image, names):
    """Renames bands of images using a dict."""
    return ee.Image(image).geetools.rename(names)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.remove instead")
def removeBands(image, bands):
    """Remove bands from an image."""
    return ee.Image(image).geetools.remove(bands)


@deprecated(
    version="1.0.0", reason="Use ee.Image.addbands instead with the overwrite parameter"
)
def replace(image, to_replace, to_add):
    """Replace bands in an image."""
    return ee.Image(image).addBands(to_add.rename(to_replace), overwrite=True)
