# coding=utf-8

import ee
from geetools import indices
from geetools.tools.image import get_value
from . import TEST_CLOUD_IMAGES
ee.Initialize()

image = ee.Image(TEST_CLOUD_IMAGES['S2'])
p = image.geometry().centroid()
col = ee.ImageCollection('COPERNICUS/S2').filterBounds(p)


def test_ndvi():
    collection = col.map(indices.ndvi('B8','B4'))
    image = ee.Image(collection.first())
    values = get_value(image, p, 10, side='client')
    NIR = float(values['B8'])
    RED = float(values['B4'])
    index = (NIR-RED)/(NIR+RED)
    index_from_i = get_value(image, p, 10, 'client')['ndvi']

    assert index == index_from_i


def test_evi():
    collection = col.map(indices.evi('B8', 'B4', 'B2'))
    image = ee.Image(collection.first())
    values = get_value(image, p, 10, side='client')
    NIR = float(values['B8'])
    RED = float(values['B4'])
    BLUE = float(values['B2'])

    index = (2.5)*((NIR-RED)/(NIR+(6*RED)-((7.5)*BLUE)+1))
    index_from_i = get_value(image, p, 10, 'client')['evi']

    assert index == index_from_i


def test_nbr():
    collection = col.map(indices.nbr('B8', 'B12'))
    image = ee.Image(collection.first())
    values = get_value(image, p, 10, side='client')
    NIR = float(values['B8'])
    SWIR2 = float(values['B12'])

    index = (NIR-SWIR2)/(NIR+SWIR2)
    index_from_i = get_value(image, p, 10, 'client')['nbr']

    assert index == index_from_i


def test_nbr2():
    collection = col.map(indices.nbr2('B11', 'B12'))
    image = ee.Image(collection.first())
    values = get_value(image, p, 10, side='client')
    SWIR1 = float(values['B11'])
    SWIR2 = float(values['B12'])

    index = (SWIR1-SWIR2)/(SWIR1+SWIR2)
    index_from_i = get_value(image, p, 10, 'client')['nbr2']

    assert index == index_from_i