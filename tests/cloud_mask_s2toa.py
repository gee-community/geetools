# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import getValue
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-71.44110783027168, -42.760436204035514])
p_cirrus = ee.Geometry.Point([-71.90539080580817, -43.02237648453567])

image = ee.Image(TEST_CLOUD_IMAGES['S2'])


def test_clouds():
    masked = cloud_mask.sentinel2(['cloud'])(image)
    vals = getValue(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_cirrus():
    masked = cloud_mask.sentinel2(['cirrus'])(image)
    vals = getValue(masked, p_cirrus, 30)

    assert vals.get("B1").getInfo() == None