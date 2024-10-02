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


def euclideanDistance(image1, image2, bands=None, discard_zeros=False, name="distance"):
    """Compute the Euclidean distance between two images. The image's bands.

    is the dimension of the arrays.

    :param image1:
    :type image1: ee.Image
    :param image2:
    :type image2: ee.Image
    :param bands: the bands that want to be computed
    :type bands: list
    :param discard_zeros: pixel values equal to zero will not count in the
        distance computation
    :type discard_zeros: bool
    :param name: the name of the resulting band
    :type name: str
    :return: a distance image
    :rtype: ee.Image
    """
    if not bands:
        bands = image1.bandNames()

    image1 = image1.select(bands)
    image2 = image2.select(bands)

    proxy = tools.image.empty(0, bands)
    image1 = proxy.where(image1.gt(0), image1)
    image2 = proxy.where(image2.gt(0), image2)

    if discard_zeros:
        # zeros
        zeros1 = image1.eq(0)
        zeros2 = image2.eq(0)

        # fill zeros with values from the other image
        image1 = image1.where(zeros1, image2)
        image2 = image2.where(zeros2, image1)

    a = image1.subtract(image2)
    b = a.pow(2)
    c = b.reduce("sum")
    d = c.sqrt()

    return d.rename(name)


@deprecated(
    version="1.4.0",
    reason="Should not be used as a wrapper as the method is too computational heavy.",
)
def sumDistance(image, collection, bands=None, discard_zeros=False, name="sumdist"):
    """Compute de sum of all distances between the given image and the collection passed."""
    collection = collection.toList(collection.size())
    accum = ee.Image(0).rename(name)

    def over_rest(im, ini):
        ini = ee.Image(ini)
        im = ee.Image(im)
        dist = ee.Image(euclideanDistance(image, im, bands, discard_zeros)).rename(name)
        return ini.add(dist)

    return ee.Image(collection.iterate(over_rest, accum))


@deprecated(version="1.4.0", reason="It's included in the ee_extra bindings.")
def pansharpenKernel(image, pan, rgb=None, kernel=None):
    """Compute the per-pixel means of the unsharpened bands."""
    raise NotImplementedError("This function is deprecated. Use the one in ee_extra.")


@deprecated(version="1.4.0", reason="It's included in the ee_extra bindings.")
def pansharpenIhsFusion(image, pan=None, rgb=None):
    """HSV-based Pan-Sharpening."""
    raise NotImplementedError("This function is deprecated. Use the one in ee_extra.")
