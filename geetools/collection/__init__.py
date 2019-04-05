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


def info(collection):
    """ Get the information for the parsed collection

    :param collection: the collection to get the information from
    :type collection: Collection
    :rtype: dict
    """
    data = dict()
    data['spacecraft'] = collection.spacecraft
    data['id'] = collection.id
    data['bands'] = collection.bands
    data['band_names'] = collection.band_names
    data['ranges'] = collection.ranges
    data['start_date'] = collection.start_date
    data['end_date'] = collection.end_date
    data['bits'] = collection.bits
    data['algorithms'] = collection.algorithms
    data['thermal_bands'] = collection.thermal_bands
    data['quality_bands'] = collection.quality_bands
    data['optical_bands'] = collection.optical_bands
    data['cloud_cover'] = collection.cloud_cover
    data['scales'] = collection.scales
    data['visualization'] = collection.visualization
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


class Collection(object):
    """ Parent class for common operations """
    # Common properties for all collections
    bands = {}
    ranges = {}
    scales = {}
    spacecraft = None
    id = None
    start_date = None
    end_date = None
    bits = {}
    algorithms = {}
    thermal_bands = {}
    quality_bands = {}
    optical_bands = {}
    cloud_cover = None

    @property
    def collection(self):
        """ Google Earth Engine Original Image Collection """
        return ee.ImageCollection(self.id)

    @property
    def band_names(self):
        """ Band names. The opposite of bands """
        return {v: k for k, v in self.bands.items()}

    def visualization(self, colors, renamed=False):
        """ Return visualization parameters for ui.Map.addLayer.

        :param colors: 'NSR' (nir swir red), 'NSR2' ((nir swir2 red),
            'RGB' (red green blue), 'falseColor' (nir red green)
        """
        options = ['NSR', 'NSR2', 'RGB', 'falseColor', 'SCL']
        vis = {}
        b = self.band_data('blue')
        g = self.band_data('green')
        r = self.band_data('red')
        n = self.band_data('nir')
        s = self.band_data('swir')
        s2 = self.band_data('swir2')
        scl = self.band_data('scene_classification_map')

        def register(one, two, three, factor, name):
            if renamed:
                bandone = one['name']
                bandtwo = two['name']
                bandthree = three['name']
            else:
                bandone = one['band_name']
                bandtwo = two['band_name']
                bandthree = three['band_name']

            vis[name] = {
                'bands': [bandone, bandtwo, bandthree],
                'min': [one['min'], two['min'], three['min']],
                'max': [one['max']/factor, two['max']/factor, three['max']/factor]
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
                band = scl['name']
            else:
                band = scl['band_name']

            vis['SCL'] = {
                'bands': [band],
                'min': scl['min'],
                'max': scl['max'],
                'palette': ['ff0004', '868686', '774b0a', '10d22c',
                            'ffff52', '0000ff', '818181', 'c0c0c0',
                            'f1f1f1', 'bac5eb', '52fff9']
            }

        if colors in options:
            return vis[colors]
        else:
            return {}

    def ndvi(self, name='ndvi'):
        n = self.bands.get('nir')
        r = self.bands.get('red')
        if n and r:
            return indices.ndvi(n, r, name, False)
        else:
            raise ValueError('ndvi index cannot be computed in {}'.format(
                self.id
            ))

    def evi(self, name='evi'):
        n = self.bands.get('nir')
        r = self.bands.get('red')
        b = self.bands.get('blue')
        if n and r and b:
            return indices.evi(n, r, b, bandname=name, addBand=False)
        else:
            raise ValueError('evi index cannot be computed in {}'.format(
                self.id
            ))

    def nbr(self, name='nbr'):
        n = self.bands.get('nir')
        s = self.bands.get('swir2')
        if not s:
            s = self.bands.get('swir')
        if n and s:
            return indices.nbr(n, s, name, False)
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

    def band_data(self, band):
        """ Data from the parsed band """
        name = None
        band_name = None
        min = None
        max = None
        scale = None
        ty = None

        if band in self.bands:
            name = band
            band_name = self.bands[band]
        elif band in self.band_names:
            name = self.band_names[band]
            band_name = band

        if band in self.bands or band in self.band_names:
            min = self.ranges[name]['min']
            max = self.ranges[name]['max']
            scale = self.scales[name]

            # Guess pixel type
            if min >= 0:
                if max <= 255:
                    ty = 'uint8'
                elif max <= 65535:
                    ty = 'uint16'
                elif max <= 4294967295:
                    ty = 'uint32'
            if min < 0:
                if max <= 127:
                    ty = 'int8'
                elif max <= 32767:
                    ty = 'int16'
                elif max <= 2147483647:
                    ty = 'int32'
                elif max <= 9223372036854776000:
                    ty = 'int64'

            if min >= -1 and max <= 1:
                ty = 'double'

        return {
            'name': name,
            'band_name': band_name,
            'min': min,
            'max': max,
            'scale': scale,
            'type': ty
            }

    def bit_image(self, qa, image):
        """ Get an image from the bit information from the qa band

        :param qa: the quality band name
        :type qa: str
        :param image: the image to decode with the qa band
        :type image: ee.Image
        :return: the image with the decode bands added
        """
        if qa not in self.bands.values():
            raise ValueError('{} band not present in {}'.format(
                qa, self.id
            ))

        reader = bitreader.BitReader(self.bits[qa])
        return reader.decode_image(image, qa)

    def check_bands(self, bands):
        """ Check if all bands have the same max and min

        :type collection: Collection
        :type bands: list
        :rtype: bool
        """
        bandsmax = []
        bandsmin = []
        for name, band in bands.items():
            bandmax = self.ranges[name]['max']
            bandmin = self.ranges[name]['min']
            bandsmax.append(bandmax)
            bandsmin.append(bandmin)

        if not allequal(bandsmax) or not allequal(bandsmin):
            return False
        return True

    def rename_optical(self, image):
        """ Rename the optical bands of an image (with original bands from EE
            collection)

        :param image: the image that holds the original bands from EE
        :type image: ee.Image
        :return: the parsed image with the optical bands renamed
        :rtype: ee.Image
        """
        original_names = {v: k for k, v in self.optical_bands.items()}
        return tools.image.renameDict(image, original_names)

    def rename_thermal(self, image):
        """ Rename the thermal bands of an image (with original bands from EE
            collection)

        :param image: the image that holds the original bands from EE
        :type image: ee.Image
        :return: the parsed image with the thermal bands renamed
        :rtype: ee.Image
        """
        original_names = {v: k for k, v in self.thermal_bands.items()}
        return tools.image.renameDict(image, original_names)

    def rename_quality(self, image):
        """ Rename the quality bands of an image (with original bands from EE
            collection)

        :param image: the image that holds the original bands from EE
        :type image: ee.Image
        :return: the parsed image with the quality bands renamed
        :rtype: ee.Image
        """
        original_names = {v: k for k, v in self.quality_bands.items()}
        return tools.image.renameDict(image, original_names)

    def rename_all(self, image):
        """ Rename all bands of an image (with original bands from EE
            collection)

        :param image: the image that holds the original bands from EE
        :type image: ee.Image
        :return: the parsed image with the all bands renamed
        :rtype: ee.Image
        """
        optical = self.rename_optical(image)
        thermal = self.rename_thermal(optical)
        quality = self.rename_quality(thermal)

        return quality

    def proxy_image(self):
        """ Create an Image with the band names, type and scale but empty """



from .landsat import *
from .sentinel import *
from . import landsat, sentinel


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


def get_common_bands(*collections, type_of_band=None):
    """ Get the common bands of the parsed collections """
    first = collections[0]
    if type_of_band == 'optical':
        first_bands = first.optical_bands
    elif type_of_band == 'thermal':
        first_bands = first.thermal_bands
    elif type_of_band == 'quality':
        first_bands = first.quality_bands
    else:
        first_bands = first.bands

    first_set = set(first_bands.keys())
    if (len(collections) == 1):
        return first_bands
    else:
        rest = collections[1:]
        for col in rest:
            if type_of_band == 'optical':
                bands = col.optical_bands
            elif type_of_band == 'thermal':
                bands = col.thermal_bands
            elif type_of_band == 'quality':
                bands = col.quality_bands
            else:
                bands = col.bands
            bandset = set(bands.keys())
            first_set = first_set.intersection(bandset)

    return list(first_set)



def rescale(image, col, collection_to_match, renamed=False, drop=False):
    """ Re-scale the values of image which must belong to collection so the
        values match the ones from collection_from

    :param collection: The Collection to which belongs the image
    :type collection: Collection
    :param collection_to_match: the Collection to get the range from
    :type collection_to_match: Collection
    """
    # Create comparative collection
    bands = ee.Dictionary(col.bands)

    common_optical_bands = ee.List(get_common_bands(col, collection_to_match,
                                                    type_of_band='optical'))
    common_thermal_bands = ee.List(get_common_bands(col, collection_to_match,
                                                    type_of_band='thermal'))
    common_bands = common_optical_bands.cat(common_thermal_bands)

    ranges_this = ee.Dictionary(col.ranges)
    ranges_proxy = ee.Dictionary(collection_to_match.ranges)

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

        def false(ini, bands, band, min_this, max_this, min_proxy, max_proxy):
            if not renamed:
                band = ee.String(bands.get(band))

            return tools.image.parametrize(ini,
                                           (min_this, max_this),
                                           (min_proxy, max_proxy),
                                           bands=[band])

        return ee.Image(ee.Algorithms.If(
            equal, true(ini),
            false(ini, bands, band, min_this, max_this, min_proxy, max_proxy)))

    final = ee.Image(common_bands.iterate(iteration, image))
    if drop:
        if not renamed:
            common_bands = tools.dictionary.extractList(col.bands,
                                                        common_bands)
        final = final.select(common_bands)

    return final

from .group import CollectionGroup