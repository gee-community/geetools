# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import get_value
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-72.35439658020805, -42.909877084944945])
p_shadow = ee.Geometry.Point([-72.40366193088799, -42.8993149292846])
p_snow = ee.Geometry.Point([-72.31921773694792, -42.92788613999289])
p_cirrus = ee.Geometry.Point([-72.36041235428117, -42.90549801791416])

image = TEST_CLOUD_IMAGES['S2']


def test_clouds():
    masked = cloud_mask.apply_hollstein(image, ['cloud'])
    vals = get_value(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_cirrus():
    masked = cloud_mask.apply_hollstein(image, ['cirrus'])
    vals = get_value(masked, p_cirrus, 30)

    assert vals.get("B1").getInfo() == None


def test_shadow():
    masked = cloud_mask.apply_hollstein(image, ['shadow'])
    vals = get_value(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.apply_hollstein(image, ['snow'])
    vals = get_value(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None