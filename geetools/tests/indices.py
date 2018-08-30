# coding=utf-8
from __future__ import print_function
import unittest
import ee
from .. import indices
from ..tools.image import get_value
ee.Initialize()
from . import TEST_CLOUD_IMAGES

p = ee.Geometry.Point([-71.69, -42.07])
image = ee.Image(TEST_CLOUD_IMAGES['S2'])
col = ee.ImageCollection('COPERNICUS/S2').filterBounds(p)

class TestIndices(unittest.TestCase):
    def test(self):
        ndvi_i = indices.ndvi('B8', 'B4', addBand=False)(image)
        evi_i = indices.evi('B8', 'B4', 'B2', addBand=False)(image)
        nbr_i = indices.nbr('B8', 'B12', addBand=False)(image)
        nbr2_i = indices.nbr2('B11', 'B12', addBand=False)(image)

        values = get_value(image, p, 10, side='client')

        NIR = float(values['B8'])
        SWIR1 = float(values['B11'])
        SWIR2 = float(values['B12'])
        RED = float(values['B4'])
        BLUE = float(values['B2'])
        GREEN = float(values['B3'])

        ndvi = (NIR-RED)/(NIR+RED)
        evi = (2.5)*((NIR-RED)/(NIR+(6*RED)-((7.5)*BLUE)+1))
        nbr = (NIR-SWIR2)/(NIR+SWIR2)
        nbr2 = (SWIR1-SWIR2)/(SWIR1+SWIR2)

        ndvi_from_i = get_value(ndvi_i, p, 10, 'client')['NDVI']
        evi_from_i = get_value(evi_i, p, 10, 'client')['EVI']
        nbr_from_i = get_value(nbr_i, p, 10, 'client')['NBR']
        nbr2_from_i = get_value(nbr2_i, p, 10, 'client')['NBR2']

        self.assertEqual(ndvi, ndvi_from_i)
        self.assertEqual(evi, evi_from_i)
        self.assertEqual(nbr, nbr_from_i)
        self.assertEqual(nbr2, nbr2_from_i)

class TestMap(unittest.TestCase):
    def test_ndvi(self):
        ndvi_col = col.map(indices.ndvi('B8','B4'))
        ndvi_i = ee.Image(ndvi_col.first())
        values = get_value(ndvi_i, p, 10, side='client')
        NIR = float(values['B8'])
        RED = float(values['B4'])
        ndvi = (NIR-RED)/(NIR+RED)
        ndvi_from_i = get_value(ndvi_i, p, 10, 'client')['NDVI']
        self.assertEqual(ndvi, ndvi_from_i)
