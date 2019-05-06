# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import assert_equal

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-71.67030933850714, -42.92352111915706])
p_snow = ee.Geometry.Point([-71.75856720476548, -42.93871143148904])
p_shadow = ee.Geometry.Point([-71.67144910085082, -43.0356524986155])

image = ee.Image('LANDSAT/LT04/C01/T1_TOA/LT04_231077_19890725')


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