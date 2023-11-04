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


def paint(
    image,
    featurecollection,
    vis_params=None,
    color="black",
    width=1,
    fillColor=None,
    **kwargs
):
    """Paint a FeatureCollection onto an Image. Returns an Image with three.

    bands: vis-blue, vis-geen, vis-red (uint8).

    It admits the same parameters as ee.FeatureCollection.style
    """
    if not fillColor:
        fillColor = "#00000000"
    if not vis_params:
        firstband = ee.String(image.bandNames().get(0))
        vis_params = dict(bands=[firstband, firstband, firstband], min=0, max=1)
    region = image.geometry()
    filtered = ee.FeatureCollection(
        ee.Algorithms.If(
            region.isUnbounded(),
            featurecollection,
            featurecollection.filterBounds(region),
        )
    )
    fcraster = filtered.style(color=color, width=width, fillColor=fillColor, **kwargs)
    mask = fcraster.reduce("sum").gte(0).rename("mask")
    topaint = image.visualize(**vis_params)
    final = topaint.where(mask, fcraster)
    final = final.copyProperties(source=image)
    properties = image.propertyNames()
    final = ee.Image(
        ee.Algorithms.If(
            properties.contains("system:time_start"),
            final.set("system:time_start", image.date().millis()),
            final,
        )
    )
    final = ee.Image(
        ee.Algorithms.If(
            properties.contains("system:time_end"),
            final.set("system:time_end", ee.Number(image.get("system:time_end"))),
            final,
        )
    )

    return final


def repeatBand(image, times=None, names=None, properties=None):
    """Repeat one band. If the image parsed has more than one band, the first.

    will be used
    .
    """
    band = ee.Image(image.select([0]))
    if times is not None:
        times = ee.Number(times)
        proxylist = ee.List.repeat(0, times.subtract(1))

        def add(band, i):
            band = ee.Image(band)
            i = ee.Image(i)
            return i.addBands(band)

        proxyImg = proxylist.map(lambda n: band)
        repeated = ee.Image(proxyImg.iterate(add, band))
    else:
        newNames = ee.List(names)
        firstName = ee.String(newNames.get(0))
        rest = ee.List(newNames.slice(1))

        def add(name, i):
            name = ee.String(name)
            i = ee.Image(i)
            return i.addBands(band.rename(name))

        first = band.rename(firstName)
        repeated = ee.Image(rest.iterate(add, first))

    if properties:
        repeated = repeated.setMulti(properties)

    return ee.Image(repeated)


def arrayNonZeros(image):
    """Return an image array without zeros.

    :param image:
    :return:
    """

    def wrap(arr):
        binarr = arr.divide(arr)
        n = binarr.arrayReduce(ee.Reducer.sum(), [0]).multiply(-1)
        nimg = n.arrayProject([0]).arrayFlatten([["n"]]).toInt()
        sorted = arr.arraySort()
        sliced = sorted.arraySlice(0, nimg)
        return sliced

    bands = image.bandNames()
    first = wrap(image.select([bands.get(0)]))
    rest = bands.slice(1)

    def overBands(band, i):
        band = ee.String(band)
        i = ee.Image(i)
        array = wrap(image.select([band]))
        return i.addBands(array)

    result1 = ee.Image(rest.iterate(overBands, first))
    result2 = ee.Image(wrap(image))

    return ee.Image(ee.Algorithms.If(bands.size(), result1, result2))


class Classification(object):
    """Class holding (static) methods for classified images."""

    @staticmethod
    def vectorize(image, categories, label="label"):
        """Reduce to vectors the selected classes for a classified image.

        :param categories: the categories to vectorize
        :type categories: list

        """

        def over_cat(cat, ini):
            cat = ee.Number(cat)
            ini = ee.Image(ini)
            return ini.add(image.eq(cat).multiply(cat))

        filtered = ee.Image(
            ee.List(categories).iterate(over_cat, empty(0, [label]))  # noqa: F821
        )

        out = filtered.neq(0)
        filtered = filtered.updateMask(out)

        return filtered.reduceToVectors(
            **{"scale": 30, "maxPixels": 1e13, "labelProperty": label}
        )


# Create a lookup table to make sourceHist match targetHist.
def _lookup(sourceHist, targetHist):
    # Split the histograms by column and normalize the counts.
    sourceValues = sourceHist.slice(1, 0, 1).project([0])
    sourceCounts = sourceHist.slice(1, 1, 2).project([0])
    sourceCounts = sourceCounts.divide(sourceCounts.get([-1]))

    targetValues = targetHist.slice(1, 0, 1).project([0])
    targetCounts = targetHist.slice(1, 1, 2).project([0])
    targetCounts = targetCounts.divide(targetCounts.get([-1]))

    # Find first position in target where targetCount >= srcCount[i], for each i.
    lookup = sourceCounts.toList().map(
        lambda n: targetValues.get(targetCounts.gte(n).argmax())
    )
    return ee.Dictionary({"x": sourceValues.toList(), "y": lookup})


def histogramMatch(
    sourceImg, targetImg, geometry=None, scale=None, tiles=4, bestEffort=True
):
    """Histogram Matching. From https://medium.com/google-earth/histogram-matching-c7153c85066d."""
    if not geometry:
        geometry = sourceImg.geometry()

    bands = sourceImg.bandNames()

    args = dict(
        reducer=ee.Reducer.autoHistogram(maxBuckets=256, cumulative=True),
        geometry=geometry,
        scale=scale
        or 30,  # Need to specify a scale, but it doesn't matter what it is because bestEffort is true.
        maxPixels=65536 * tiles - 1,
        bestEffort=bestEffort,
    )

    # Only use pixels in target that have a value in source
    # (inside the footprint and unmasked).
    source = sourceImg.reduceRegion(**args)
    target = targetImg.updateMask(sourceImg.mask()).reduceRegion(**args)

    def interpolation(band):
        look = _lookup(source.getArray(band), target.getArray(band))
        x = ee.List(look.get("x"))
        y = ee.List(look.get("y"))
        return sourceImg.select([band]).interpolate(x, y)

    def iteration(band, i):
        interpolated = interpolation(band)
        return ee.Image.cat(i, interpolated)

    proxy = ee.Image()
    result = ee.Image(bands.iterate(iteration, proxy))
    return result.select(bands)
