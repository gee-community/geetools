# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-70.47305608720774, -43.23185291813854])
p_snow = ee.Geometry.Point([-71.45790258078314, -42.65855880983149])
p_shadow = ee.Geometry.Point([-70.80613567662904, -43.01702683734614])

image = TEST_CLOUD_IMAGES['L5SR']


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