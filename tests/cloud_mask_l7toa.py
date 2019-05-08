# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import getValue
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-71.09680552342795, -42.65765342130262])
p_snow = ee.Geometry.Point([-71.34485556784499, -42.572002133174415])
p_shadow = ee.Geometry.Point([-71.48614073981918, -42.648269348224574])

image = ee.Image(TEST_CLOUD_IMAGES['L7TOA'])


def test_clouds():
    masked = cloud_mask.landsat457ToaBQA(['cloud'])(image)
    vals = getValue(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_shadows():
    masked = cloud_mask.landsat457ToaBQA(['shadow'])(image)
    vals = getValue(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.landsat457ToaBQA(['snow'])(image)
    vals = getValue(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None