# coding=utf-8
"""Tools for ee.Image."""
from __future__ import absolute_import

import ee
import ee.data

from ..utils import castImage
from . import ee_list


def parametrize(image, range_from, range_to, bands=None, drop=False):
    """Parametrize from a original **known** range to a fixed new range.

    :param range_from: Original range. example: (0, 5000)
    :type range_from: tuple
    :param range_to: Fixed new range. example: (500, 1000)
    :type range_to: tuple
    :param bands: bands to parametrize. If *None* all bands will be
        parametrized.
    :type bands: list
    :param drop: drop the bands that will not be parametrized
    :type drop: bool

    :return: the parsed image with the parsed bands parametrized
    :rtype: ee.Image
    """
    original_range = (
        range_from if isinstance(range_from, ee.List) else ee.List(range_from)
    )

    final_range = range_to if isinstance(range_to, ee.List) else ee.List(range_to)

    # original min and max
    min0 = ee.Image.constant(original_range.get(0))
    max0 = ee.Image.constant(original_range.get(1))

    # range from min to max
    rango0 = max0.subtract(min0)

    # final min max images
    min1 = ee.Image.constant(final_range.get(0))
    max1 = ee.Image.constant(final_range.get(1))

    # final range
    rango1 = max1.subtract(min1)

    # all bands
    all = image.bandNames()

    # bands to parametrize
    if bands:
        bands_ee = ee.List(bands)
    else:
        bands_ee = image.bandNames()

    inter = ee_list.intersection(bands_ee, all)
    diff = ee_list.difference(all, inter)
    image_ = image.select(inter)

    # Percentage corresponding to the actual value
    percent = image_.subtract(min0).divide(rango0)

    # Taking count of the percentage of the original value in the original
    # range compute the final value corresponding to the final range.
    # Percentage * final_range + final_min

    final = percent.multiply(rango1).add(min1)

    if not drop:
        # Add the rest of the bands (no parametrized)
        final = image.select(diff).addBands(final)

    # return passProperty(image, final, 'system:time_start')
    return ee.Image(final.copyProperties(source=image))


def linearFunction(
    image,
    band,
    range_min=None,
    range_max=None,
    mean=None,
    output_min=None,
    output_max=None,
    name="linear_function",
    region=None,
    scale=None,
    **kwargs
):
    """Apply a linear function over one image band using the following.

    formula:

    - a = abs(val-mean)
    - b = output_max-output_min
    - c = abs(range_max-mean)
    - d = abs(range_min-mean)
    - e = max(c, d)

    f(x) = a*(-1)*(b/e)+output_max

    :param band: the band to process
    :param range_min: the minimum pixel value in the parsed band. If None, it
        will be computed over the parsed region (heavy process that can fail)
    :param range_max: the maximum pixel value in the parsed band. If None, it
        will be computed over the parsed region (heavy process that can fail)
    :param output_min: the minimum value that will take the resulting band.
    :param output_max: the minimum value that will take the resulting band.
    :param mean: the value on the given range that will take the `output_max`
        value
    :param name: the name of the resulting band
    :param region: the region to reduce over if no `range_min` and/or no
        `range_max` has been parsed
    :param scale: the scale that will be use for reduction if no `range_min`
        and/or no `range_max` has been parsed
    :param kwargs: extra arguments for the reduction: crs, crsTransform,
        bestEffort, maxPixels, tileScale.
    :return: a one band image that results of applying the linear function
        over every pixel in the image
    :rtype: ee.Image
    """
    image = image.select(band)

    if not region:
        region = image.geometry()

    if not scale:
        scale = image.projection().nominalScale()

    if range_min is None and range_max is None:
        minmax = image.reduceRegion(
            reducer=ee.Reducer.minMax(), geometry=region, scale=scale, **kwargs
        )
        minname = "{}_min".format(band)
        maxname = "{}_max".format(band)

        imin = ee.Image.constant(minmax.get(minname))
        imax = ee.Image.constant(minmax.get(maxname))

    elif range_min is None:
        minmax = image.reduceRegion(
            reducer=ee.Reducer.min(), geometry=region, scale=scale, **kwargs
        )
        imin = ee.Image.constant(minmax.get(band))
        imax = castImage(range_max)

    elif range_max is None:
        minmax = image.reduceRegion(
            reducer=ee.Reducer.max(), geometry=region, scale=scale, **kwargs
        )
        imax = ee.Image.constant(minmax.get(band))
        imin = castImage(range_min)
    else:
        imax = castImage(range_max)
        imin = castImage(range_min)

    if mean is None:
        imean = imax
    else:
        imean = castImage(mean)

    if output_max is None:
        output_max = imax

    if output_min is None:
        output_min = imin

    a = imax.subtract(imean).abs()
    b = imin.subtract(imean).abs()
    t = a.max(b)

    result = ee.Image().expression(
        "abs(val-mean)*(-1)*((max-min)/t)+max",
        {
            "val": image,
            "mean": imean,
            "t": t,
            "imin": imin,
            "max": output_max,
            "min": output_min,
        },
    )

    return result.rename(name)
