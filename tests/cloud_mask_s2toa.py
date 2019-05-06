# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import assert_equal

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-71.44110783027168, -42.760436204035514])
p_cirrus = ee.Geometry.Point([-71.90539080580817, -43.02237648453567])

image = ee.Image('COPERNICUS/S2/20150825T143316_20150825T144048_T18GYT')


def test_clouds():
    masked = cloud_mask.sentinel2(['cloud'])(image)
    vals = get_value(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_cirrus():
    masked = cloud_mask.sentinel2(['cirrus'])(image)
    vals = get_value(masked, p_cirrus, 30)

    assert vals.get("B1").getInfo() == None