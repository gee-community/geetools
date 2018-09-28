# coding=utf-8
import unittest
import ee
from ..tools.image import get_value
ee.Initialize()

class TestExpressions(unittest.TestCase):

    def setUp(self):
        self.l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")
        self.p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

    def test_expressions(self):
        from geetools import expressions
        generator = expressions.Expression()
        exp_max = generator.max("b('B1')", "b('B2')")
        exp_min = generator.min("b('B1')", "b('B2')")

        img_max = self.l8SR.expression(exp_max).select([0], ["max"])
        img_min = self.l8SR.expression(exp_min).select([0], ["min"])

        vals_max = get_value(img_max, self.p_l8SR_no_cloud, 30, 'client')
        vals_min = get_value(img_min, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals_max["max"], 580)
        self.assertEqual(vals_min["min"], 517)

if __name__ == '__main__':
    unittest.test()