# coding=utf-8
import unittest
import ee
from .. import tools
ee.Initialize()

class TestTools(unittest.TestCase):

    def setUp(self):
        self.l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")

        self.p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
        self.p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

        self.list1 = ee.List([1, 2, 3, 4, 5])
        self.list2 = ee.List([4, 5, 6, 7])

    def test_getRegion(self):
        expected = [[0.0,0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]
        pol = ee.Geometry.Polygon(expected)
        feat = ee.Feature(pol)

        region_geom = tools.getRegion(pol)
        region_feat = tools.getRegion(feat)

        self.assertEqual(region_geom, [expected])
        self.assertEqual(region_feat, [expected])

    def test_pass_prop(self):
        empty1 = ee.Image.constant(0)
        empty2 = ee.Image.constant(0).set("satellite", "None")

        pass1 = tools.pass_prop(self.l8SR, empty1, ["satellite", "WRS_PATH"])
        pass2 = tools.pass_prop(self.l8SR, empty2, ["satellite", "WRS_PATH"])

        self.assertEqual(pass1.get("satellite").getInfo(), "LANDSAT_8")
        self.assertEqual(pass2.get("satellite").getInfo(), "LANDSAT_8")
        self.assertEqual(pass1.get("WRS_PATH").getInfo(), 231)
        self.assertEqual(pass2.get("WRS_PATH").getInfo(), 231)

if __name__ == '__main__':
    unittest.test()