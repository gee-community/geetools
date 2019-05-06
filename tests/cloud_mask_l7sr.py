# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import assert_equal

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-71.09680552342795, -42.65765342130262])
p_snow = ee.Geometry.Point([-71.34485556784499, -42.572002133174415])
p_shadow = ee.Geometry.Point([-71.48614073981918, -42.648269348224574])

image = ee.Image('LANDSAT/LE07/C01/T1_SR/LE07_231090_19990907')


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