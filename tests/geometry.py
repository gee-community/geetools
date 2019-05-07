# coding=utf-8

import ee
from geetools.tools.geometry import getRegion
ee.Initialize()

l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")

p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

list1 = ee.List([1, 2, 3, 4, 5])
list2 = ee.List([4, 5, 6, 7])


def test_getRegion():
    expected = [[0.0,0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]
    pol = ee.Geometry.Polygon(expected)
    feat = ee.Feature(pol)

    region_geom = getRegion(pol)
    region_feat = getRegion(feat)

    assert region_geom == [expected]
    assert region_feat == [expected]