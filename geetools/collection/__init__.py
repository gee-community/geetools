# coding=utf-8
""" Google Earth Engine collections """
import ee
ee.Initialize()

from .. import indices, bitreader


class Collection(object):
    """ Parent class for common operations """
    bands = {}
    ranges = {}
    scales = {}
    id = None
    start_date = None
    end_date = None
    bits = {}
    algorithms = {}
    thermal_bands = []
    quality_bands = []
    optical_bands = []

    @property
    def collection(self):
        """ Google Earth Engine Original Image Collection """
        return ee.ImageCollection(self.id)

    def band_data(self, band):
        """ Data from the parsed band """
        if band in self.bands:
            return {
                'name': self.bands[band],
                'min': self.ranges[band]['min'],
                'max': self.ranges[band]['max'],
                'scale': self.scales[band]
            }

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

    @property
    def ndvi(self, name='ndvi'):
        n = self.bands.get('nir')
        r = self.bands.get('red')
        if n and r:
            return indices.ndvi(n, r, name, False)
        else:
            raise ValueError('ndvi index cannot be computed in {}'.format(
                self.id
            ))

    @property
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

    @property
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

    def bit_image(self, qa, image):
        """ Get an image from the bit information from the qa band """
        if qa not in self.bands.values():
            raise ValueError('{} band not present in {}'.format(
                qa, self.id
            ))

        reader = bitreader.BitReader(self.bit[qa])
        return reader.decode_image(qa, image)


from .landsat import Landsat
from . import landsat