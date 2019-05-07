# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-70.15588363762427, -42.98086920709981])
p_snow = ee.Geometry.Point([-69.9144023012539, -42.73663097771261])
p_shadow = ee.Geometry.Point([-70.3042273263779, -42.70884337439131])

image = TEST_CLOUD_IMAGES['L8TOA']


def test_clouds():
    masked = cloud_mask.landsat8TOA_BQA(['cloud'])(image)
    vals = get_value(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_shadows():
    masked = cloud_mask.landsat8TOA_BQA(['shadow'])(image)
    vals = get_value(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.landsat8TOA_BQA(['snow'])(image)
    vals = get_value(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None