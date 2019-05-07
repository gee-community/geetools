# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-71.67030933850714, -42.92352111915706])
p_snow = ee.Geometry.Point([-71.75856720476548, -42.93871143148904])
p_shadow = ee.Geometry.Point([-71.67144910085082, -43.0356524986155])

image = TEST_CLOUD_IMAGES['L4SR']


def test_clouds():
    masked = cloud_mask.landsat457SR_pixelQA(['cloud'])(image)
    vals = get_value(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_shadows():
    masked = cloud_mask.landsat457SR_pixelQA(['shadow'])(image)
    vals = get_value(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.landsat457SR_pixelQA(['snow'])(image)
    vals = get_value(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None