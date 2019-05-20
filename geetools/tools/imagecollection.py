# coding=utf-8
""" Module holding tools for ee.ImageCollections """
import ee
import ee.data
import pandas as pd
import math
from . import date
from . import image as image_module
from . import collection as eecollection
from ..utils import castImage


def add(collection, image):
    """ Add an Image to the Collection

    **SERVER SIDE**

    """
    # TODO: handle a list of images
    collist = collection.toList(collection.size())
    append = collist.add(image)
    return ee.ImageCollection.fromImages(append)


def getId(collection):
    """ Get the ImageCollection id.

    **CLIENT SIDE**

    :type collection: ee.ImageCollection
    :return: the collection's id
    :rtype: str
    """
    return collection.limit(0).getInfo()['id']


def wrapper(f, *arg, **kwargs):
    """ Wrap a function and its arguments into a mapping function for
    ImageCollections. The first parameter of the functions must be an Image,
    and it must return an Image.

    :param f: the function to be wrapped
    :type f: function
    :return: a function to use in ee.ImageCollection.map
    :rtype: function
    """
    def wrap(img):
        return f(img, *arg, **kwargs)
    return wrap


def enumerateProperty(collection, name='enumeration'):
    """

    :param collection:
    :param name:
    :return:
    """
    enumerated = eecollection.enumerate(collection)

    def over_list(l):
        l = ee.List(l)
        index = ee.Number(l.get(0))
        element = l.get(1)
        return ee.Image(element).set(name, index)

    imlist = enumerated.map(over_list)
    return ee.ImageCollection(imlist)


def fillWithLast(collection):
    """ Fill masked values of each image pixel with the last available
    value

    :param collection: the collection that holds the images that will be filled
    :type collection: ee.ImageCollection
    :rtype: ee.ImageCollection
    """

    new = collection.sort('system:time_start', True)
    collist = new.toList(new.size())
    first = ee.Image(collist.get(0)).unmask()
    rest = collist.slice(1)

    def wrap(img, ini):
        ini = ee.List(ini)
        img = ee.Image(img)
        last = ee.Image(ini.get(-1))
        mask = img.mask().Not()
        last_masked = last.updateMask(mask)
        last2add = last_masked.unmask()
        img2add = img.unmask()
        added = img2add.add(last2add) \
            .set('system:index', ee.String(img.id()))

        props = img.propertyNames()
        condition = props.contains('system:time_start')

        final = ee.Image(ee.Algorithms.If(condition,
                                          added.set('system:time_start',
                                                    img.date().millis()),
                                          added))

        return ini.add(final.copyProperties(img))

    newcol = ee.List(rest.iterate(wrap, ee.List([first])))
    return ee.ImageCollection.fromImages(newcol)


def mergeGeometries(collection):
    """ Merge the geometries of many images. Return ee.Geometry """
    imlist = collection.toList(collection.size())

    first = ee.Image(imlist.get(0))
    rest = imlist.slice(1)

    def wrap(img, ini):
        ini = ee.Geometry(ini)
        img = ee.Image(img)
        geom = img.geometry()
        union = geom.union(ini)
        return union.dissolve()

    return ee.Geometry(rest.iterate(wrap, first.geometry()))


def mosaicSameDay(collection, reducer=None):
    """ Return a collection where images from the same day are mosaicked

    :param reducer: the reducer to use for merging images from the same day.
        Defaults to 'first'
    :type reducer: ee.Reducer
    :return: a new image collection with 1 image per day. The only property
        kept is `system:time_start`
    :rtype: ee.ImageCollection
    """
    if reducer is None:
        reducer = ee.Reducer.mean()

    def make_date_list(img, l):
        l = ee.List(l)
        img = ee.Image(img)
        date = img.date()
        # make clean date
        day = date.get('day')
        month = date.get('month')
        year = date.get('year')
        clean_date = ee.Date.fromYMD(year, month, day)
        condition = l.contains(clean_date)

        return ee.Algorithms.If(condition, l, l.add(clean_date))

    col_list = collection.toList(collection.size())
    date_list = ee.List(col_list.iterate(make_date_list, ee.List([])))

    def make_col(date):
        date = ee.Date(date)
        def wrap(img):
            e = image_module.emptyBackground(img, -9999)
            return e.updateMask(e.neq(-9999))

        filtered = collection.filterDate(date, date.advance(1, 'day')).map(wrap)
        first_img = ee.Image(collection.first())

        mosaic = filtered.reduce(reducer).set(
            'system:time_start', date.millis(),
            'system:footprint', mergeGeometries(filtered)
        )
        return mosaic.rename(first_img.bandNames())

    new_col = ee.ImageCollection.fromImages(date_list.map(make_col))
    return new_col


def reduceEqualInterval(collection, interval=30, unit='day', reducer=None,
                        start_date=None, end_date=None):
    """ Reduce an ImageCollection into a new one that has one image per
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
    first = ee.Image(collection.sort('system:time_start').first())
    bands = first.bandNames()

    if not start_date:
        start_date = first.date()
    if not end_date:
        last = ee.Image(collection.sort('system:time_start', False).first())
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
            image = apply_reducer(reducer, filtered)\
                    .set('system:time_start', end.millis())\
                    .set('reduced_from', start.format())\
                    .set('reduced_to', end.format())
            # rename to original names
            image = image.select(image.bandNames(), bands)
            result = ini.add(image)
            return result
        return ee.List(ee.Algorithms.If(condition, true(), ini))

    imlist = ee.List(ranges.iterate(over_ranges, ee.List([])))

    return ee.ImageCollection.fromImages(imlist)


def makeEqualInterval(collection, interval=1, unit='month'):
    """ Make a list of image collections filtered by the given interval,
    for example, one month. Starts from the end of the parsed collection

    :param collection: the collection
    :type collection: ee.ImageCollection
    :param interval: the interval
    :type interval: int
    :param unit: unit of the interval. Can be 'day', 'month', 'year'
    :rtype: ee.List
    """
    interval = int(interval)  # force to int
    collist = collection.sort('system:time_start').toList(collection.size())
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


def getValues(collection, geometry, scale=None, reducer=None,
              id='system:index', properties=None, side='server',
              maxPixels=1e9):
    """ Return all values of all bands of an image collection in the
        specified geometry

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
    :return: Values of all bands in the ponit
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
        values = img.reduceRegion(reducer, geometry, scale,
                                  maxPixels=maxPixels)
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
    result = ee.Dictionary(ee.Algorithms.If(collection.size().neq(0),
                                            result, {}))

    if side == 'server':
        return result
    elif side == 'client':
        return result.getInfo()
    else:
        raise ValueError("side parameter must be 'server' or 'client'")


def data2pandas(data):
    """
    Convert data coming from tools.imagecollection.get_values to a
    pandas DataFrame

    :type data: dict
    :rtype: pandas.DataFrame
    """
    # Indices
    # header
    allbands = [val.keys() for bands, val in data.items()]
    header = []
    for bandlist in allbands:
        for band in bandlist:
            if band not in header:
                header.append(band)

    data_dict = {}
    indices = []
    for i, head in enumerate(header):
        band_data = []
        for iid, val in data.items():
            if i == 0:
                indices.append(iid)
            band_data.append(val[head])
        data_dict[head] = band_data

    df = pd.DataFrame(data=data_dict, index=indices)

    return df


def parametrizeProperty(collection, property, range_from, range_to,
                        pattern='{property}_PARAMETRIZED'):
    """ Parametrize a property

    :param collection: the ImageCollection
    :param range_from: the original property range
    :param range_to: the desired property range
    :param property: the name of the property
    :param pattern: the name of the resulting property. Wherever it says
        'property' will be replaced with the passed property.
    :return: the parsed collection in which every image has a new
        parametrized property
    """
    name = pattern.replace('{property}', property)

    original_range = range_from if isinstance(range_from, ee.List) \
        else ee.List(range_from)

    final_range = range_to if isinstance(range_to, ee.List) \
        else ee.List(range_to)

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


def linearFunctionBand(collection, band, range_min=None, range_max=None,
                       mean=None, output_min=None, output_max=None,
                       name='linear_function'):
    """ Apply a linear function over the bands across every image of the
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
        range_min = ee.Image(collection.select(band).min()).rename('imin')
    else:
        range_min = castImage(range_min)

    if range_max is None:
        range_max = ee.Image(collection.select(band).max()).rename('imax')
    else:
        range_max = castImage(range_max)

    def to_map(img):
        result = image_module.linearFunction(img, band, range_min, range_max,
                                             mean, output_min, output_max,
                                             name)
        return img.addBands(result.rename(name))

    collection = collection.map(to_map)

    return collection


def linearFunctionProperty(collection, property, range_min=None,
                           range_max=None, mean=None, output_min=None,
                           output_max=None, name='LINEAR_FUNCTION'):
    """ Apply a linear function over the properties across every image of the
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


def gaussFunctionBand(collection, band, range_min=None, range_max=None,
                      mean=0, output_min=None, output_max=1, std=None,
                      stretch=1, name='gauss'):
    """ Compute a Guass function using a specified band over an
        ImageCollection. See: https://en.wikipedia.org/wiki/Gaussian_function

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

        result = image_module.gaussFunction(img, band,
                                            range_min=range_min,
                                            range_max=range_max,
                                            mean=mean, std=std,
                                            output_min=output_min,
                                            output_max=output_max,
                                            stretch=stretch,
                                            name=name)
        return img.addBands(result)

    collection = collection.map(to_map)

    return collection


def gaussFunctionProperty(collection, property, range_min=None,
                          range_max=None, mean=0, output_min=None,
                          output_max=1, std=None, stretch=1,
                          name='GAUSS'):
    """ Compute a Guass function using a specified property over an
        ImageCollection. See: https://en.wikipedia.org/wiki/Gaussian_function

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


def normalDistributionProperty(collection, property, mean=None, std=None,
                               name='NORMAL_DISTRIBUTION'):
    """ Compute a normal distribution using a specified property, over an
    ImageCollection. For more see:
    https://en.wikipedia.org/wiki/Normal_distribution

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

    imax = ee.Number(1)\
             .divide(istd.multiply(ee.Number(2).multiply(math.pi).sqrt()))

    return gaussFunctionProperty(collection, property, mean=imean,
                                 output_max=imax, std=istd, name=name)


def normalDistributionBand(collection, band, mean=None, std=None,
                           name='normal_distribution'):
    """ Compute a normal distribution using a specified band, over an
    ImageCollection. For more see:
    https://en.wikipedia.org/wiki/Normal_distribution

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

    imax = ee.Image(1) \
             .divide(istd.multiply(ee.Image.constant(2).multiply(ipi).sqrt()))

    return gaussFunctionBand(collection, band, mean=imean,
                             output_max=imax, std=istd, name=name)