# coding=utf-8
"""legacy Module holding tools for ee.ImageCollections."""
import ee
from deprecated.sphinx import deprecated

import geetools  # noqa: F401


def fillWithLast(collection, reverse=False, proxy=-999):
    """Fill each masked pixels with the last available not masked pixel. If reverse, it goes backwards.

    Images must contain a valid date (system:time_start property by default)
    .
    """
    axis = 0

    def shift(array):
        if reverse:
            right = array.arraySlice(axis, 1)
            last = array.arraySlice(axis, -1)
            return right.arrayCat(last, axis)
        else:
            left = array.arraySlice(axis, 0, -1)
            first = array.arraySlice(axis, 0, 1)
            return first.arrayCat(left, axis)

    def move(array):
        shifted = shift(array)
        masked = array.neq(proxy)
        maskednot = array.eq(proxy)
        t1 = array.multiply(masked)
        t2 = shifted.multiply(maskednot)
        final = t1.add(t2)
        return final

    def fill(array, size):
        size = ee.Number(size)
        indices = ee.List.sequence(0, size.subtract(1))

        def wrap(i, a):
            a = ee.Image(a)
            return move(a)

        return ee.Image(indices.iterate(wrap, array))

    collection = collection.map(
        lambda i: image_module.emptyBackground(i, proxy).copyProperties(
            source=i, properties=i.propertyNames()
        )
    )
    bands = ee.Image(collection.first()).bandNames()
    size = collection.size()
    array = collection.toArray()
    fill_array = fill(array, size)

    props = aggregate_array_all(collection)
    indices = ee.List.sequence(0, size.subtract(1))

    def wrap(index):
        index = ee.Number(index).toInt()
        sliced = fill_array.arraySlice(axis, index, index.add(1))
        im = sliced.arrayProject([1]).arrayFlatten([bands])
        prop = ee.Dictionary(props.get(index))
        im = ee.Image(im.setMulti(prop))
        return im.updateMask(im.neq(proxy))

    return ee.ImageCollection.fromImages(indices.map(wrap))


def mosaicSameDay(collection, qualityBand=None):
    """Return a collection where images from the same day are mosaicked.

    :param qualityBand: the band that holds the quality score for mosaiking.
        If None it will use the simpler mosaic() function
    :type qualityBand: str
    :return: a new image collection with 1 image per day. The only property
        kept is `system:time_start`
    :rtype: ee.ImageCollection
    """
    all_dates = collection.aggregate_array("system:time_start")

    def overdates(d, l):
        l = ee.List(l)
        date = ee.Date(d)
        day = date.get("day")
        month = date.get("month")
        year = date.get("year")
        clean_date = ee.Date.fromYMD(year, month, day)
        condition = l.contains(clean_date)
        return ee.Algorithms.If(condition, l, l.add(clean_date))

    date_list = ee.List(all_dates.iterate(overdates, ee.List([])))
    first_img = ee.Image(collection.first())
    bands = first_img.bandNames()

    def make_col(date):
        date = ee.Date(date)
        filtered = collection.filterDate(date, date.advance(1, "day"))

        if qualityBand:
            mosaic = filtered.qualityMosaic(qualityBand)
        else:
            mosaic = filtered.mosaic()

        mosaic = mosaic.set(
            "system:time_start",
            date.millis(),
            "system:footprint",
            mergeGeometries(filtered),
        )

        # mosaic = mosaic.rename(bands)
        mosaic = mosaic.select(bands)

        def reproject(bname, mos):
            mos = ee.Image(mos)
            mos_bnames = mos.bandNames()
            bname = ee.String(bname)
            proj = first_img.select(bname).projection()

            newmos = ee.Image(
                ee.Algorithms.If(
                    mos_bnames.contains(bname),
                    image_module.replace(mos, bname, mos.select(bname).setDefaultProjection(proj)),
                    mos,
                )
            )

            return newmos

        mosaic = ee.Image(bands.iterate(reproject, mosaic))
        return mosaic

    new_col = ee.ImageCollection.fromImages(date_list.map(make_col))
    return new_col


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead.")
def reduceEqualInterval(
    collection, interval=30, unit="day", reducer=None, start_date=None, end_date=None
):
    """Reduce an ImageCollection into a new one that has one image per reduced interval."""
    return ee.ImageCollection(collection).geetools.reduceInterval(reducer, unit, interval)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.groupInterval instead.")
def makeEqualInterval(collection, interval=1, unit="month"):
    """Make a list of image collections filtered by the given interval."""
    return ee.ImageCollection(collection).geetools.groupInterval(unit, interval)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.groupInterval instead..")
def makeDayIntervals(collection, interval=30, reverse=False, buffer="second"):
    """Make day intervals."""
    return ee.ImageCollection(collection).geetools.groupInterval("day", 1)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead.")
def reduceDayIntervals(collection, reducer, interval=30, reverse=False, buffer="second"):
    """Reduce Day Intervals."""
    return ee.ImageCollection(collection).geetools.reduceInterval(reducer, "day", 1)


@deprecated(version="1.4.0", reason="Removed from the lib as untested")
def linearFunctionBand(*args, **kwargs):
    """Apply a linear function over the bands across every image of the ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested")
def linearFunctionProperty(*args, **kwargs):
    """Apply a linear function over the properties across every image of the ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def linearInterpolation(collection, date_property="system:time_start"):
    """TODO missing docstring."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def gaussFunctionBand(*args, **kwargs):
    """Compute a Gauss function using a specified band over an ImageCollection, See: https://en.wikipedia.org/wiki/Gaussian_function."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def gaussFunctionProperty(*args, **kwargs):
    """Compute a Gauss function using a specified property over an ImageCollection."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def normalDistributionProperty(*args, **kwargs):
    """Compute a normal distribution using a specified property, over an ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def normalDistributionBand(collection, band, mean=None, std=None, name="normal_distribution"):
    """Compute a normal distribution using a specified band, over an ImageCollection."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


def moving_average(collection, back=5, reducer=None, use_original=True):
    """Compute the moving average over a time series.

    :param back: number of images back to use for computing the stats
    :type back: int
    :param reducer: the reducer to apply. Default is ee.Reducer.mean()
    :type reducer: ee.Reducer
    :param use_original: if True, computes the stats over the last original
        values, otherwise, computes the stats over the last computed values
    :type use_original: bool
    """
    if reducer is None:
        reducer = ee.Reducer.mean()

    def wrap(i, d):
        d = ee.Dictionary(d)
        i = ee.Image(i)
        original = ee.List(d.get("original"))
        ee.List(d.get("stats"))

        def true(im, di):
            original_true = ee.List(di.get("original"))
            stats_true = ee.List(di.get("stats"))
            original_true = original_true.add(im)
            tocompute = original_true if use_original else stats_true.add(im)
            tempcol = ee.ImageCollection.fromImages(tocompute.slice(back * -1))
            stats = tempcol.reduce(reducer)
            stats = stats.rename(im.bandNames())
            stats = ee.Image(stats.copyProperties(im, properties=im.propertyNames()))
            return ee.Dictionary({"original": original_true, "stats": stats_true.add(stats)})

        def false(im, di):
            original2 = ee.List(di.get("original"))
            ee.List(di.get("stats"))
            condition2 = original2.size().gt(0)

            def true2(ima, dic):
                original_true2 = ee.List(dic.get("original"))
                original_true2 = original_true2.add(ima)
                stats_true2 = ee.List(dic.get("stats"))
                tocompute = original_true2 if use_original else stats_true2.add(ima)
                tempcol2 = ee.ImageCollection.fromImages(tocompute)
                stats2 = tempcol2.reduce(reducer)
                stats2 = stats2.rename(ima.bandNames())
                stats2 = ee.Image(stats2.copyProperties(ima, properties=ima.propertyNames()))
                return ee.Dictionary({"original": original_true2, "stats": stats_true2.add(stats2)})

            def false2(ima, dic):
                # first element
                original_false2 = ee.List(dic.get("original"))
                stats_false2 = ee.List(dic.get("stats"))
                return ee.Dictionary(
                    {
                        "original": original_false2.add(ima),
                        "stats": stats_false2.add(ima),
                    }
                )

            return ee.Dictionary(ee.Algorithms.If(condition2, true2(im, di), false2(im, di)))

        condition = original.size().gte(back)
        return ee.Dictionary(ee.Algorithms.If(condition, true(i, d), false(i, d)))

    final = ee.Dictionary(collection.iterate(wrap, ee.Dictionary({"original": [], "stats": []})))
    return ee.ImageCollection.fromImages(ee.List(final.get("stats")))
