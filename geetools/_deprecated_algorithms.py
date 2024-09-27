# coding=utf-8
"""Module holding misc algorithms."""

import ee
import ee.data
from deprecated.sphinx import deprecated

from . import tools


def distanceToMask(
    image,
    kernel=None,
    radius=1000,
    unit="meters",
    scale=None,
    geometry=None,
    band_name="distance_to_mask",
    normalize=False,
):
    """Compute the distance to the mask in meters.

    :param image: Image holding the mask
    :type image: ee.Image
    :param kernel: Kernel to use for computing the distance. By default uses
        euclidean
    :type kernel: ee.Kernel
    :param radius: radius for the kernel. Defaults to 1000
    :type radius: int
    :param unit: units for the kernel radius. Defaults to 'meters'
    :type unit: str
    :param scale: scale for reprojection. If None, will reproject on the fly
        (according to EE lazy computing)
    :type scale: int
    :param geometry: compute the distance only inside this geometry. If you
        want to compute the distance inside a clipped image, using this
        parameter will make the edges not be considered as a mask.
    :type geometry: ee.Geometry or ee.Feature
    :param band_name: name of the resulting band. Defaults to
        'distance_to_mask'
    :type band_name: str
    :param normalize: Normalize result (between 0 and 1)
    :type normalize: bool
    :return: A one band image with the distance to the mask
    :rtype: ee.Image
    """
    if not kernel:
        kernel = ee.Kernel.euclidean(radius, unit)

    # select first band
    image = image.select(0)

    # get mask
    mask = image.mask()
    inverse = mask.Not()

    if geometry:
        # manage geometry types
        if isinstance(geometry, (ee.Feature, ee.FeatureCollection)):
            geometry = geometry.geometry()

        inverse = inverse.clip(geometry)

    # Compute distance to the mask (inverse)
    distance = inverse.distance(kernel)

    if scale:
        proj = image.projection()
        distance = distance.reproject(proj.atScale(scale))

    # make mask to be the max distance
    dist_mask = distance.mask().Not().remap([0, 1], [0, radius])

    if geometry:
        dist_mask = dist_mask.clip(geometry)

    final = distance.unmask().add(dist_mask)

    if normalize:
        final = tools.image.parametrize(final, (0, radius), (0, 1))

    return final.rename(band_name)


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


def sumDistance(image, collection, bands=None, discard_zeros=False, name="sumdist"):
    """Compute de sum of all distances between the given image and the.

    collection passed.

    :param image:
    :param collection:
    :return:
    """
    condition = isinstance(collection, ee.ImageCollection)

    if condition:
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
