# coding=utf-8

import ee
from geetools import cloud_mask
from geetools.tools.image import getValue
from . import TEST_CLOUD_IMAGES

# Initialize
ee.Initialize()

p_cloud = ee.Geometry.Point([-72.35439658020805, -42.909877084944945])
p_shadow = ee.Geometry.Point([-72.40366193088799, -42.8993149292846])
p_snow = ee.Geometry.Point([-72.31921773694792, -42.92788613999289])
p_cirrus = ee.Geometry.Point([-72.36041235428117, -42.90549801791416])

image = ee.Image(TEST_CLOUD_IMAGES['S2'])


def test_clouds():
    masked = cloud_mask.applyHollstein(image, ['cloud'])
    vals = getValue(masked, p_cloud, 30)

    assert vals.get("B1").getInfo() == None


def test_cirrus():
    masked = cloud_mask.applyHollstein(image, ['cirrus'])
    vals = getValue(masked, p_cirrus, 30)

    assert vals.get("B1").getInfo() == None


def test_shadow():
    masked = cloud_mask.applyHollstein(image, ['shadow'])
    vals = getValue(masked, p_shadow, 30)

    assert vals.get("B1").getInfo() == None


def test_snow():
    masked = cloud_mask.applyHollstein(image, ['snow'])
    vals = getValue(masked, p_snow, 30)

    assert vals.get("B1").getInfo() == None