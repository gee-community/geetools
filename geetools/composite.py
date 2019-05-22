# coding=utf-8
""" Module holding tools for creating composites """
import ee
from uuid import uuid4
from . import tools, algorithms


def medoidScore(collection, bands=None, discard_zeros=False,
                bandname='sumdist', normalize=True):
    """ Compute a score to reflect 'how far' is from the medoid. Same params
     as medoid() """
    first_image = ee.Image(collection.first())
    if not bands:
        bands = first_image.bandNames()

    # Create a unique id property called 'enumeration'
    enumerated = tools.imagecollection.enumerateProperty(collection)
    collist = enumerated.toList(enumerated.size())

    def over_list(im):
        im = ee.Image(im)
        n = ee.Number(im.get('enumeration'))

        # Remove the current image from the collection
        filtered = tools.ee_list.removeIndex(collist, n)

        # Select bands for medoid
        to_process = im.select(bands)

        def over_collist(img):
            return ee.Image(img).select(bands)
        filtered = filtered.map(over_collist)

        # Compute the sum of the euclidean distance between the current image
        # and every image in the rest of the collection
        dist = algorithms.sumDistance(
            to_process, filtered,
            name=bandname,
            discard_zeros=discard_zeros)

        # Mask zero values
        if not normalize:
            # multiply by -1 to get the lowest value in the qualityMosaic
            dist = dist.multiply(-1)

        return im.addBands(dist)

    imlist = ee.List(collist.map(over_list))

    medcol = ee.ImageCollection.fromImages(imlist)

    # Normalize result to be between 0 and 1
    if normalize:
        min_sumdist = ee.Image(medcol.select(bandname).min())\
                        .rename('min_sumdist')
        max_sumdist = ee.Image(medcol.select(bandname).max()) \
                        .rename('max_sumdist')

        def to_normalize(img):
            sumdist = img.select(bandname)
            newband = ee.Image().expression(
                '1-((val-min)/(max-min))',
                {'val': sumdist,
                 'min': min_sumdist,
                 'max': max_sumdist}
            ).rename(bandname)
            return tools.image.replace(img, bandname, newband)

        medcol = medcol.map(to_normalize)

    return medcol


def medoid(collection, bands=None, discard_zeros=False):
    """ Medoid Composite

    :param collection: the collection to composite
    :type collection: ee.ImageCollection
    :param bands: the bands to use for computation. The composite will include
        all bands
    :type bands: list
    :param discard_zeros: Masked and pixels with value zero will not be use
        for computation. Improves dark zones.
    :type discard_zeros: bool
    :return: the Medoid Composite
    :rtype: ee.Image
    """
    medcol = medoidScore(collection, bands, discard_zeros)
    comp = medcol.qualityMosaic('sumdist')
    final = tools.image.removeBands(comp, ['sumdist', 'mask'])
    return final


def closestDate(col, clip_to_first=False):
    """ Make a composite in which masked pixels are filled with the
    last available pixel. Make sure all image bands are casted

    :param clip_to_first: whether to clip with the 'first' image
        geometry
    """
    col = col.sort('system:time_start', False)
    first = ee.Image(col.first())

    # band names
    bandnames = first.bandNames()

    if clip_to_first:
        col = col.map(lambda img: img.clip(first.geometry()))

    tempname = 'a{}'.format(uuid4().hex)

    # add millis band (for compositing)
    col = col.map(lambda img: img.addBands(
        ee.Image.constant(img.date().millis()).rename(tempname).toInt()))

    col = col.sort('system:time_start')

    composite = col.qualityMosaic(tempname)

    return composite.select(bandnames)


def compositeRegularIntervals(collection, interval=1, unit='month',
                              date_range=(1, 1), date_range_unit='day',
                              direction='backward',
                              composite_function=None,
                              composite_date=0.5):
    """ Make a composite at regular intervals parsing a composite
    function. This function MUST have as only argument the collection,
    for example, the default function (if the argument is None) is
    `lambda col: col.median()`.
    """
    if composite_function is None:
        composite_function = lambda col: col.median()
    sorted_list = collection.sort('system:time_start').toList(
        collection.size())
    start_date = ee.Image(sorted_list.get(0)).date()
    end_date = ee.Image(sorted_list.get(-1)).date()
    date_ranges = tools.date.regularIntervals(
        start_date, end_date, interval, unit,
        date_range, date_range_unit, direction)
    def wrap(dr, l):
        l = ee.List(l)
        dr = ee.DateRange(dr)
        filtered = collection.filterDate(dr.start(), dr.end())
        def true(filt, ll):
            comp = composite_function(filtered)
            comp = comp.set(
                'system:time_start', dr.start().advance(
                    composite_date, 'day').millis())
            return ll.add(comp)

        return ee.Algorithms.If(filtered.size(), true(filtered, l), l)

    return ee.ImageCollection.fromImages(
        ee.List(date_ranges.iterate(wrap, ee.List([]))))
