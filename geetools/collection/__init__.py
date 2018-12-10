# coding=utf-8
""" Google Earth Engine collections """
import ee
ee.Initialize()

from .. import indices, bitreader


class Collection(object):
    """ Parent class for common operations """
    bands = {}
    range = {}
    scales = {}
    id = None
    start_date = None
    end_date = None
    bits = None
    algorithms = None

    @property
    def collection(self):
        return ee.ImageCollection(self.id)

    @property
    def visualization(self):
        vis = {}
        b = self.bands.get('blue')
        g = self.bands.get('green')
        r = self.bands.get('red')
        n = self.bands.get('nir')
        s = self.bands.get('swir')
        s2 = self.bands.get('swir2')

        if n and s2 and r:
            vis['NSR2'] = {'bands': [n, s2, r], 'min': self.range['min'],
                          'max': self.range['max']/2}

        if n and s and r:
            vis['NSR'] = {'bands': [n, s, r], 'min': self.range['min'],
                          'max': self.range['max']/2}

        if r and g and b:
            vis['RGB'] = {'bands': [r, g, b], 'min': self.range['min'],
                          'max': self.range['max']/3}

        if n and r and g:
            vis['falseColor'] = {'bands': [n, r, g], 'min': self.range['min'],
                                 'max': self.range['max']/2}

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