# coding=utf-8
"""
Tools for ee.Image
"""
from __future__ import absolute_import
import ee
import ee.data
from . import ee_list

if not ee.data._initialized:
    ee.Initialize()


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


def get_value(image, point, scale=None, side="server"):
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


def addMultiBands(img, *imgs):
    """ Image.addBands for many images. All bands from all images will be
    put together, so if there is one band with the same name in different
    images, the first occurrence will keep the name and the rest will have a
    number suffix ({band}_1, {band}_2, etc)

    :param imgs: images to add bands
    :type imgs: tuple
    :rtype: ee.Image
    """
    for i in imgs:
        img = img.addBands(i)
    return img


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
    newnames = ee_list.replace_many(bandnames, names)
    return image.select(bandnames, newnames)


def removeBands(image, bands):
    """ Remove the specified bands from an image """
    bnames = image.bandNames()
    bands = ee.List(bands)
    inter = ee_list.intersection(bnames, bands)
    diff = bnames.removeAll(inter)
    return image.select(diff)


def parametrize(image, range_from, range_to, bands=None):
    """ Parametrize from a original known range to a fixed new range

    :Parameters:
    :param range_from: Original range. example: (0, 5000)
    :type range_from: tuple
    :param range_to: Fixed new range. example: (500, 1000)
    :type range_to: tuple
    :param bands: bands to parametrize. If *None* all bands will be
    parametrized.
    :type bands: list

    :return: Function to use in map() or alone
    :rtype: function
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

    # Add the rest of the bands (no parametrized)
    final = image.select(diff).addBands(final)

    return passProperty(image, final, 'system:time_start')


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


def compute_bits(image, start, end, newName):
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


def good_pix(image, retain=None, drop=None, name='good_pix'):
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


class Mapping(object):
    """ Mapping functions to map over ImageCollections """

    # TODO: should be possible to make a general method to map any function
    # that starts with an image

    @staticmethod
    def parametrize(range_from, range_to, bands=None):
        """ Parametrize from a original known range to a fixed new range

        :Parameters:
        :param range_from: Original range. example: (0, 5000)
        :type range_from: tuple
        :param range_to: Fixed new range. example: (500, 1000)
        :type range_to: tuple
        :param bands: bands to parametrize. If *None* all bands will be
        parametrized.
        :type bands: list

        :return: Function to use in map() or alone
        :rtype: function
        """
        def wrap(img):
            return parametrize(img, range_from, range_to, bands)
        return wrap

    @staticmethod
    def renameDict(names):
        """ Renames bands of images using a dict. Can be used in one image or
            in a collection

        :param names: matching names where key is original name and values the
            new name
        :type names: dict
        :return: a function to rename images
        :rtype: function

        :EXAMPLE:

        .. code:: python

            p = ee.Geometry.Point(-71.72029495239258, -42.78997046797438)
            collection = ee.ImageCollection("COPERNICUS/S2").filterBounds(p)
            image = ee.Image(collection.first())

            f = Image.Mapping.rename_bands({"B2":"BLUE", "B3":"GREEN"})
            renamed = collection.map(f)
            i = ee.Image(renamed.first())

            print get_value(image, p)
            print get_value(i, p)

        >> {u'B1': 0.1009, u'B2': 0.078, u'B3': 0.057}
        >> {u'BLUE': 0.1009, u'GREEN': 0.078, u'B3': 0.057}
        """
        def wrap(img):
            return renameDict(img, names)
        return wrap

    @staticmethod
    def sumBands(name="sum", bands=None):
        """ Adds all *bands* values and puts the result on *name*.

        .. code:: python

            col = ee.ImageCollection("LANDSAT/LC8_L1T_TOA_FMASK")
            fsum = Image.Mapping.sumBands("added_bands", ("B1", "B2", "B3"))
            newcol = col.map(fsum)

        :param name: name for the band that contains the added values of bands
        :type name: str
        :param bands: names of the bands to be added. If None (default) it sums
            all bands
        :type bands: tuple
        :return: The function to use in ee.ImageCollection.map()
        :rtype: function
        """
        def wrap(img):
            return sumBands(img, name, bands)
        return wrap

    @staticmethod
    def addConstantBands(value=None, *names, **pairs):
        def apply(img):
            return addConstantBands(img, value, *names, **pairs)
        return apply

    @staticmethod
    def compute_bits(start, end, newName):
        def wrap(img):
            return img.compute_bits(img, start, end, newName)
        return wrap

    @staticmethod
    def good_pix(retain=None, drop=None, name='good_pix'):
        def wrap(img):
            return good_pix(img, retain, drop, name)
        return wrap

