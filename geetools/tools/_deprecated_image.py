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


@deprecated(version="1.0.0", reason="Use ee.Image.addbands instead")
def replace(image, to_replace, to_add):
    """Replace bands in an image."""
    return ee.Image(image).addBands(to_add.rename(to_replace), overwrite=True)


@deprecated(version="1.0.0", reason="Too many use cases, use pure GEE instead")
def addConstantBands(image, value=None, *names, **pairs):
    """Add constant bands to an image."""
    names = ee.Dictionary({k: value for k in names}.update(**pairs))
    image = names.keys().iterate(
        lambda k, i: ee.Image(i).addBands(ee.Image.constant(names.get(k)).rename(k)),
        ee.Image(image),
    )
    return ee.Image(image)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.toGrid instead")
def toGrid(image, size=1, band=None, geometry=None):
    """Create a grid from pixels in an image. Results may depend on the image."""
    return ee.Image(image).geetools.toGrid(size, band, geometry)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.clipOnCollection instead")
def clipToCollection(image, featureCollection, keepFeatureProperties=True):
    """Clip an image using each feature of a collection and return an. image collection."""
    return ee.Image(image).geetools.clipOnCollection(
        featureCollection, int(keepFeatureProperties)
    )
