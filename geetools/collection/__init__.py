# coding=utf-8
""" Google Earth Engine collections """
import ee
ee.Initialize()

from .. import indices, bitreader


# HELPERS
def allequal(iterable):
    """ Check if all elements inside an iterable are equal """
    first = iterable[0]
    rest = iterable[1:]
    for item in rest:
        if item == first: continue
        else: return False
        first = item
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

    @property
    def visualization(self):
        vis = {}
        b = self.band_data('blue')
        g = self.band_data('green')
        r = self.band_data('red')
        n = self.band_data('nir')
        s = self.band_data('swir')
        s2 = self.band_data('swir2')

        def register(one, two, three, factor, name):
            vis[name] = {
                'bands': [one['name'], two['name'], three['name']],
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

        return vis

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
        if band in self.bands:
            return {
                'name': band,
                'band_name': self.bands[band],
                'min': self.ranges[band]['min'],
                'max': self.ranges[band]['max'],
                'scale': self.scales[band]
            }
        elif band in self.band_names:
            name = self.band_names[band]
            return {
                'name': name,
                'band_name': band,
                'min': self.ranges[name]['min'],
                'max': self.ranges[name]['max'],
                'scale': self.scales[name]
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