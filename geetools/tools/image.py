# coding=utf-8
"""
Tools for ee.Image
"""
from __future__ import absolute_import
import ee
import ee.data
import math
from . import ee_list, date, string
from ..utils import castImage
from ..ui import map as mapui


def _add_suffix_prefix(image, value, option, bands=None):
    """ Internal function to handle addPrefix and addSuffix """
    if bands:
        bands = ee.List(bands)

    addon = ee.String(value)

    allbands = image.bandNames()
    bands_ = ee.List(ee.Algorithms.If(bands, bands, allbands))

    def over_bands(band, first):
        all = ee.List(first)
        options = ee.Dictionary({
            'suffix': ee.String(band).cat(addon),
            'prefix': addon.cat(ee.String(band))
        })
        return all.replace(band, ee.String(options.get(option)))

    newbands = bands_.iterate(over_bands, allbands)
    newbands = ee.List(newbands)
    return image.select(allbands, newbands)


def addSuffix(image, suffix, bands=None):
    """ Add a suffix to the specified bands

    :param suffix: the value to add as a suffix
    :type suffix: str
    :param bands: the bands to apply the suffix. If None, suffix will fill
        all bands
    :type bands: list
    :rtype: ee.Image
    """
    return _add_suffix_prefix(image, suffix, 'suffix', bands)


def addPrefix(image, prefix, bands=None):
    """ Add a prefix to the specified bands

    :param prefix: the value to add as a prefix
    :type prefix: str
    :param bands: the bands to apply the prefix. If None, prefix will fill
        all bands
    :type bands: list
    :rtype: ee.Image
    """
    return _add_suffix_prefix(image, prefix, 'prefix', bands)


def bufferMask(image, radius=1.5, kernelType='square', units='pixels'):
    """ Make a buffer around the masked pixels """
    masked = image.mask().Not()
    buffer = masked.focal_max(radius, kernelType, units)
    return image.updateMask(buffer.Not())


def empty(value=0, names=None, from_dict=None):
    """ Create a constant image with the given band names and value, and/or
    from a dictionary of {name: value}

    :param names: list of names
    :type names: ee.List or list
    :param value: value for every band of the resulting image
    :type value: int or float
    :param from_dict: {name: value}
    :type from_dict: dict
    :rtype: ee.Image
    """
    image = ee.Image.constant(0)
    bandnames = ee.List([])
    if names:
        bandnames = names if isinstance(names, ee.List) else ee.List(names)
        def bn(name, img):
            img = ee.Image(img)
            newi = ee.Image(value).select([0], [name])
            return img.addBands(newi)
        image = ee.Image(bandnames.iterate(bn, image)) \
            .select(bandnames)

    if from_dict:
        bandnames = bandnames.cat(ee.List(from_dict.keys()))
        for name, value in from_dict.items():
            i = ee.Image(value).select([0], [name])
            image = image.addBands(i).select(bandnames)

    if not from_dict and not names:
        image = ee.Image.constant(value)

    return image


def emptyBackground(image, value=0):
    """ Make all background pixels (not only masked, but all over the world)
    take the parsed value """
    bnames = image.bandNames()
    emp = empty(value, bnames)
    return ee.Image(emp.where(image, image).copyProperties(
        source=image, properties=image.propertyNames()))


def emptyCopy(image, emptyValue=0, copyProperties=None, keepMask=False):
    """ Make an empty copy of the given image """
    footprint = image.geometry()
    emp = empty(emptyValue, image.bandNames())
    if copyProperties:
        emp = emp.copyProperties(source=image, properties=copyProperties)
    if keepMask:
        emp = emp.updateMask(image.mask())

    return ee.Image(ee.Algorithms.If(footprint.isUnbounded(),
                                     emp, emp.clip(footprint)))


def getValue(image, point, scale=None, side="server"):
    """ Return the value of all bands of the image in the specified point

    :param img: Image to get the info from
    :type img: ee.Image
    :param point: Point from where to get the info
    :type point: ee.Geometry.Point
    :param scale: The scale to use in the reducer. It defaults to 10 due to the
        minimum scale available in EE (Sentinel 10m)
    :type scale: int
    :param side: 'server' or 'client' side
    :type side: str
    :return: Values of all bands in the ponit
    :rtype: ee.Dictionary or dict
    """
    if scale:
        scale = int(scale)
    else:
        scale = 1

    type = point.getInfo()["type"]
    if type != "Point":
        raise ValueError("Point must be ee.Geometry.Point")

    result = image.reduceRegion(ee.Reducer.first(), point, scale)

    if side == 'server':
        return result
    elif side == 'client':
        return result.getInfo()
    else:
        raise ValueError("side parameter must be 'server' or 'client'")


def addMultiBands(imagesList):
    """ Image.addBands for many images. All bands from all images will be
    put together, so if there is one band with the same name in different
    images, the first occurrence will keep the name and the rest will have a
    number suffix ({band}_1, {band}_2, etc)

    :param imagesList: a list of images
    :type imagesList: list or ee.List
    :rtype: ee.Image
    """
    imagesList = ee.List(imagesList)
    first = ee.Image(imagesList.get(0))
    rest = imagesList.slice(1)

    def iteration(img, ini):
        ini = ee.Image(ini)
        img = ee.Image(img)
        return ini.addBands(img)

    return ee.Image(rest.iterate(iteration, first))


def renameDict(image, names):
    """ Renames bands of images using a dict

    :param names: matching names where key is original name and values the
        new name
    :type names: dict
    :rtype: ee.Image

    :EXAMPLE:

    .. code:: python

        image = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013344LGN00")
        p = ee.Geometry.Point(-71.72029495239258, -42.78997046797438)

        i = rename_bands({"B1":"BLUE", "B2":"GREEN"})

        print get_value(image, p)
        print get_value(i, p)

    >> {u'B1': 0.10094200074672699, u'B2': 0.07873955368995667, u'B3': 0.057160500437021255}
    >> {u'BLUE': 0.10094200074672699, u'GREEN': 0.07873955368995667, u'B3': 0.057160500437021255}
    """
    bandnames = image.bandNames()
    newnames = ee_list.replaceDict(bandnames, names)
    return image.select(bandnames, newnames)


def removeBands(image, bands):
    """ Remove the specified bands from an image """
    bnames = image.bandNames()
    bands = ee.List(bands)
    inter = ee_list.intersection(bnames, bands)
    diff = bnames.removeAll(inter)
    return image.select(diff)


def parametrize(image, range_from, range_to, bands=None, drop=False):
    """ Parametrize from a original **known** range to a fixed new range

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
    original_range = range_from if isinstance(range_from, ee.List) \
        else ee.List(range_from)

    final_range = range_to if isinstance(range_to, ee.List) \
        else ee.List(range_to)

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


def sumBands(image, name="sum", bands=None):
    """ Adds all *bands* values and puts the result on *name*.

    There are 2 ways to use it:

    .. code:: python

        img = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013344LGN00")
        newimg = Image.sumBands(img, "added_bands", ("B1", "B2", "B3"))

    :param name: name for the band that contains the added values of bands
    :type name: str
    :param bands: names of the bands to be added. If None (default) it sums
        all bands
    :type bands: tuple
    :return: the parsed image with one additional band with the sum of `bands`
    :rtype: ee.Image
    """
    band_names = image.bandNames()
    if bands is None:
        bn = band_names
    else:
        bn = ee.List(list(bands))

    nim = ee.Image(0).select([0], [name])

    # TODO: check if passed band names are in band names # DONE
    def sum_bands(n, ini):
        condition = ee.List(band_names).contains(n)
        return ee.Algorithms.If(condition,
                                ee.Image(ini).add(image.select([n])),
                                ee.Image(ini))

    newimg = ee.Image(bn.iterate(sum_bands, nim))

    return image.addBands(newimg)


def replace(image, to_replace, to_add):
    """ Replace one band of the image with a provided band

    :param to_replace: name of the band to replace. If the image hasn't got
        that band, it will be added to the image.
    :type to_replace: str
    :param to_add: Image (one band) containing the band to add. If an Image
        with more than one band is provided, it uses the first band.
    :type to_add: ee.Image
    :return: Same Image provided with the band replaced
    :rtype: ee.Image
    """
    # TODO: see Image.addBands({overwrite:True})
    band = to_add.select([0])
    bands = image.bandNames()
    resto = bands.remove(to_replace)
    img_resto = image.select(resto)
    img_final = img_resto.addBands(band)
    return img_final


def addConstantBands(image, value=None, *names, **pairs):
    """ Adds bands with a constant value

    :param names: final names for the additional bands
    :type names: str
    :param value: constant value
    :type value: int or float
    :param pairs: keywords for the bands (see example)
    :type pairs: int or float
    :return: the function for ee.ImageCollection.map()
    :rtype: function

    :Example:

    .. code:: python

        from geetools.tools import addConstantBands
        import ee

        col = ee.ImageCollection(ID)

        # Option 1 - arguments
        addC = addConstantBands(0, "a", "b", "c")
        newcol = col.map(addC)

        # Option 2 - keyword arguments
        addC = addConstantBands(a=0, b=1, c=2)
        newcol = col.map(addC)

        # Option 3 - Combining
        addC = addC = addConstantBands(0, "a", "b", "c", d=1, e=2)
        newcol = col.map(addC)
    """
    from functools import reduce

    # check type of value
    # is_val_n = type(value) is int or type(value) is float
    is_val_n = isinstance(value, (int, float))

    if is_val_n and names:
        list1 = [ee.Image.constant(value).select([0], [n]) for n in names]
    else:
        list1 = []

    if pairs:
        list2 = [ee.Image.constant(val).select([0], [key]) for key, val \
                 in pairs.items()]
    else:
        list2 = []

    if list1 or list2:
        lista_img = list1 + list2
    elif value is None:
        raise ValueError("Parameter 'value' must be a number")
    else:
        return addConstantBands(image, value, "constant")

    img_final = reduce(lambda x, y: x.addBands(y), lista_img)

    return ee.Image(image).addBands(ee.Image(img_final))


def minscale(image):
    """ Get the minimal scale of an Image, looking at all Image's bands.
    For example if:
        B1 = 30
        B2 = 60
        B3 = 10
    the function will return 10

    :return: the minimal scale
    :rtype: ee.Number
    """
    bands = image.bandNames()

    first = image.select([ee.String(bands.get(0))])
    ini = ee.Number(first.projection().nominalScale())

    def wrap(name, i):
        i = ee.Number(i)
        scale = ee.Number(image.select([name]).projection().nominalScale())
        condition = scale.lte(i)
        newscale = ee.Algorithms.If(condition, scale, i)
        return newscale

    return ee.Number(bands.slice(1).iterate(wrap, ini))


def mixBands(imgs):
    """ Mix all bands into a single image """
    if isinstance(imgs, (list, tuple)):
        imgs = ee.List(imgs)

    first = ee.Image(imgs.get(0))
    rest = imgs.slice(1)

    return ee.Image(rest.iterate(lambda i, f: ee.Image(f).addBands(i), first))


def computeBits(image, start, end, newName):
    """ Compute the bits of an image

    :param start: start bit
    :type start: int
    :param end: end bit
    :type end: int
    :param newName: new name for the band
    :type newName: str
    :return: A function which single argument is the image and returns a single
        band image of the extracted bits, giving the band a new name
    :rtype: function
    """
    pattern = ee.Number(0)
    start = ee.Number(start).toInt()
    end = ee.Number(end).toInt()
    newName = ee.String(newName)

    seq = ee.List.sequence(start, end)

    def toiterate(element, ini):
        ini = ee.Number(ini)
        bit = ee.Number(2).pow(ee.Number(element))
        return ini.add(bit)

    patt = seq.iterate(toiterate, pattern)

    patt = ee.Number(patt).toInt()

    good_pix = image.select([0], [newName]).toInt() \
        .bitwiseAnd(patt).rightShift(start)
    return good_pix.toInt()


def passProperty(image, to, properties):
    """ Pass properties from one image to another

    :param img_with: image that has the properties to tranpass
    :type img_with: ee.Image
    :param img_without: image that will recieve the properties
    :type img_without: ee.Image
    :param properties: properies to transpass
    :type properties: list
    :return: the image with the new properties
    :rtype: ee.Image
    """
    for prop in properties:
        p = image.get(prop)
        to = to.set(prop, p)
    return to


def goodPix(image, retain=None, drop=None, name='good_pix'):
    """ Get a 'good pixels' bands from the image's bands that retain the good
    pixels and drop the bad pixels. It will first retain the retainable bands
    and then drop the droppable ones

    :param image: the image
    :type image: ee.Image
    :param retain: names of the bands that hold good (want to retain) pixels,
        for example, a good quality band
    :type retain: tuple
    :param drop: names of the bands that hold bad (want to drop) pixels, for
        example a cloud mask band
    :type drop: tuple
    :param name: name for the resulting band
    :type name: str
    :rtype: ee.Image
    """
    to_retain = ee.List(retain)
    to_drop = ee.List(drop)

    def make_or(bandname, ini):
        ini = ee.Image(ini)
        band = image.select(bandname)
        return ini.Or(band)

    final_retain = ee.Image(to_retain.iterate(make_or, empty(0)))
    final_drop = ee.Image(to_drop.iterate(make_or, empty(0)))

    # not bad but not good (retain)
    not_bad_not_good = final_drop.And(final_retain)

    final = not_bad_not_good.bitwiseXor(final_drop)

    return final.select([0], [name])


def toGrid(image, size=1, band=None, geometry=None):
    """ Create a grid from pixels in an image. Results may depend on the image
    projection. Work fine in Landsat imagery.

    IMPORTANT: This grid is not perfect, it can be misplaced and have some
    holes due to projection.

    :param image: the image
    :type image: ee.Image
    :param size: the size of each cell, according to:
        - 1: 1 pixel
        - 2: 9 pixels (3x3)
        - 3: 25 pixels (5x5)
        - and so on..
    :type size: int
    :param band: the band to get the projection (and so, the scale) from. If
        None, the first one will be used
    :type band: str
    :param geometry: the geometry where the grid will be computed. If the image
        is unbounded this parameter must be set in order to work. If None,
        the image geometry will be used if not unbounded.
    :type geometry: ee.Geometry or ee.Feature
    """
    band = band if band else 0
    iband = image.select(band)

    if geometry:
        if isinstance(geometry, ee.Feature):
            geometry = geometry.geometry()
    else:
        geometry = image.geometry()

    projection = iband.projection()
    scale = projection.nominalScale()
    scale = scale.multiply((int(size)*2)-1)
    buffer = scale.divide(2)

    # get coordinates image
    latlon = ee.Image.pixelLonLat().reproject(projection)

    # put each lon lat in a list
    coords = latlon.select(['longitude', 'latitude'])

    coords = coords.reduceRegion(
        reducer= ee.Reducer.toList(),
        geometry= geometry.buffer(scale),
        scale= scale)

    # get lat & lon
    lat = ee.List(coords.get('latitude'))
    lon = ee.List(coords.get('longitude'))

    # zip them. Example: zip([1, 3],[2, 4]) --> [[1, 2], [3,4]]
    point_list = lon.zip(lat)

    def over_list(p):
        p = ee.List(p)
        point = ee.Geometry.Point(p).buffer(buffer).bounds()
        return ee.Feature(point)

    # make grid
    fc = ee.FeatureCollection(point_list.map(over_list))

    return fc


def renamePattern(image, pattern, bands=None):
    """ Rename the bands of the parsed image with the given pattern

    :param image:
    :param pattern: the special keyword `{band}` will be replaced with the
        actual band name. Spaces will be replaced with underscore. It also will
        be trimmed
    :param bands: the bands to rename. If None it'll rename all the bands
    :return:
    """
    allbands = image.bandNames()

    pattern = ee.String(pattern)
    selected = image.select(bands) if bands else image

    pattern = pattern.trim().split(' ').join('_')

    bands_to_replace = selected.bandNames()

    def wrap(name):
        condition = pattern.index('{band}').gt(0)

        return ee.String(ee.Algorithms.If(
            condition,
            pattern.replace('{band}', ee.String(name)),
            ee.String(name)))

    newbands = bands_to_replace.map(wrap)

    new_allbands = ee_list.replaceDict(
        allbands, ee.Dictionary.fromLists(bands_to_replace, newbands))

    return image.select(allbands, new_allbands)


def gaussFunction(image, band, range_min=None, range_max=None, mean=0,
                  std=None, output_min=None, output_max=1, stretch=1,
                  region=None, scale=None, name='gauss', **kwargs):
    """ Apply the Guassian function to an Image.
    https://en.wikipedia.org/wiki/Gaussian_function

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
    :param name: name of the resulting band
    :type name: strmax
    """
    image = image.select(band)

    if not region:
        region = image.geometry()

    if not scale:
        scale = image.projection().nominalScale()

    if range_min is None and range_max is None:
        minmax = image.reduceRegion(reducer=ee.Reducer.minMax(),
                                    geometry=region, scale=scale, **kwargs)
        minname = '{}_min'.format(band)
        maxname = '{}_max'.format(band)

        range_min = ee.Image.constant(minmax.get(minname))
        range_max = ee.Image.constant(minmax.get(maxname))

    elif range_min is None:
        minmax = image.reduceRegion(reducer=ee.Reducer.min(),
                                    geometry=region, scale=scale, **kwargs)
        range_min = ee.Image.constant(minmax.get(band))
        range_max = castImage(range_max)

    elif range_max is None:
        minmax = image.reduceRegion(reducer=ee.Reducer.max(),
                                    geometry=region, scale=scale, **kwargs)
        range_max = ee.Image.constant(minmax.get(band))
        range_min = castImage(range_min)
    else:
        range_max = castImage(range_max)
        range_min = castImage(range_min)

    mean = castImage(mean)

    if std is None:
        std = range_max.subtract(range_min).divide(4)
    else:
        std = castImage(std)

    output_min = castImage(output_min)
    output_max = castImage(output_max)
    stretch = castImage(stretch)

    def compute_gauss(img):
        result = ee.Image().expression(
            'exp(((val-mean)**2)/(-2*(std**2))*(abs(stretch)))*max',
            {'val': img,
             'mean': mean,
             'std': std,
             'max': output_max,
             'stretch': stretch
             })
        return result

    no_parametrized = compute_gauss(image)

    if output_min is None:
        return no_parametrized.rename(name)
    else:
        min_result = compute_gauss(range_min)
        max_result = compute_gauss(range_max)
        min_result_final = min_result.min(max_result)

        parametrized = ee.Image().expression(
            '(value-min_result)/(max-min_result)*(max-min)+min',
            {'value': no_parametrized,
             'min_result': min_result_final,
             'max': output_max,
             'min': output_min
             })
        return parametrized.rename(name)


def makeName(img, pattern, date_pattern=None, extra=None):
    """ Make a name with the given pattern. The pattern must contain the
    propeties to replace between curly braces. There are 2 special words:

    * 'system_date': replace with the date of the image formatted with
      `date_pattern`, which defaults to 'yyyyMMdd'
    * 'id' or 'ID': the image id. If None, it'll be replaced with 'id'

    Pattern example (supposing each image has a property called `city`):
    'image from {city} on {system_date}'

    You can add extra parameters using keyword `extra`
    """
    img = ee.Image(img)
    props = img.toDictionary()
    props = ee.Dictionary(ee.Algorithms.If(
        img.id(),
        props.set('id', img.id()).set('ID', img.id()),
        props))
    props = ee.Dictionary(ee.Algorithms.If(
        img.propertyNames().contains('system:time_start'),
        props.set('system_date', img.date().format(date_pattern)),
        props))
    if extra:
        extra = ee.Dictionary(extra)
        props = props.combine(extra)
    name = string.format(pattern, props)

    return name


def normalDistribution(image, band, mean=None, std=None, region=None,
                       scale=None, name='normal_distribution', **kwargs):
    """ Compute a Normal Distribution using the Gaussian Function """
    pi = ee.Number(math.pi)

    image = image.select(band)

    if mean is None:
        mean = image.reduceRegion(reducer=ee.Reducer.mean(),
                                  geometry=region, scale=scale, **kwargs)
        mean = ee.Image.constant(mean.get(band))
    else:
        mean = castImage(mean)

    if std is None:
        std = image.reduceRegion(reducer=ee.Reducer.stdDev(),
                                 geometry=region, scale=scale, **kwargs)
        std = ee.Image.constant(std.get(band))
    else:
        std = castImage(std)

    output_max = ee.Image(1)\
                   .divide(std.multiply(ee.Image(2).multiply(pi).sqrt()))

    return gaussFunction(image, band, mean=mean, std=std,
                         output_max=output_max, name=name, **kwargs)


def linearFunction(image, band, range_min=None, range_max=None, mean=None,
                   output_min=None, output_max=None, name='linear_function',
                   region=None, scale=None, **kwargs):
    """ Apply a linear function over one image band using the following
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
        minmax = image.reduceRegion(reducer=ee.Reducer.minMax(),
                                    geometry=region, scale=scale, **kwargs)
        minname = '{}_min'.format(band)
        maxname = '{}_max'.format(band)

        imin = ee.Image.constant(minmax.get(minname))
        imax = ee.Image.constant(minmax.get(maxname))

    elif range_min is None:
        minmax = image.reduceRegion(reducer=ee.Reducer.min(),
                                    geometry=region, scale=scale, **kwargs)
        imin = ee.Image.constant(minmax.get(band))
        imax = castImage(range_max)

    elif range_max is None:
        minmax = image.reduceRegion(reducer=ee.Reducer.max(),
                                    geometry=region, scale=scale, **kwargs)
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
        'abs(val-mean)*(-1)*((max-min)/t)+max',
        {'val': image,
         'mean': imean,
         't': t,
         'imin': imin,
         'max': output_max,
         'min': output_min
         })

    return result.rename(name)


def doyToDate(image, dateFormat='yyyyMMdd', year=None):
    """ Make a date band from a day of year band """
    if not year:
        year = image.date().get('year')

    doyband = image.select([0])
    leap = date.isLeap(year)
    limit = ee.Number(ee.Algorithms.If(leap, 365, 364))
    alldoys = ee.List.sequence(1, limit)

    def wrap(doy, i):
        i = ee.Image(i)
        doy = ee.Number(doy)
        d = date.fromDOY(doy, year)
        date_band = ee.Image.constant(ee.Number.parse(d.format(dateFormat)))
        condition = i.eq(doy)
        return i.where(condition, date_band)

    datei = ee.Image(alldoys.iterate(wrap, doyband))

    return datei.rename('date')


def maskInside(image, geometry):
    """ This is the opposite to ee.Image.clip(geometry) """
    mask = ee.Image.constant(1).clip(geometry).mask().Not()
    return image.updateMask(mask)


def paint(image, featurecollection, vis_params=None, color='black', width=1,
          fillColor=None, **kwargs):
    """ Paint a FeatureCollection onto an Image. Returns an Image with three
    bands: vis-blue, vis-geen, vis-red (uint8)

    It admits the same parameters as ee.FeatureCollection.style
    """
    if not fillColor:
        fillColor = "#00000000"
    if not vis_params:
        firstband = ee.String(image.bandNames().get(0))
        vis_params = dict(bands=[firstband, firstband, firstband], min=0,
                          max=1)
    region = image.geometry()
    filtered = ee.FeatureCollection(
        ee.Algorithms.If(
            region.isUnbounded(),
            featurecollection,
            featurecollection.filterBounds(region)
        ))
    fcraster = filtered.style(color=color, width=width, fillColor=fillColor,
                              **kwargs)
    mask = fcraster.reduce('sum').gte(0).rename('mask')
    topaint = image.visualize(**vis_params)
    final = topaint.where(mask, fcraster)
    final = final.copyProperties(source=image)
    properties = image.propertyNames()
    final = ee.Image(ee.Algorithms.If(
        properties.contains('system:time_start'),
        final.set('system:time_start', image.date().millis()),
        final))
    final = ee.Image(ee.Algorithms.If(
        properties.contains('system:time_end'),
        final.set('system:time_end', ee.Number(image.get('system:time_end'))),
        final))

    return final


def repeatBand(image, times=None, names=None, properties=None):
    """ Repeat one band. If the image parsed has more than one band, the first
    will be used """
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
    """
    Return an image array without zeros

    :param image:
    :return:
    """
    def wrap(arr):
        binarr = arr.divide(arr)
        n = binarr.arrayReduce(ee.Reducer.sum(), [0]).multiply(-1)
        nimg = n.arrayProject([0]).arrayFlatten([['n']]).toInt()
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


def getTileURL(image, visParams=None):
    """ Get the URL for the given image passing a normal visualization
    parameters like `{'bands':['B4','B3','B2'], 'min':0, 'max':5000}` """
    if visParams:
        vis = mapui.formatVisParams(visParams)
        image_info = image.getMapId(vis)
    else:
        image_info = image.getMapId()
    fetcher = image_info['tile_fetcher']
    return fetcher.url_format


def applyMask(image, mask, bands=None, negative=True):
    """ Apply a passed positive mask """
    bands = bands or mask.bandNames()
    bands = ee.List(bands)
    def wrap(band, img):
        img = ee.Image(img)
        band = ee.String(band)
        m = mask.select(band)
        toapply = m.Not() if negative else m
        return img.updateMask(toapply)

    return ee.Image(bands.iterate(wrap, image))


def maskCover(image, geometry=None, scale=None, property_name='MASK_COVER',
              crs=None, crsTransform=None, bestEffort=False,
              maxPixels=1e13, tileScale=1):
    """ Percentage of masked pixels (masked/total * 100) as an Image property

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
        reducer= ee.Reducer.count(),
        geometry= geometry,
        scale= scale,
        maxPixels= maxPixels,
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
    zeros_in_mask =  image_to_compute.reduceRegion(
        reducer= ee.Reducer.count(),
        geometry= geometry,
        scale= scale,
        maxPixels= maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale
    ).get(band)
    zeros_in_mask = ee.Number(zeros_in_mask)

    percentage = zeros_in_mask.divide(ones)
    # Multiply by 100
    cover = percentage.multiply(100)

    # Return None if geometry is unbounded
    final = ee.Number(ee.Algorithms.If(unbounded, 0, cover))

    return image.set(property_name, final)


def regionCover(image, region, bands=None, scale=None, operator='OR',
                property_name='REGION_COVER', crs=None, crsTransform=None,
                bestEffort=False, maxPixels=1e13, tileScale=1):
    """ Compute the percentage of values greater than 1 in a region. If more
     than one band is specified, it applies the specified operator """
    operators = ['OR', 'AND']
    if operator not in operators:
        raise ValueError('operator must be one of {}'.format(operators))

    if not bands:
        bands = ee.List([image.bandNames().get(0)])

    if operator == 'AND':
        reducer = ee.Reducer.bitwiseAnd()
    else:
        reducer = ee.Reducer.bitwiseOr()

    bandname = 'regionCover'
    mask = image.select(bands).reduce(reducer).rename(bandname)

    # get projection
    projection = mask.projection()

    if not scale:
        scale = projection.nominalScale()

    # Make an image with all ones
    ones_i = ee.Image.constant(1).reproject(projection).rename(bandname)

    # manage geometry types
    if isinstance(region, (ee.Feature, ee.FeatureCollection)):
        region = region.geometry()

    unbounded = region.isUnbounded()

    # Get total number of pixels
    ones = ones_i.reduceRegion(
        reducer= ee.Reducer.count(),
        geometry= region,
        scale= scale,
        maxPixels= maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale,
    ).get(bandname)
    ones = ee.Number(ones)

    # select first band, unmask and get the inverse
    image_to_compute = mask.selfMask()

    # Get number of zeros in the given image
    zeros_in_mask =  image_to_compute.reduceRegion(
        reducer= ee.Reducer.count(),
        geometry= region,
        scale= scale,
        maxPixels= maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale
    ).get(bandname)
    zeros_in_mask = ee.Number(zeros_in_mask)

    percentage = zeros_in_mask.divide(ones)

    # Multiply by 100
    cover = percentage.multiply(100)

    # Return None if geometry is unbounded
    final = ee.Number(ee.Algorithms.If(unbounded, 0, cover))
    return image.set(property_name, final)


def proxy(values=(0,), names=('constant',), types=('int8',)):
    """ Create a proxy image with the given values, names and types

    :param values: list of values for every band of the resulting image
    :type values: list
    :param names: list of names
    :type names: list
    :param types: list of band types. Options are  'int8', 'int16', 'int32',
    'int64', 'uint8', 'uint16', 'uint32', 'byte', 'short', 'int', 'long',
    'float' and 'double'
    :type types: list
    :rtype: ee.Image
    """
    values = list(values)
    names = list(names)
    types = list(types)
    tps = dict(zip(names, types))
    im = ee.Image(values).rename(names).cast(tps)
    # update mask
    for v, n in zip(values, names):
        if v is None:
            band = im.select(n)
            masked = band.selfMask()
            im = im.addBands(masked, overwrite=True)
    return im


class Classification(object):
    """ Class holding (static) methods for classified images. """
    @staticmethod
    def vectorize(image, categories, label='label'):
        """ Reduce to vectors the selected classes fro a classified image

        :param categories: the categories to vectorize
        :type categories: list

        """
        def over_cat(cat, ini):
            cat = ee.Number(cat)
            ini = ee.Image(ini)
            return ini.add(image.eq(cat).multiply(cat))

        filtered = ee.Image(
            ee.List(categories).iterate(over_cat,
                                        empty(0, [label])))

        out = filtered.neq(0)
        filtered = filtered.updateMask(out)

        return filtered.reduceToVectors(**{
            'scale': 30,
            'maxPixels':1e13,
            'labelProperty': label})
