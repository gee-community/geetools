# coding=utf-8

import ee
from geetools.tools.image import getValue
ee.Initialize()


l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")
p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

def test_expressions():
    from geetools import expressions
    generator = expressions.Expression()
    exp_max = generator.max("b('B1')", "b('B2')")
    exp_min = generator.min("b('B1')", "b('B2')")

    img_max = l8SR.expression(exp_max).select([0], ["max"])
    img_min = l8SR.expression(exp_min).select([0], ["min"])

    vals_max = getValue(img_max, p_l8SR_no_cloud, 30, 'client')
    vals_min = getValue(img_min, p_l8SR_no_cloud, 30, 'client')

    assert vals_max["max"] == 580
    assert vals_min["min"] == 517