# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import getValue
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-70.47305608720774, -43.23185291813854])
p_snow = ee.Geometry.Point([-71.45790258078314, -42.65855880983149])
p_shadow = ee.Geometry.Point([-70.80613567662904, -43.01702683734614])

image = ee.Image(TEST_CLOUD_IMAGES['L5SR'])


def test_clouds():
    masked = cloud_mask.landsat457SRPixelQA(['cloud'])(image)
    vals = getValue(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_shadows():
    masked = cloud_mask.landsat457SRPixelQA(['shadow'])(image)
    vals = getValue(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.landsat457SRPixelQA(['snow'])(image)
    vals = getValue(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None