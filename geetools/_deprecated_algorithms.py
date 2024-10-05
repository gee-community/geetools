# coding=utf-8
"""Module holding misc algorithms."""

import ee
import ee.data
from deprecated.sphinx import deprecated

from . import tools


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
    """Percentage of masked pixels (masked/total * 100) as an Image property.

    :param image: ee.Image holding the mask. If the image has more than
        one band, the first one will be used
    :type image: ee.Image
    :param geometry: the value will be computed inside this geometry. If None,
        will use image boundaries. If unbounded the result will be 0
    :type geometry: ee.Geometry or ee.Feature
    :param scale: the scale of the mask
    :type scale: int
    :param property_name: the name of the resulting property
    :type property_name: str
    :return: The same parsed image with a new property holding the mask cover
        percentage
    :rtype: ee.Image
    """
    # keep only first band
    imageband = image.select(0)

    # get projection
    projection = imageband.projection()

    if not scale:
        scale = projection.nominalScale()

    # get band name
    band = ee.String(imageband.bandNames().get(0))

    # Make an image with all ones
    ones_i = ee.Image.constant(1).reproject(projection).rename(band)

    if not geometry:
        geometry = image.geometry()

    # manage geometry types
    if isinstance(geometry, (ee.Feature, ee.FeatureCollection)):
        geometry = geometry.geometry()

    unbounded = geometry.isUnbounded()

    # Get total number of pixels
    ones = ones_i.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geometry,
        scale=scale,
        maxPixels=maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale,
    ).get(band)
    ones = ee.Number(ones)

    # select first band, unmask and get the inverse
    mask = imageband.mask()
    mask_not = mask.Not()
    image_to_compute = mask.updateMask(mask_not)

    # Get number of zeros in the given image
    zeros_in_mask = image_to_compute.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geometry,
        scale=scale,
        maxPixels=maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale,
    ).get(band)
    zeros_in_mask = ee.Number(zeros_in_mask)

    percentage = tools.trimDecimals(zeros_in_mask.divide(ones), 4)

    # Multiply by 100
    cover = percentage.multiply(100)

    # Return None if geometry is unbounded
    final = ee.Number(ee.Algorithms.If(unbounded, 0, cover))

    return image.set(property_name, final)


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
