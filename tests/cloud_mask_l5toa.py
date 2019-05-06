# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import assert_equal

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-69.7850919885049, -42.74847761369703])
p_snow = ee.Geometry.Point([-69.95680141007878, -43.08818524620294])
p_shadow = ee.Geometry.Point([-69.85037130586764, -42.78657084334236])

image = ee.Image('LANDSAT/LT05/C01/T1_TOA/LT05_231090_19860810')


def test_clouds():
    masked = cloud_mask.landsat457TOA_BQA(['cloud'])(image)
    vals = get_value(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_shadows():
    masked = cloud_mask.landsat457TOA_BQA(['shadow'])(image)
    vals = get_value(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.landsat457TOA_BQA(['snow'])(image)
    vals = get_value(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None