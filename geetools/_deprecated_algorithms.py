# coding=utf-8
"""Module holding misc algorithms."""

import ee
import ee.data
from deprecated.sphinx import deprecated


@deprecated(version="1.4.0", reason="Use ee.Image.geetools.distanceToMask instead.")
def distanceToMask(
    image,
    mask,
    kernel=None,
    radius=1000,
    unit="meters",
    scale=None,
    geometry=None,
    band_name="distance_to_mask",
    normalize=False,
):
    """Compute the distance to the mask in meters."""
    return (
        ee.Image(image)
        .geetools.distanceToMask(mask, radius=radius, band_name=band_name)
        .select(band_name)
    )


@deprecated(version="1.5.0", reason="Use ee.Image.geetools.maskCover instead.")
def maskCover(
    image,
    geometry=None,
    scale=None,
    property_name="MASK_COVER",
    crs=None,
    crsTransform=None,
    bestEffort=False,
    maxPixels=1e13,
    tileScale=1,
):
    """Percentage of masked pixels (masked/total * 100) as an Image property."""
    return ee.Image(image).geetools.maskCover()


@deprecated(version="1.5.0", reason="Use ee.Image.geetools.distance instead.")
def euclideanDistance(image1, image2, bands=None, discard_zeros=False, name="distance"):
    """Compute the Euclidean distance between two images."""
    return ee.Image(image1).geetools.distance(image2)


@deprecated(version="1.4.0", reason="It's included in the ee_extra bindings.")
def pansharpenKernel(image, pan, rgb=None, kernel=None):
    """Compute the per-pixel means of the unsharpened bands."""
    raise NotImplementedError("This function is deprecated. Use the one in ee_extra.")


@deprecated(version="1.4.0", reason="It's included in the ee_extra bindings.")
def pansharpenIhsFusion(image, pan=None, rgb=None):
    """HSV-based Pan-Sharpening."""
    raise NotImplementedError("This function is deprecated. Use the one in ee_extra.")
