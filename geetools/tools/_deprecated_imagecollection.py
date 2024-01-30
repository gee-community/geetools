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


def containsAllBands(collection, bands):
    """Filter a collection with images containing all bands specified in.

    parameter `bands`
    .
    """
    bands = ee.List(bands)
    # add bands as metadata
    collection = collection.map(lambda i: ee.Image(i).set("_BANDS_", ee.Image(i).bandNames()))

    band0 = ee.String(bands.get(0))
    rest = ee.List(bands.slice(1))
    filt0 = ee.Filter.listContains(leftField="_BANDS_", rightValue=band0)

    # Get filter
    def wrap(band, filt):
        band = ee.String(band)
        filt = ee.Filter(filt)
        newfilt = ee.Filter.listContains(leftField="_BANDS_", rightValue=band)
        return ee.Filter.And(filt, newfilt)

    filt = ee.Filter(rest.iterate(wrap, filt0))
    return collection.filter(filt)


def containsAnyBand(collection, bands):
    """Filter a collection with images cotaining any of the bands specified in.

    parameter `bands`
    .
    """
    bands = ee.List(bands)
    # add bands as metadata
    collection = collection.map(lambda i: ee.Image(i).set("_BANDS_", ee.Image(i).bandNames()))

    band0 = ee.String(bands.get(0))
    rest = ee.List(bands.slice(1))
    filt0 = ee.Filter.listContains(leftField="_BANDS_", rightValue=band0)

    # Get filter
    def wrap(band, filt):
        band = ee.String(band)
        filt = ee.Filter(filt)
        newfilt = ee.Filter.listContains(leftField="_BANDS_", rightValue=band)
        return ee.Filter.Or(filt, newfilt)

    filt = ee.Filter(rest.iterate(wrap, filt0))
    return collection.filter(filt)


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


def enumerateProperty(collection, name="enumeration"):
    """Missing docstring.

    :param collection:
    :param name:
    :return:
    """
    enumerated = collection.enumerate(collection)

    def over_list(l):
        l = ee.List(l)
        index = ee.Number(l.get(0))
        element = l.get(1)
        return ee.Image(element).set(name, index)

    imlist = enumerated.map(over_list)
    return ee.ImageCollection(imlist)


def enumerateSimple(collection, name="ENUM"):
    """Simple enumeration of features inside a collection. Each feature stores.

    its enumeration, so if the order of features changes over time, the numbers
    will not be in order
    .
    """
    size = collection.size()
    collist = collection.toList(size)
    seq = ee.List.sequence(0, size.subtract(1))

    def wrap(n):
        n = ee.Number(n).toInt()
        feat = collist.get(n)
        return ee.Image(feat).set(name, n)

    fc = ee.ImageCollection.fromImages(seq.map(wrap))

    return ee.ImageCollection(fc.copyProperties(source=collection))


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


def getValues(
    collection,
    geometry,
    scale=None,
    reducer=None,
    id="system:index",
    properties=None,
    side="server",
    maxPixels=1e7,
    bestEffort=False,
    tileScale=1,
):
    """Return all values of all bands of an image collection in the.

        specified geometry.

    :param geometry: Point from where to get the info
    :type geometry: ee.Geometry
    :param scale: The scale to use in the reducer. It defaults to 10 due
        to the minimum scale available in EE (Sentinel 10m)
    :type scale: int
    :param id: image property that will be the key in the result dict
    :type id: str
    :param properties: image properties that will be added to the resulting
        dict
    :type properties: list
    :param side: 'server' or 'client' side
    :type side: str
    :return: Values of all bands in the point
    :rtype: dict
    """
    if reducer is None:
        reducer = ee.Reducer.mean()

    if not scale:
        scale = 1
    else:
        scale = int(scale)

    if not properties:
        properties = []
    properties = ee.List(properties)

    def listval(img, it):
        theid = ee.Algorithms.String(img.get(id))
        values = img.reduceRegion(
            reducer,
            geometry,
            scale,
            maxPixels=maxPixels,
            bestEffort=bestEffort,
            tileScale=tileScale,
        )
        values = ee.Dictionary(values)
        img_props = img.propertyNames()

        def add_properties(prop, ini):
            ini = ee.Dictionary(ini)
            condition = img_props.contains(prop)

            def true():
                value = img.get(prop)
                return ini.set(prop, value)

            return ee.Algorithms.If(condition, true(), ini)

        with_prop = ee.Dictionary(properties.iterate(add_properties, values))
        return ee.Dictionary(it).set(theid, with_prop)

    result = collection.iterate(listval, ee.Dictionary({}))
    result = ee.Dictionary(ee.Algorithms.If(collection.size().neq(0), result, {}))

    if side == "server":
        return result
    elif side == "client":
        return result.getInfo()
    else:
        raise ValueError("side parameter must be 'server' or 'client'")


@deprecated(version="1.0.0", reason="Use ee.ImageCollection.geetools.outliers instead")
def outliers(collection, bands, sigma=2, updateMask=False):
    """Compute outliers in the collection"""
    return ee.ImageCollection(collection).geetools.outliers(bands, sigma, updateMask)


@deprecated(version="1.0.0", reason="geetools will mostly focus on server-side methods now")
def data2pandas(data):
    """Convert data coming from tools.imagecollection.get_values to a pandas DataFrame."""
    raise NotImplementedError("geetools will mostly focus on server-side methods now")


def parametrizeProperty(
    collection, property, range_from, range_to, pattern="{property}_PARAMETRIZED"
):
    """Parametrize a property.

    :param collection: the ImageCollection
    :param range_from: the original property range
    :param range_to: the desired property range
    :param property: the name of the property
    :param pattern: the name of the resulting property. Wherever it says
        'property' will be replaced with the passed property.
    :return: the parsed collection in which every image has a new
        parametrized property
    """
    name = pattern.replace("{property}", property)

    original_range = range_from if isinstance(range_from, ee.List) else ee.List(range_from)

    final_range = range_to if isinstance(range_to, ee.List) else ee.List(range_to)

    # original min and max
    min0 = ee.Number(original_range.get(0))
    max0 = ee.Number(original_range.get(1))

    # range from min to max
    rango0 = max0.subtract(min0)

    # final min max images
    min1 = ee.Number(final_range.get(0))
    max1 = ee.Number(final_range.get(1))

    rango1 = max1.subtract(min1)

    def wrap(img):
        value = ee.Number(img.get(property))
        percent = value.subtract(min0).divide(rango0)
        final = percent.multiply(rango1).add(min1)
        return img.set(name, final)

    return collection.map(wrap)


def linearFunctionBand(
    collection,
    band,
    range_min=None,
    range_max=None,
    mean=None,
    output_min=None,
    output_max=None,
    name="linear_function",
):
    """Apply a linear function over the bands across every image of the.

    ImageCollection using the following formula:

    - a = abs(val-mean)
    - b = output_max-output_min
    - c = abs(range_max-mean)
    - d = abs(range_min-mean)
    - e = max(c, d)

    f(x) = a*(-1)*(b/e)+output_max

    :param band: the band to process
    :param range_min: the minimum pixel value in the parsed band. If None, it
        will be computed reducing the collection
    :param range_max: the maximum pixel value in the parsed band. If None, it
        will be computed reducing the collection
    :param output_min: the minimum value that will take the resulting band.
    :param output_max: the minimum value that will take the resulting band.
    :param mean: the value on the given range that will take the `output_max`
        value
    :param name: the name of the resulting band
    :return: the parsed collection in which every image will have an extra band
        that results of applying the linear function over every pixel in the
        image
    :rtype: ee.ImageCollection
    """
    if range_min is None:
        range_min = ee.Image(collection.select(band).min()).rename("imin")
    else:
        range_min = castImage(range_min)

    if range_max is None:
        range_max = ee.Image(collection.select(band).max()).rename("imax")
    else:
        range_max = castImage(range_max)

    def to_map(img):
        result = image_module.linearFunction(
            img, band, range_min, range_max, mean, output_min, output_max, name
        )
        return img.addBands(result.rename(name))

    collection = collection.map(to_map)

    return collection


def linearFunctionProperty(
    collection,
    property,
    range_min=None,
    range_max=None,
    mean=None,
    output_min=None,
    output_max=None,
    name="LINEAR_FUNCTION",
):
    """Apply a linear function over the properties across every image of the.

    ImageCollection using the following formula:

    - a = abs(val-mean)
    - b = output_max-output_min
    - c = abs(range_max-mean)
    - d = abs(range_min-mean)
    - e = max(c, d)

    f(x) = a*(-1)*(b/e)+output_max

    :param property: the property to process
    :param range_min: the minimum pixel value in the parsed band. If None, it
        will be computed reducing the collection
    :param range_max: the maximum pixel value in the parsed band. If None, it
        will be computed reducing the collection
    :param output_min: the minimum value that will take the resulting band.
    :param output_max: the minimum value that will take the resulting band.
    :param mean: the value on the given range that will take the `output_max`
        value
    :param name: the name of the resulting band
    :return: the parsed collection in which every image will have an extra
        property that results of applying the linear function over every pixel
        in the image
    :rtype: ee.ImageCollection
    """
    if range_min is None:
        imin = ee.Number(collection.aggregate_min(property))
    else:
        imin = ee.Number(range_min)

    if range_max is None:
        imax = ee.Number(collection.aggregate_max(property))
    else:
        imax = ee.Number(range_max)

    if mean is None:
        imean = imax
    else:
        imean = ee.Number(mean)

    if output_max is None:
        output_max = imax
    else:
        output_max = ee.Number(output_max)

    if output_min is None:
        output_min = imin
    else:
        output_min = ee.Number(output_min)

    a = imax.subtract(imean).abs()
    b = imin.subtract(imean).abs()
    t = a.max(b)

    def to_map(img):
        val = ee.Number(img.get(property))

        a = val.subtract(imean).abs().multiply(-1)
        b = output_max.subtract(output_min)
        c = b.divide(t)
        d = a.multiply(c)
        result = d.add(output_max)

        return img.set(name, result)

    collection = collection.map(to_map)

    return collection


def linearInterpolation(collection, date_property="system:time_start"):
    """TODO missing docstring."""

    def _addTime(collection):
        def wrap(i):
            sec = ee.Number(i.get(date_property))
            isec = image_module.empty(sec, i.bandNames())
            isec_suffix = image_module.addSuffix(isec, "_tmpTime")
            m = i.mask()
            isec_masked = isec.updateMask(m)
            isec_masked_suffix = image_module.addSuffix(isec_masked, "_maskedTime")
            return i.addBands(isec_suffix).addBands(isec_masked_suffix)

        return collection.map(wrap)

    # get the mask for the final result
    finalmask = allMasked(collection)

    if date_property != "system:time_start":
        collection = collection.sort(date_property)

    # add time bands
    collection = _addTime(collection)

    filled = fillWithLast(collection, False)
    filled_back = fillWithLast(collection, True)

    condition = ee.Filter.equals(leftField="system:index", rightField="system:index")

    match1 = ee.Join.saveFirst("filled").apply(
        primary=collection, secondary=filled, condition=condition
    )

    match2 = ee.Join.saveFirst("filled_back").apply(
        primary=match1, secondary=filled_back, condition=condition
    )

    def wrap(image):
        o = ee.Image(image)
        bands = o.bandNames()

        masked = o.mask().Not()
        f = ee.Image(image.get("filled")).unmask()
        fb = ee.Image(image.get("filled_back")).unmask()

        # filters
        filter0 = ee.Filter.stringContains("item", "maskedTime")
        filter1 = ee.Filter.stringContains("item", "maskedTime").Not()
        filter2 = ee.Filter.stringContains("item", "tmpTime").Not()

        # get all deltas (including delta x)
        dy = ee.Image(fb.subtract(f)).unmask()
        dx_bands = bands.filter(filter0)

        # select only delta x for each band
        dx = dy.select(dx_bands)

        # get original bands
        original_bands = bands.filter(filter1).filter(filter2)

        # get delta for original bands
        delta = dy.select(original_bands)

        # now that we have delta x and delta for the original bands
        # get the slope
        slope = delta.divide(dx).unmask()

        # filled original bands
        fos = f.select(original_bands)

        # filled back original bands
        fob = fb.select(original_bands)

        # original bands
        oo = o.select(original_bands)

        # masked original bands
        mo = masked.select(original_bands)

        t = o.select(".+_tmpTime").subtract(f.select(".+_maskedTime"))
        fill = fos.add(slope.multiply(t)).unmask()
        fill2 = fob.where(fill, fill)
        fill3 = fos.where(fill2, fill2)
        final = oo.unmask().where(mo, fill3)
        final = image_module.deleteProperties(final)
        final = (
            final.select(original_bands)
            .copyProperties(o, exclude=["filled", "filled_back"])
            .set(date_property, o.get(date_property))
            .set("system:index", o.get("system:index"))
        )
        return ee.Image(final).updateMask(finalmask)

    return ee.ImageCollection(match2.map(wrap))


def gaussFunctionBand(
    collection,
    band,
    range_min=None,
    range_max=None,
    mean=0,
    output_min=None,
    output_max=1,
    std=None,
    stretch=1,
    name="gauss",
):
    """Compute a Gauss function using a specified band over an.

        ImageCollection. See: https://en.wikipedia.org/wiki/Gaussian_function.

    :param band: the name of the band to use
    :type band: str
    :param range_min: the minimum pixel value in the parsed band. If None, it
        will be computed
    :param range_max: the maximum pixel value in the parsed band. If None, it
        will be computed
    :param mean: the position of the center of the peak. Defaults to 0
    :type mean: int or float
    :param std: the standard deviation value. Defaults to range/4
    :type std: int or float
    :param output_max: height of the curve's peak
    :type output_max: int or float
    :param output_min: the desired minimum of the curve
    :type output_min: int or float
    :param stretch: a stretching value. As bigger as stretch
    :type stretch: int or float
    :param name: the name of the resulting band
    :return: the parsed collection in which every image will have an extra band
        that results of applying the gauss function over every pixel in the
        image
    :rtype: ee.ImageCollection
    """
    if range_min is None:
        range_min = ee.Image(collection.min())
    else:
        range_min = castImage(range_min)

    if range_max is None:
        range_max = ee.Image(collection.max())
    else:
        range_max = castImage(range_max)

    def to_map(img):

        result = image_module.gaussFunction(
            img,
            band,
            range_min=range_min,
            range_max=range_max,
            mean=mean,
            std=std,
            output_min=output_min,
            output_max=output_max,
            stretch=stretch,
            name=name,
        )
        return img.addBands(result)

    collection = collection.map(to_map)

    return collection


def gaussFunctionProperty(
    collection,
    property,
    range_min=None,
    range_max=None,
    mean=0,
    output_min=None,
    output_max=1,
    std=None,
    stretch=1,
    name="GAUSS",
):
    """Compute a Gauss function using a specified property over an.

        ImageCollection. See: https://en.wikipedia.org/wiki/Gaussian_function.

    :param collection:
    :type collection: ee.ImageCollection
    :param property: the name of the property to use
    :type property: str
    :param range_min: the minimum pixel value in the parsed band. If None, it
        will be computed
    :param range_max: the maximum pixel value in the parsed band. If None, it
        will be computed
    :param mean: the position of the center of the peak. Defaults to 0
    :type mean: int or float
    :param std: the standard deviation value. Defaults to range/4
    :type std: int or float
    :param output_max: height of the curve's peak
    :type output_max: int or float
    :param output_min: the desired minimum of the curve
    :type output_min: int or float
    :param stretch: a stretching value. As bigger as stretch
    :type stretch: int or float
    :param name: the name of the resulting property
    :return: the parsed collection in which every image will have an extra
        property that results of applying the linear function over every pixel
        in the image
    :rtype: ee.ImageCollection
    """
    if range_min is None:
        range_min = ee.Number(collection.aggregate_min(property))
    else:
        range_min = ee.Number(range_min)

    if range_max is None:
        range_max = ee.Number(collection.aggregate_max(property))
    else:
        range_max = ee.Number(range_max)

    mean = ee.Number(mean)
    output_max = ee.Number(output_max)
    if std is None:
        std = range_max.subtract(range_min).divide(4)
    else:
        std = ee.Number(std)
    stretch = ee.Number(stretch)

    def to_map(img):
        def compute_gauss(value):
            a = value.subtract(mean).pow(2)
            b = std.pow(2).multiply(-2)
            c = a.divide(b).multiply(stretch)
            d = c.exp()
            return d.multiply(output_max)

        no_parametrized = compute_gauss(ee.Number(img.get(property)))

        if output_min is None:
            return img.set(name, no_parametrized)
        else:
            min_result = compute_gauss(range_min)
            max_result = compute_gauss(range_max)
            min_result_final = min_result.min(max_result)
            e = no_parametrized.subtract(min_result_final)
            f = output_max.subtract(min_result_final)
            g = output_max.subtract(output_min)
            parametrized = e.divide(f).multiply(g).add(output_min)
            return img.set(name, parametrized)

    collection = collection.map(to_map)

    return collection


def normalDistributionProperty(
    collection, property, mean=None, std=None, name="NORMAL_DISTRIBUTION"
):
    """Compute a normal distribution using a specified property, over an.

    ImageCollection. For more see:
    https://en.wikipedia.org/wiki/Normal_distribution.

    :param property: the name of the property to use
    :type property: str
    :param mean: the mean value. If None it will be computed from the source.
        defaults to None.
    :type mean: float
    :param std: the standard deviation value. If None it will be computed from
        the source. Defaults to None.
    :type std: float
    """
    if mean is None:
        imean = ee.Number(collection.aggregate_mean(property))
    else:
        imean = ee.Number(mean)

    if std is None:
        istd = ee.Number(collection.aggregate_total_sd(property))
    else:
        istd = ee.Number(std)

    imax = ee.Number(1).divide(istd.multiply(ee.Number(2).multiply(math.pi).sqrt()))

    return gaussFunctionProperty(
        collection, property, mean=imean, output_max=imax, std=istd, name=name
    )


def normalDistributionBand(collection, band, mean=None, std=None, name="normal_distribution"):
    """Compute a normal distribution using a specified band, over an.

    ImageCollection. For more see:
    https://en.wikipedia.org/wiki/Normal_distribution.

    :param band: the name of the property to use
    :type band: str
    :param mean: the mean value. If None it will be computed from the source.
        defaults to None.
    :type mean: float
    :param std: the standard deviation value. If None it will be computed from
        the source. Defaults to None.
    :type std: float
    """
    if mean is None:
        imean = ee.Image(collection.mean())
    else:
        imean = ee.Image.constant(mean)

    if std is None:
        istd = ee.Image(collection.reduce(ee.Reducer.stdDev()))
    else:
        istd = ee.Image.constant(std)

    ipi = ee.Image.constant(math.pi)

    imax = ee.Image(1).divide(istd.multiply(ee.Image.constant(2).multiply(ipi).sqrt()))

    return gaussFunctionBand(collection, band, mean=imean, output_max=imax, std=istd, name=name)


def maskedSize(collection):
    """Return an image with the percentage of masked pixels. 100% means all.

    pixels are masked
    .
    """
    mask = collection.map(lambda i: i.mask().Not())

    def wrap(i):
        onemore = i.add(1)
        return onemore.divide(onemore)

    total = mask.map(wrap)
    masksum = mask.sum()
    totalsum = total.sum()
    return masksum.divide(totalsum).multiply(100).toInt()


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


def aggregate_array_all(collection):
    """Aggregate array in all images and return a list of dicts."""
    props = collection.first().propertyNames()
    allprops = props.map(lambda p: collection.aggregate_array(p))
    transposed = ee_list.transpose(allprops)
    return transposed.map(lambda ps: ee.Dictionary.fromLists(props, ps))


@deprecated(version="1.0.0", reason="Use vanilla ee.ImageCollection.toBands instead")
def toBands(collection):
    """Convert an ImageCollection into an Image"""
    return ee.Image(collection.toBands())
