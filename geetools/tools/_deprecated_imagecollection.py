# coding=utf-8
"""legacy Module holding tools for ee.ImageCollections."""
import ee
from deprecated.sphinx import deprecated

import geetools  # noqa: F401


@deprecated(version="1.0.0", reason="Use geetools.tools.imagecollection.append instead")
def add(collection, image):
    """Add an Image to the Collection."""
    return ee.ImageCollection(collection).geetools.append(image)


@deprecated(version="1.0.0", reason="Use geetools.tools.imagecollection.collectionMask instead")
def allMasked(collection):
    """Get a mask which indicates pixels that are masked in all images (0) from the others"""
    return ee.ImageCollection(collection).geetools.collectionMask()


@deprecated(version="1.0.0", reason="Use ee.imageCollection.geetools.containsAllBands instead")
def containsAllBands(collection, bands):
    """Filter a collection with images containing all the specified bands"""
    return ee.ImageCollection(collection).geetools.containsAllBands(bands)


@deprecated(version="1.0.0", reason="Use ee.imageCollection.geetools.containsAnyBands instead")
def containsAnyBand(collection, bands):
    """Filter a collection with images cotaining any of the specified bands"""
    return ee.ImageCollection(collection).geetools.containsAnyBands(bands)


@deprecated(version="1.0.0", reason="It is error prone as some collection have no ID.")
def getId(collection):
    """Get the ID of an ImageCollection."""
    raise NotImplementedError("It is error prone as some collection have no ID.")


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.iloc instead")
def getImage(collection, index):
    """Get an Image using its collection index."""
    return ee.ImageCollection(collection).geetools.iloc(index)


@deprecated(version="1.0.0", reason="Underefficient, use the vanilla map method instead")
def wrapper(f, *arg, **kwargs):
    """Wrap a function and its arguments into a mapping function for ImageCollection"""
    raise NotImplementedError("Underefficient, use the vanilla map method instead")


@deprecated(
    version="1.0.0",
    reason="Bad practice, Use vanilla mapping function instead of indexing imageCollection.",
)
def enumerateProperty(collection, name="enumeration"):
    """add an enumeration property to a imagecollection"""
    raise NotImplementedError(
        "Bad practice, Use vanilla mapping function instead of indexing imageCollection."
    )


@deprecated(
    version="1.0.0",
    reason="Bad practice, Use vanilla mapping function instead of indexing featureCollections.",
)
def enumerateSimple(collection, name="ENUM"):
    """Add an enumeration property to a featureCollection"""
    raise NotImplementedError(
        "Bad practice, Use vanilla mapping function instead of indexing featureCollections."
    )


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


@deprecated(version="1.0.0", reason="Use vanilla ee.ImageCollection.geometry instead")
def mergeGeometries(collection):
    """Merge the geometries of many images. Return ee.Geometry."""
    return ee.ImageCollection(collection).geometry()


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


def reduceEqualInterval(
    collection, interval=30, unit="day", reducer=None, start_date=None, end_date=None
):
    """Reduce an ImageCollection into a new one that has one image per.

        reduced interval, for example, one image per month.

    :param collection: the collection
    :type collection: ee.ImageCollection
    :param interval: the interval to reduce
    :type interval: int
    :param unit: unit of the interval. Can be 'day', 'month', 'year'
    :param reducer: the reducer to apply where images overlap. If None, uses
        a median reducer
    :type reducer: ee.Reducer
    :param start_date: fix the start date. If None, uses the date of the first
        image in the collection
    :type start_date: ee.Date
    :param end_date: fix the end date. If None, uses the date of the last image
        in the collection
    :type end_date: ee.Date
    :return:
    """
    interval = int(interval)  # force to int
    first = ee.Image(collection.sort("system:time_start").first())
    bands = first.bandNames()

    if not start_date:
        start_date = first.date()
    if not end_date:
        last = ee.Image(collection.sort("system:time_start", False).first())
        end_date = last.date()
    if not reducer:
        reducer = ee.Reducer.median()

    def apply_reducer(red, col):
        return ee.Image(col.reduce(red))

    ranges = date.daterangeList(start_date, end_date, interval, unit)

    def over_ranges(drange, ini):
        ini = ee.List(ini)
        drange = ee.DateRange(drange)
        start = drange.start()
        end = drange.end()
        filtered = collection.filterDate(start, end)
        condition = ee.Number(filtered.size()).gt(0)

        def true():
            image = (
                apply_reducer(reducer, filtered)
                .set("system:time_start", end.millis())
                .set("reduced_from", start.format())
                .set("reduced_to", end.format())
            )
            # rename to original names
            image = image.select(image.bandNames(), bands)
            result = ini.add(image)
            return result

        return ee.List(ee.Algorithms.If(condition, true(), ini))

    imlist = ee.List(ranges.iterate(over_ranges, ee.List([])))

    return ee.ImageCollection.fromImages(imlist)


def makeEqualInterval(collection, interval=1, unit="month"):
    """Make a list of image collections filtered by the given interval.

    for example, one month. Starts from the end of the parsed collection.

    :param collection: the collection
    :type collection: ee.ImageCollection
    :param interval: the interval
    :type interval: int
    :param unit: unit of the interval. Can be 'day', 'month', 'year'
    :rtype: ee.List
    """
    interval = int(interval)  # force to int
    collist = collection.sort("system:time_start").toList(collection.size())
    start_date = ee.Image(collist.get(0)).date()
    end_date = ee.Image(collist.get(-1)).date()

    ranges = date.daterangeList(start_date, end_date, interval, unit)

    def over_ranges(drange, ini):
        ini = ee.List(ini)
        drange = ee.DateRange(drange)
        start = drange.start()
        end = drange.end()
        filtered = collection.filterDate(start, end)
        condition = ee.Number(filtered.size()).gt(0)
        return ee.List(ee.Algorithms.If(condition, ini.add(filtered), ini))

    imlist = ee.List(ranges.iterate(over_ranges, ee.List([])))

    return imlist


def makeDayIntervals(collection, interval=30, reverse=False, buffer="second"):
    """Make day intervals."""
    interval = int(interval)
    collection = collection.sort("system:time_start", True)
    start = collection.first().date()
    end = collection.sort("system:time_start", False).first().date()
    ranges = date.dayRangeIntervals(start, end, interval, reverse, buffer)

    def over_ranges(drange, ini):
        ini = ee.List(ini)
        drange = ee.DateRange(drange)
        start = drange.start()
        end = drange.end()
        filtered = collection.filterDate(start, end)
        condition = ee.Number(filtered.size()).gt(0)
        return ee.List(ee.Algorithms.If(condition, ini.add(filtered), ini))

    imlist = ee.List(ranges.iterate(over_ranges, ee.List([])))

    return imlist


def reduceDayIntervals(collection, reducer, interval=30, reverse=False, buffer="second"):
    """Reduce Day Intervals.

    :param reducer: a function that takes as only argument a collection
        and returns an image
    :type reducer: function
    :return: an image collection
    :rtype: ee.ImageCollection
    """
    intervals = makeDayIntervals(collection, interval, reverse, buffer)
    reduced = intervals.map(reducer)
    return ee.ImageCollection.fromImages(reduced)


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.reduceRegions instead")
def getValues(*args, **kwargs):
    """Get values from an image collection in a geometry."""
    raise NotImplementedError("Use ee.ImageCollection.geetools.reduceRegions instead")


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.outliers instead")
def outliers(collection, bands, sigma=2, updateMask=False):
    """Compute outliers in the collection"""
    return ee.ImageCollection(collection).geetools.outliers(bands, sigma, updateMask)


@deprecated(version="1.0.0", reason="geetools will mostly focus on server-side methods now")
def data2pandas(data):
    """Convert data coming from tools.imagecollection.get_values to a pandas DataFrame."""
    raise NotImplementedError("geetools will mostly focus on server-side methods now")


@deprecated(
    version="1.0.0",
    reason="Use a mapping function with the ee.String.geetools.format method instead",
)
def parametrizeProperty(
    collection, property, range_from, range_to, pattern="{property}_PARAMETRIZED"
):
    """Parametrize a property."""
    raise NotImplementedError(
        "Use a mapping function with the ee.String.geetools.format method instead"
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested")
def linearFunctionBand(*args, **kwargs):
    """Apply a linear function over the bands across every image of the ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested")
def linearFunctionProperty(*args, **kwargs):
    """Apply a linear function over the properties across every image of the ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested.")
def linearInterpolation(collection, date_property="system:time_start"):
    """TODO missing docstring."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested.")
def gaussFunctionBand(*args, **kwargs):
    """Compute a Gauss function using a specified band over an ImageCollection, See: https://en.wikipedia.org/wiki/Gaussian_function."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested.")
def gaussFunctionProperty(*args, **kwargs):
    """Compute a Gauss function using a specified property over an ImageCollection."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested.")
def normalDistributionProperty(*args, **kwargs):
    """Compute a normal distribution using a specified property, over an ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Removed from the lib as untested.")
def normalDistributionBand(collection, band, mean=None, std=None, name="normal_distribution"):
    """Compute a normal distribution using a specified band, over an ImageCollection."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.validPixels instead")
def maskedSize(collection):
    """Return an image with the percentage of masked pixels"""
    valid = ee.ImageCollection(collection).geetools.validPixel().select("pct_valid")
    return ee.Image(100).subtract(valid)


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.integral instead")
def area_under_curve(collection, band, x_property="system:time_start", name="under_curve"):
    """Compute the area under the curve taking the x axis from an image property."""
    return ee.ImageCollection(collection).geetools.integral(band, x_property).rename(name)


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


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.aggregate_array instead")
def aggregate_array_all(collection):
    """Aggregate array in all images and return a list of dicts."""
    dict = collection.geetools.aggregateArray()
    keys = dict.keys()
    imageIndex = ee.List.sequence(0, collection.size().subtract(1))

    def transpose(index):
        i = ee.Number(index)
        values = keys.map(lambda k: ee.List(dict.get(k)).get(i))
        return ee.Dictionary.fromLists(keys, values)

    return imageIndex.map(transpose)


@deprecated(version="1.0.0", reason="Use vanilla ee.ImageCollection.toBands instead")
def toBands(collection):
    """Convert an ImageCollection into an Image"""
    return ee.Image(collection.toBands())
