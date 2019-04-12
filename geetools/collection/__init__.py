# coding=utf-8
""" Google Earth Engine collections """
import ee
ee.Initialize()

from .. import indices, bitreader
from datetime import date


TODAY = date.today().isoformat()
PIXEL_TYPES = {
    'float': ee.Image.toFloat,
    'double': ee.Image.toDouble,
    'int8': ee.Image.toInt8,
    'uint8': ee.Image.toUint8,
    'int16': ee.Image.toInt16,
    'uint16': ee.Image.toUint16,
    'int32': ee.Image.toInt32,
    'uint32': ee.Image.toUint32,
    'int64': ee.Image.toInt64
}


# HELPERS
def allequal(iterable):
    """ Check if all elements inside an iterable are equal """
    first = iterable[0]
    rest = iterable[1:]
    for item in rest:
        if item == first: continue
        else: return False
    return True


def convert_precision(image, precision):
    """ Convert data type precisions """
    TYPES = ee.Dictionary({'float': image.toFloat(),
                           'double': image.toDouble(),
                           'int8': image.toInt8(),
                           'uint8': image.toUint8(),
                           'uint16': image.toUint16(),
                           'int16': image.toInt16(),
                           'uint32': image.toUint32(),
                           'int32': image.toInt32(),
                           'int64': image.toInt64()
                           })
    return ee.Image(TYPES.get(precision))


def convert_precisions(image, precision_dict):
    precisions = ee.Dictionary(precision_dict)
    bands = ee.List(precisions.keys())
    def iteration(band, ini):
        ini = ee.Image(ini)
        imgband = ini.select([band])
        precision = ee.String(precisions.get(band))
        newband = convert_precision(imgband, precision)
        return tools.image.replace(ini, band, newband)

    return ee.Image(bands.iterate(iteration, image))


def info(collection, renamed=False):
    """ Get the information for the parsed collection

    :param collection: the collection to get the information from
    :type collection: Collection
    :rtype: dict
    """
    data = dict()
    data['spacecraft'] = collection.spacecraft
    data['id'] = collection.id
    data['bands'] = [b.id for b in collection.bands]
    data['band_names'] = [b.name for b in collection.bands]
    data['ranges'] = collection.ranges(renamed=renamed)
    data['scales'] = collection.scales(renamed=renamed)
    data['start_date'] = collection.start_date
    data['end_date'] = collection.end_date
    data['algorithms'] = collection.algorithms
    if not renamed:
        data['thermal_bands'] = [b.id for b in collection.thermal_bands]
        data['bit_bands'] = [b.id for b in collection.bit_bands]
        data['optical_bands'] = [b.id for b in collection.optical_bands]
        data['classification_bands'] = [b.id for b in collection.classification_bands]
    else:
        data['thermal_bands'] = [b.name for b in collection.thermal_bands]
        data['bit_bands'] = [b.name for b in collection.bit_bands]
        data['optical_bands'] = [b.name for b in collection.optical_bands]
        data['classification_bands'] = [b.name for b in collection.classification_bands]

    data['cloud_cover'] = collection.cloud_cover
    data['ee_collection'] = collection.collection
    data['indices'] = collection.indices

    if (collection.spacecraft == 'LANDSAT'):
        data['sensor'] = collection.sensor
        data['process'] = collection.process
        data['tier'] = collection.tier
        data['number'] = collection.number

    if (collection.spacecraft == 'SENTINEL'):
        data['number'] = collection.number
        if collection.number == 2:
            data['process'] = collection.process
            if collection.process == 'SR':
                data['SCL'] = collection.SCL_data
    return data


def infoEE(collection):
    """ Return an information ee.Dictionary """
    information = info(collection)
    information.pop('algorithms')
    information.pop('ee_collection')
    information.pop('indices')
    information.pop('visualization')

    return ee.Dictionary(information)


class Band(object):
    """ Bands """
    def __init__(self, id, name, precision=None, scale=None,
                 min=None, max=None, reference=None, bits=None):
        self.id = id
        self.name = name
        self.precision = precision
        self.max = max
        self.min = min
        self.scale = scale
        self.reference = reference # thermal, optical or quality
        self.bits = bits


class Collection(object):
    """ Parent class for common operations """
    def __init__(self, **kwargs):
        self._bands = None
        self._id = None
        self.spacecraft = kwargs.get('spacecraft', None)
        self.start_date = kwargs.get('start_date', None)
        self.end_date = kwargs.get('end_date', None)
        self.cloud_cover = kwargs.get('cloud_cover', None)
        self.algorithms = kwargs.get('algorithms', {})
        self.masks = kwargs.get('masks', {
            'cloud': {},
            'shadow': {},
            'snow': {},
            'water': {},
            'cirrus': {}
        })

    @property
    def bands(self):
        if not self._bands:
            self._bands = None
        return self._bands

    @property
    def id(self):
        """ Google Earth Engine ID """
        if not self._id:
            self._id = None
        return self._id

    @property
    def collection(self):
        """ Google Earth Engine Original Image Collection """
        return ee.ImageCollection(self.id)

    @property
    def optical_bands(self):
        return [band for band in self.bands if band.reference == 'optical']

    @property
    def thermal_bands(self):
        return [band for band in self.bands if band.reference == 'thermal']

    @property
    def bit_bands(self):
        return [band for band in self.bands if band.reference == 'bits']

    @property
    def classification_bands(self):
        return [band for band in self.bands if band.reference == 'classification']

    def band_names(self, reference='all', renamed=False):
        """ List of band names """
        if reference == 'all':
            if not renamed:
                bands = [band.id for band in self.bands]
            else:
                bands = [band.name for band in self.bands]
        else:
            if not renamed:
                bands = [band.id for band in self.bands if band.reference == reference]
            else:
                bands = [band.name for band in self.bands if band.reference == reference]
        return bands

    def precisions(self, reference='all', renamed=False):
        precisions_dict = {}
        for band in self.bands:
            if reference != 'all' and reference != band.reference:
                continue
            if not renamed:
                name = band.id
            else:
                name = band.name

            precisions_dict[name] = band.precision

        return precisions_dict

    def ranges(self, reference='all', renamed=False):
        ranges_dict = {}
        for band in self.bands:
            if reference != 'all' and reference != band.reference:
                continue
            if not renamed:
                name = band.id
            else:
                name = band.name

            ranges_dict[name] = {'min': band.min, 'max': band.max}

        return ranges_dict

    def scales(self, reference='all', renamed=False):
        scales_dict = {}
        for band in self.bands:
            if reference != 'all' and reference != band.reference:
                continue
            if not renamed:
                name = band.id
            else:
                name = band.name

            scales_dict[name] = band.scale

        return scales_dict

    def bit_options(self, renamed=False):
        options = {}
        for band in self.bands:
            if band.reference == 'bits' and band.bits:
                name = band.name if renamed else band.id
                opt = []
                for allclss in band.bits.values():
                    for _, clss in allclss.items():
                        opt.append(clss)
                options[name] = opt
        return options

    def get_mask(self, image, mask_band, classes='all', renamed=False):
        """ Get a mask image """
        bandnames = self.band_names(renamed=renamed)

        # CHECKS
        if mask_band not in bandnames:
            msg = 'band {} not present in bands {}'
            raise ValueError(msg.format(mask_band, bandnames))
        options = self.bit_options(renamed)[mask_band]
        if classes != 'all' and classes != ['all']:
            if not isinstance(classes, (list, tuple)):
                msg = 'classes param must be "all" or a list of classes'
                raise ValueError(msg)
            for clas in classes:
                if clas not in options:
                    msg = 'class {} not available for band {}, only {}'
                    raise ValueError(msg.format(clas, mask_band, options))

        if classes == 'all' or classes == ['all']:
            selection = options
        else:
            selection = classes

        mask = self.bit_image(image, mask_band, renamed).select(selection)
        return mask

    def apply_mask(self, image, mask_band, classes='all', renamed=False):
        """ Apply a mask """
        mask = self.get_mask(image, mask_band, classes, renamed)
        options = mask.bandNames()

        def wrap(band, img):
            img = ee.Image(img)
            band = ee.String(band)
            m = mask.select(band)
            return img.updateMask(m.Not())

        return ee.Image(options.iterate(wrap, image))

    def get_band(self, band, by='id'):
        """ get a band by its id or name """
        data = None
        for b in self.bands:
            if by == 'name':
                bid = b.name
            else:
                bid = b.id

            if bid == band:
                data = b

        return data

    def visualization(self, colors, renamed=False):
        """ Return visualization parameters for ui.Map.addLayer.

        :param colors: 'NSR' (nir swir red), 'NSR2' ((nir swir2 red),
            'RGB' (red green blue), 'falseColor' (nir red green)
        """
        options = ['NSR', 'NSR2', 'RGB', 'falseColor', 'SCL']
        vis = {}
        b = self.get_band('blue', 'name')
        g = self.get_band('green', 'name')
        r = self.get_band('red', 'name')
        n = self.get_band('nir', 'name')
        s = self.get_band('swir', 'name')
        s2 = self.get_band('swir2', 'name')
        scl = self.get_band('scene_classification_map', 'name')

        def register(one, two, three, factor, name):
            if renamed:
                bandone = one.name
                bandtwo = two.name
                bandthree = three.name
            else:
                bandone = one.id
                bandtwo = two.id
                bandthree = three.id

            vis[name] = {
                'bands': [bandone, bandtwo, bandthree],
                'min': [one.min, two.min, three.min],
                'max': [one.max/factor, two.max/factor, three.max/factor]
            }

        if n and s2 and r:
            register(n, s2, r, 2, 'NSR2')

        if n and s and r:
            register(n, s, r, 2, 'NSR')

        if r and g and b:
            register(r, g, b, 3, 'RGB')

        if n and r and g:
            register(n, r, g, 2, 'falseColor')

        if scl:
            if renamed:
                band = scl.name
            else:
                band = scl.id

            vis['SCL'] = {
                'bands': [band],
                'min': scl.min,
                'max': scl.max,
                'palette': ['ff0004', '868686', '774b0a', '10d22c',
                            'ffff52', '0000ff', '818181', 'c0c0c0',
                            'f1f1f1', 'bac5eb', '52fff9']
            }

        if colors in options:
            return vis[colors]
        else:
            return {}

    def ndvi(self, image, name='ndvi', renamed=False):
        if renamed:
            n = 'nir'
            r = 'red'
        else:
            n = self.get_band('nir', 'name').id
            r = self.get_band('red', 'name').id
        if n and r:
            return indices.ndvi(n, r, name, False)(image)
        else:
            raise ValueError('ndvi index cannot be computed in {}'.format(
                self.id
            ))

    def evi(self, image, name='evi', renamed=False):
        if renamed:
            n = 'nir'
            r = 'red'
            b = 'blue'
        else:
            n = self.get_band('nir', 'name').id
            r = self.get_band('red', 'name').id
            b = self.get_band('blue', 'name').id
        if n and r and b:
            return indices.evi(n, r, b, bandname=name, addBand=False)(image)
        else:
            raise ValueError('evi index cannot be computed in {}'.format(
                self.id
            ))

    def nbr(self, image, name='nbr', renamed=False):
        if renamed:
            n = 'nir'
            s = 'swir2'
            if not s:
                s = 'swir'
        else:
            n = self.get_band('nir', 'name').id
            s = self.get_band('swir2', 'name').id
            if not s:
                s = self.get_band('swir', 'name').id
        if n and s:
            return indices.nbr(n, s, name, False)(image)
        else:
            raise ValueError('nbr index cannot be computed in {}'.format(
                self.id
            ))

    # common indices
    indices = {
        'ndvi': ndvi,
        'evi': evi,
        'nbr': nbr
    }

    def bit_image(self, image, qa, renamed=False):
        """ Get an image from the bit information from the qa band

        :param qa: the quality band name
        :type qa: str
        :param image: the image to decode with the qa band
        :type image: ee.Image
        :return: the image with the decode bands added
        """
        if renamed:
            band = self.get_band(qa, 'name')
        else:
            band = self.get_band(qa, 'id')

        if not band:
            raise ValueError('{} band not present in {}'.format(
                qa, self.id
            ))

        reader = bitreader.BitReader(band.bits)
        return reader.decode_image(image, qa)

    def check_bands(self, bands):
        """ Check if all bands have the same max and min

        :type collection: Collection
        :type bands: list
        :rtype: bool
        """
        bandsmax = []
        bandsmin = []
        for band in bands:
            bandmax = band.max
            bandmin = band.min
            bandsmax.append(bandmax)
            bandsmin.append(bandmin)

        if not allequal(bandsmax) or not allequal(bandsmin):
            return False
        return True

    def rename(self, image, reference='all'):
        """ Rename bands according to the parsed reference. It can be:
        optical, thermal, bits, all """
        if reference == 'all':
            original_names = {band.id: band.name for band in self.bands}
        else:
            original_names = {band.id: band.name for band in self.bands if band.reference == reference}

        return tools.image.renameDict(image, original_names)

    def proxy_image(self, renamed=False):
        """ Create an Image with the band names, type and scale but empty """
        precisions = self.precisions(renamed=renamed)
        first_band = self.bands[0]
        if not renamed:
            name = first_band.id
        else:
            name = first_band.name

        init = ee.Image.constant(0).rename(name)
        init = convert_precision(init, precisions[name])
        for i, band in enumerate(self.bands):
            if i == 0: continue
            if not renamed:
                name = band.id
            else:
                name = band.name

            img = ee.Image.constant(0).rename(name)
            img = convert_precision(img, precisions[name])
            init = init.addBands(img)

        return init


from .landsat import *
from .sentinel import *
from . import landsat, sentinel
from .landsat import Landsat
from .sentinel import Sentinel2

IDS = landsat.IDS + sentinel.IDS


def from_id(id):
    """ Create a collection from a parsed ID """
    functions = [
        landsat.Landsat.fromId,
        sentinel.Sentinel2.fromId
    ]
    for f in functions:
        try:
            col = f(id)
        except:
            continue
        else:
            return col

    # tried all collections and did not find it
    raise ValueError('{} not recognized as a valid ID'.format(id))


def get_common_bands(*collections, reference='all', match='id'):
    """ Get the common bands of the parsed collections

    :param match: the field to match, can be: id or name
    :type match: str
    """
    first = collections[0]

    renamed = True if match == 'name' else False

    first_set = set(first.band_names(reference, renamed))
    if len(collections) == 1:
        return first.band_names
    else:
        rest = collections[1:]
        for col in rest:
            bandset = set(col.band_names(reference, renamed))
            first_set = first_set.intersection(bandset)

    return list(first_set)


def rescale(image, col, collection_to_match, reference='all', renamed=False,
            drop=False):
    """ Re-scale the values of image which must belong to collection so the
        values match the ones from collection_from

    :param collection: The Collection to which belongs the image
    :type collection: Collection
    :param collection_to_match: the Collection to get the range from
    :type collection_to_match: Collection
    :param reference: optical, thermal, bits or all
    :type reference: str
    """
    # Create comparative collection
    # bands = ee.Dictionary(col.bands)
    common_bands = get_common_bands(col, collection_to_match,
                                    reference=reference, match='name')
    # keep only bands with min and max values
    new_common = []

    ranges = {}
    ranges_other = {}

    def setrange(band, range_dict):
        if not renamed:
            name = band.id
        else:
            name = band.name

        range_dict[name] = {'min': band.min, 'max': band.max}

    precisions = {}
    for band in common_bands:
        b = col.get_band(band, 'name')
        b_proxy = collection_to_match.get_band(band, 'name')
        if b.min is not None and \
                b.max is not None and \
                b_proxy.min is not None and \
                b_proxy.max is not None:
            if not renamed:
                name = b.id
            else:
                name = b.name
            new_common.append(name)
            setrange(b, ranges)
            setrange(b_proxy, ranges_other)
            precisions[name] = b_proxy.precision

    new_common = ee.List(new_common)
    ranges_this = ee.Dictionary(ranges)
    ranges_proxy = ee.Dictionary(ranges_other)
    precisions = ee.Dictionary(precisions)

    def iteration(band, ini):
        ini = ee.Image(ini)
        band = ee.String(band)
        ranges_this_band = ee.Dictionary(ranges_this.get(band))
        ranges_proxy_band = ee.Dictionary(ranges_proxy.get(band))
        min_this = ee.Number(ranges_this_band.get('min'))
        min_proxy = ee.Number(ranges_proxy_band.get('min'))
        max_this = ee.Number(ranges_this_band.get('max'))
        max_proxy = ee.Number(ranges_proxy_band.get('max'))

        equal_min = min_this.eq(min_proxy)
        equal_max = max_this.eq(max_proxy)
        equal = equal_min.And(equal_max)

        def true(ini):
            return ini

        def false(ini, band, min_this, max_this, min_proxy, max_proxy):
            return tools.image.parametrize(ini,
                                           (min_this, max_this),
                                           (min_proxy, max_proxy),
                                           bands=[band])

        return ee.Image(ee.Algorithms.If(
            equal, true(ini),
            false(ini, band, min_this, max_this, min_proxy, max_proxy)))

    final = ee.Image(new_common.iterate(iteration, image))
    final = convert_precisions(final, precisions)
    if drop:
        final = final.select(new_common)

    return final

from .group import CollectionGroup

# Preload factory methods
Landsat1 = Landsat.Landsat1
Landsat2 = Landsat.Landsat2
Landsat3 = Landsat.Landsat3
Landsat4SR = Landsat.Landsat4SR
Landsat4TOA = Landsat.Landsat4TOA
Landsat5SR = Landsat.Landsat5SR
Landsat5TOA = Landsat.Landsat5TOA
Landsat7SR = Landsat.Landsat7SR
Landsat7TOA = Landsat.Landsat7TOA
Landsat8SR = Landsat.Landsat8SR
Landsat8TOA = Landsat.Landsat8TOA
Sentinel2TOA = Sentinel2.Sentinel2TOA
Sentinel2SR = Sentinel2.Sentienl2SR