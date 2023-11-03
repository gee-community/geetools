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


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.bufferMask instead")
def bufferMask(image, radius, units="pixels"):
    """Buffer the mask of an image."""
    return ee.Image(image).geetools.bufferMask(radius, units)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.full instead")
def empty(value=[0], names=["constant"], from_dict=None):
    """Create a constant image with the given band names and value, and/or. from a dictionary of {name: value}."""
    if from_dict is not None:
        raise Exception(
            "from_dict is dropped as it can be done directly using ee.Image(from_dict.toImage())"
        )
    return ee.Image.geetools.full(value, names)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.fullLike instead")
def emptyCopy(image, emptyValue=0, copyProperties=None, keepMask=False, region=None):
    """Make an empty copy of the given image."""
    copyProperties = 1 if copyProperties else 0
    keepMask = 1 if keepMask else 0
    return ee.Image(image).geetools.fullLike(emptyValue, copyProperties, keepMask)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.reduceBands instead")
def sumBands(image, name="sum", bands=None):
    """Adds all *bands* values and puts the result on *name*."""
    return ee.Image(image).geetools.reduceBands("sum", bands, name)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.full instead and cast it manually")  # fmt: skip
def proxy(values=(0,), names=("constant",), types=("int8",)):
    """Create a proxy image with the given values, names and types."""
    return ee.Image.geetools.full(values, names)


@deprecated(version="1.0.0", reason="We abandoned this method as it's bad practice")
def maskCover(*args, **kwargs):
    """Compute the percentage of covered area and set it as a property."""
    raise Exception(
        "maskCover is deprecated as you should not set this percentage in the image properties. Simply do a double zonal statistic analysis if needed that's the same amount of parameters."
    )


@deprecated(version="1.0.0", reason="We abandoned this method as it's bad practice")
def regionCover(*args, **kwargs):
    """Compute de percentage of values greater than 1 in area and set it as a property."""
    raise Exception(
        "regionCover is deprecated as you should not set this percentage in the image properties. Simply do a zonal statistic analysis if needed that's the same amount of parameters."
    )


@deprecated(
    version="1.0.0", reason="Use ee.Image.updateMask(mask).Not() instead instead"
)
def applyMask(image, mask, bands=None, negative=True):
    """Apply a passed positive mask."""
    return ee.Image(image).updateMask(mask.Not())


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.negativeClip instead")
def maskInside(image, geometry):
    """Mask the image inside the geometry."""
    return ee.Image(image).geetools.negativeClip(geometry)
