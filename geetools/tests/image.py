# coding=utf-8
import unittest
import ee
from .. import tools
ee.Initialize()


class TestImages(unittest.TestCase):
    def setUp(self):
        self.l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")

        self.p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
        self.p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

    def test_addConstantBands(self):
        newimg = tools.image.addConstantBands(self.l8SR, 0, "a", "b", "c")
        vals = tools.image.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals["B1"], 517)
        self.assertEqual(vals["a"], 0)
        self.assertEqual(vals["b"], 0)
        self.assertEqual(vals["c"], 0)

        newimg2 = tools.image.addConstantBands(self.l8SR, a=0, b=1, c=2)
        vals2 = tools.image.get_value(newimg2, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals2["B1"], 517)
        self.assertEqual(vals2["a"], 0)
        self.assertEqual(vals2["b"], 1)
        self.assertEqual(vals2["c"], 2)

        newimg3 = tools.image.addConstantBands(self.l8SR, 0, "a", "b", "c", d=1, e=2)
        vals3 = tools.image.get_value(newimg3, self.p_l8SR_no_cloud, 30, 'client')

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
        newimg = tools.image.replace(self.l8SR, "B1", testband)

        # get a value from a point with no clouds
        vals = tools.image.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        # assert
        self.assertEqual(vals["anyname"], 10)

    def test_sumBands(self):
        newimg = tools.image.sumBands(self.l8SR, "added_bands", ("B1", "B2", "B3"))

        vals = tools.image.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')
        suma = int(vals["B1"]) + int(vals["B2"]) + int(vals["B3"])

        self.assertEqual(vals["added_bands"], suma)

    def test_rename_bands(self):
        # Check original
        original_bands = self.l8SR.bandNames().getInfo()
        self.assertEqual(original_bands,
                         ["B1", "B2", "B3", "B4", "B5", "B6", "B7",
                          "cfmask", "cfmask_conf"])

        # rename
        i = tools.image.renameDict(self.l8SR, {"B1": "BLUE", "B2": "GREEN"})

        # get value from point in a cloud free zone
        vals = tools.image.get_value(i, self.p_l8SR_no_cloud, 30, 'client')

        # get new band names
        bands = i.bandNames().getInfo()

        expected = ["BLUE", "GREEN", "B3", "B4", "B5", "B6", "B7",
                    "cfmask", "cfmask_conf"]

        self.assertEqual(bands, expected)
        self.assertEqual(vals["BLUE"], 517)

    def test_parametrize(self):
        # parametrize
        newimg = tools.image.parametrize(self.l8SR, (0, 10000), (0, 1), ["B1", "B2"])

        # get a value
        vals = tools.image.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        # assert
        self.assertEqual(vals["B1"], 517.0/10000)
        self.assertEqual(vals["B2"], 580.0/10000)
        self.assertEqual(vals["B3"], 824)

    def test_minscale(self):
        minscale = tools.image.minscale(self.l8SR).getInfo()

        # assert
        self.assertEqual(minscale, 30)

    def test_pass_prop(self):
        empty1 = ee.Image.constant(0)
        empty2 = ee.Image.constant(0).set("satellite", "None")

        pass1 = tools.image.passProperty(self.l8SR, empty1,
                                         ["satellite", "WRS_PATH"])
        pass2 = tools.image.passProperty(self.l8SR, empty2,
                                         ["satellite", "WRS_PATH"])

        self.assertEqual(pass1.get("satellite").getInfo(), "LANDSAT_8")
        self.assertEqual(pass2.get("satellite").getInfo(), "LANDSAT_8")
        self.assertEqual(pass1.get("WRS_PATH").getInfo(), 231)
        self.assertEqual(pass2.get("WRS_PATH").getInfo(), 231)