# coding=utf-8
""" Module holding tools for ee.ImageCollections """
import ee
import ee.data
import pandas as pd
import math
from . import date
from . import image as image_module
from . import collection as eecollection


if not ee.data._initialized:
    ee.Initialize()


def add(collection, image):
    """ Add an Image to the Collection

    **SERVER SIDE**

    """
    # TODO: handle a list of images
    collist = collection.toList(collection.size())
    append = collist.add(image)
    return ee.ImageCollection.fromImages(append)


def get_id(collection):
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


def fill_with_last(collection):
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


def reduce_equal_interval(collection, interval=30, unit='day', reducer=None,
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

    ranges = date.daterange_list(start_date, end_date, interval, unit)

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


def get_values(collection, geometry, scale=None, reducer=ee.Reducer.mean(),
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
    if not scale:
        # scale = minscale(ee.Image(self.first()))
        scale = 1
    else:
        scale = int(scale)

    propid = ee.Image(collection.first()).get(id).getInfo()
    def transform(eeobject):
        try: # Py2
            isstr = isinstance(propid, (str, unicode))
        except: # Py3
            isstr = isinstance(propid, (str))

        if isinstance(propid, (int, float)):
            return ee.Number(eeobject).format()
        elif isstr:
            return ee.String(eeobject)
        else:
            msg = 'property must be a number or string, found {}'
            raise ValueError(msg.format(type(propid)))


    if not properties:
        properties = []
    properties = ee.List(properties)

    def listval(img, it):
        theid = ee.String(transform(img.get(id)))
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
            # value = img.get(prop)
            # return ini.set(prop, value)
            return ee.Algorithms.If(condition, true(), ini)

        with_prop = ee.Dictionary(properties.iterate(add_properties, values))
        return ee.Dictionary(it).set(theid, with_prop)

    result = collection.iterate(listval, ee.Dictionary({}))
    result = ee.Dictionary(result)

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


def distribution_linear_band(collection, band, range_min=None, range_max=None,
                             mean=None, max=None, min=None,
                             name='linear_dist'):
    """ Compute a linear distribution using a specified band over an
        ImageCollection

    f(x) = abs(val-mean)*(-1)*((max-min)/a)+max

    :param collection:
    :type collection: ee.ImageCollection
    :param band: the name of the band to use
    :type band: str
    :param mean: the mean value. If None it will be computed from the source.
        defaults to None.
    :type mean: float
    """
    if range_min is None:
        imin = ee.Image(collection.select(band).min()).rename('imin')
    else:
        imin = ee.Image.constant(range_min)

    if range_max is None:
        imax = ee.Image(collection.select(band).max()).rename('imax')
    else:
        imax = ee.Image.constant(range_max)

    if mean is None:
        imean = imax
    else:
        imean = ee.Image.constant(mean).rename('imean')

    if max is None:
        max = imax

    if min is None:
        min = imin

    condition = imean.lt(imax.divide(2))
    # a = ee.Image(ee.Algorithms.If(condition,
    #                               imax.subtract(imean).abs(),
    #                               imin.subtract(imean).abs()))

    # Because of
    # https://groups.google.com/d/msg/google-earth-engine-developers/rars5FsT03g/uQsHzccXAQAJ
    # https://github.com/google/earthengine-api/issues/80
    # a = a.where(a.eq(0.0), imax)
    a = imin.subtract(imean).abs().where(condition, imax.subtract(imean).abs())

    def to_map(img):
        iband = img.select(band)
        result = ee.Image().expression(
            'abs(val-mean)*(-1)*((max-min)/a)+max',
            {'val': iband,
             'mean': imean,
             'a': a,
             'imin': imin,
             'max': max,
             'min': min
             })
        return img.addBands(result.rename(name))

    collection = collection.map(to_map)

    return collection


def distribution_linear_property(collection, property, range_min=None,
                                 range_max=None,mean=None, max=None,
                                 min=None, name='LINEAR_DIST'):
    """ Compute a linear distribution using a specified property over an
        ImageCollection

    f(x) = abs(val-mean)*(-1)*((max-min)/a)+max

    :param collection:
    :type collection: ee.ImageCollection
    :param property: the name of the property to use
    :type property: str
    :param mean: the mean value. If None it will be computed from the source.
        defaults to None.
    :type mean: float
    :return: the parsed collection in which each image has an new property for
        the computed value called by parameter `name`
    :rtype: ee.ImageCollection
    """
    if range_min is None:
        imin = ee.Number(collection.aggregate_min(property))
    else:
        imin = ee.Image.constant(range_min)

    if range_max is None:
        imax = ee.Number(collection.aggregate_max(property))
    else:
        imax = ee.Image.constant(range_max)

    if mean is None:
        imean = imax
    else:
        imean = ee.Number(mean)

    if max is None:
        max = imax
    else:
        max = ee.Number(max)

    if min is None:
        min = imin
    else:
        min = ee.Number(min)

    condition = imean.lt(imax.divide(2))
    t = ee.Image(ee.Algorithms.If(condition,
                                  imax.subtract(imean).abs(),
                                  imin.subtract(imean).abs()))

    def to_map(img):
        val = ee.Number(img.get(property))

        a = val.subtract(imean).abs().multiply(-1)
        b = max.subtract(min)
        c = b.divide(t)
        d = a.multiply(c)
        result = d.add(max)

        return img.set(name, result)

    collection = collection.map(to_map)

    return collection


def distribution_normal_band(collection, band, mean=None, std=None,
                             max=None, min=None, stretch=-1,
                             name='normal_dist'):
    """ Compute a Normal distribution using a specified band over an
        ImageCollection

    f(x) = exp((((((x-mean)**2)/(2*(std**2))*(factor)))/(sqrt(2*pi)*std)))

    :param collection:
    :type collection: ee.ImageCollection
    :param band: the name of the band to use
    :type band: str
    :param mean: the mean value. If None it will be computed from the source.
        defaults to None.
    :type mean: float
    :param std: the standard deviation value. If None it will be computed from
        the source. Defaults to None.
    :type std: float
    """
    pi = ee.Image(math.pi)

    if mean is None:
        imean = ee.Image(collection.select(band).mean()).rename('imean')
    else:
        imean = ee.Image.constant(mean).rename('imean')

    if std is None:
        istd = ee.Image(collection.select(band).reduce(ee.Reducer.stdDev())) \
            .rename('istd')
    else:
        istd = ee.Image.constant(std).rename('istd')

    if max is None:
        imax = ee.Image(1) \
            .divide(istd.multiply(ee.Image(2).multiply(pi).sqrt())) \
            .rename('imax')
    else:
        imax = ee.Image(max).rename('imax')

    def to_map(img):
        iband = img.select(band)

        result = ee.Image().expression(
            'exp(((val-mean)**2)/(2*(std**2))*(stretch))*imax',
            {'val': iband,
             'mean': imean,
             'std': istd,
             'imax': imax,
             'stretch': ee.Image(stretch)
             })
        return img.addBands(result.rename(name))

    collection = collection.map(to_map)

    if min is None:
        return collection
    else:
        imin = ee.Image(collection.select(name).min())
        def normalize(img):
            value = img.select(name)
            e = value.subtract(imin)
            f = imax.subtract(imin)
            g = e.divide(f)
            result = g.multiply(imax.subtract(ee.Image(min))) \
                .add(ee.Image(min))
            return image_module.replace(img, name, result)
        return collection.map(normalize)


def distribution_normal_property(collection, property, mean=None, std=None,
                                 max=None, min=None, stretch=-1,
                                 name='NORMAL_DIST'):
    """ Compute a normal distribution using a specified property, over an
        ImageCollection

    f(x) = exp((((((x-mean)**2)/(2*(std**2))*(factor)))/(sqrt(2*pi)*std)))

    :param collection:
    :type collection: ee.ImageCollection
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
        imean = ee.Number(collection.aggregate_mean(property))
    else:
        imean = ee.Number(mean)

    if std is None:
        istd = ee.Number(collection.aggregate_total_sd(property))
    else:
        istd = ee.Number(std)

    if max is None:
        imax = ee.Number(1)\
                 .divide(istd.multiply(ee.Number(2).multiply(math.pi).sqrt()))
    else:
        imax = ee.Number(max)

    def to_map(img):
        val = ee.Number(img.get(property))

        a = val.subtract(imean).pow(2)
        b = istd.pow(2).multiply(2)
        c = a.divide(b).multiply(stretch)
        d = c.exp()
        result = d.multiply(imax)
        return img.set(name, result)

    collection = collection.map(to_map)

    if min is None:
        return collection
    else:
        imin = ee.Number(collection.aggregate_min(name))
        def normalize(img):
            value = ee.Number(img.get(name))
            e = value.subtract(imin)
            f = imax.subtract(imin)
            g = e.divide(f)
            result = g.multiply(imax.subtract(ee.Number(min)))\
                      .add(ee.Number(min))
            return img.set(name, result)
        return collection.map(normalize)