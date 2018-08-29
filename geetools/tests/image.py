# coding=utf-8
import unittest
import ee
from .. import tools_image, tools
ee.Initialize()


class TestImages(unittest.TestCase):
    def setUp(self):
        self.l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")

        # wrap an Image into an tools_image.Image class
        self.l8SRi = tools_image.Image(self.l8SR)

        self.p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
        self.p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

    def test_addConstantBands(self):
        newimg = self.l8SRi.addConstantBands(0, "a", "b", "c")
        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals["B1"], 517)
        self.assertEqual(vals["a"], 0)
        self.assertEqual(vals["b"], 0)
        self.assertEqual(vals["c"], 0)

        newimg2 = self.l8SRi.addConstantBands(a=0, b=1, c=2)
        vals2 = tools.get_value(newimg2, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals2["B1"], 517)
        self.assertEqual(vals2["a"], 0)
        self.assertEqual(vals2["b"], 1)
        self.assertEqual(vals2["c"], 2)

        newimg3 = self.l8SRi.addConstantBands(0, "a", "b", "c", d=1, e=2)
        vals3 = tools.get_value(newimg3, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals3["B1"], 517)
        self.assertEqual(vals3["a"], 0)
        self.assertEqual(vals3["b"], 0)
        self.assertEqual(vals3["c"], 0)
        self.assertEqual(vals3["d"], 1)
        self.assertEqual(vals3["e"], 2)

    def test_replace(self):
        # constant image with value 10 and name 'anyname'
        testband = ee.Image.constant(10).select([0],["anyname"])

        # replace band B1 of l8SR for the testband
        newimg = self.l8SRi.replace("B1", testband)

        # get a value from a point with no clouds
        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        # assert
        self.assertEqual(vals["anyname"], 10)

    def test_sumBands(self):
        newimg = self.l8SRi.sumBands("added_bands", ("B1", "B2", "B3"))

        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')
        suma = int(vals["B1"]) + int(vals["B2"]) + int(vals["B3"])

        self.assertEqual(vals["added_bands"], suma)

    def test_rename_bands(self):
        i = self.l8SRi.renameDict({"B1": "BLUE", "B2": "GREEN"})

        vals = tools.get_value(i, self.p_l8SR_no_cloud, 30, 'client')
        bands = i.bandNames().getInfo()

        self.assertEqual(bands, ["BLUE", "GREEN", "B3", "B4", "B5", "B6", "B7",
                                 "cfmask", "cfmask_conf"])
        self.assertEqual(vals["BLUE"], 517)

    def test_parametrize(self):
        # parametrize
        newimg = self.l8SRi.parametrize((0, 10000), (0, 1), ["B1", "B2"])

        # get a value
        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        # assert
        self.assertEqual(vals["B1"], 517.0/10000)
        self.assertEqual(vals["B2"], 580.0/10000)
        self.assertEqual(vals["B3"], 824)

    def test_minscale(self):
        minscale = self.l8SRi.minscale().getInfo()

        # assert
        self.assertEqual(minscale, 30)