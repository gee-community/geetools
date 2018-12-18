# coding=utf-8
""" Module holding tools for ee.ImageCollections """
import ee
import ee.data
from . import date
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
