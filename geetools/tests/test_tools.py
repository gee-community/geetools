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

        self.list1 = ee.List([1,2,3,4,5])
        self.list2 = ee.List([4,5,6,7])

    def test_getRegion(self):
        expected = [[0.0,0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]
        pol = ee.Geometry.Polygon(expected)
        feat = ee.Feature(pol)

        region_geom = tools.getRegion(pol)
        region_feat = tools.getRegion(feat)

        self.assertEqual(region_geom, [expected])
        self.assertEqual(region_feat, [expected])

    def test_mask2(self):
        masked_img = self.l8SR.updateMask(self.l8SR.select(["cfmask"]).eq(0))

        mask2zero = tools.mask2zero(masked_img)
        val_no_change = tools.get_value(mask2zero, self.p_l8SR_no_cloud, 30, 'client')["B1"]
        val_change = tools.get_value(mask2zero, self.p_l8SR_cloud, 30, 'client')["B1"]

        self.assertEqual(val_no_change, 517)
        self.assertEqual(val_change, 0)

        mask2num = tools.mask2number(10)(masked_img)
        val_no_change_num = tools.get_value(mask2num, self.p_l8SR_no_cloud, 30, 'client')["B1"]
        val_change_num = tools.get_value(mask2num, self.p_l8SR_cloud, 30, 'client')["B1"]

        self.assertEqual(val_no_change_num, 517)
        self.assertEqual(val_change_num, 10)

    def test_addConstantBands(self):
        newimg = tools.addConstantBands(0, "a", "b", "c")(self.l8SR)
        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals["B1"], 517)
        self.assertEqual(vals["a"], 0)
        self.assertEqual(vals["b"], 0)
        self.assertEqual(vals["c"], 0)

        newimg2 = tools.addConstantBands(a=0, b=1, c=2)(self.l8SR)
        vals2 = tools.get_value(newimg2, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals2["B1"], 517)
        self.assertEqual(vals2["a"], 0)
        self.assertEqual(vals2["b"], 1)
        self.assertEqual(vals2["c"], 2)

        newimg3 = tools.addConstantBands(0, "a", "b", "c", d=1, e=2)(self.l8SR)
        vals3 = tools.get_value(newimg3, self.p_l8SR_no_cloud, 30, 'client')

        self.assertEqual(vals3["B1"], 517)
        self.assertEqual(vals3["a"], 0)
        self.assertEqual(vals3["b"], 0)
        self.assertEqual(vals3["c"], 0)
        self.assertEqual(vals3["d"], 1)
        self.assertEqual(vals3["e"], 2)

    def test_replace(self):
        testband = ee.Image.constant(10).select([0],["anyname"])
        newimg = tools.replace(self.l8SR, "B1", testband)
        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')
        self.assertEqual(vals["B1"], 10)

    def test_sumBands(self):
        newimg = tools.sumBands("added_bands", ("B1", "B2", "B3"))(self.l8SR)

        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')
        suma = int(vals["B1"]) + int(vals["B2"]) + int(vals["B3"])

        self.assertEqual(vals["added_bands"], suma)

    def test_replace_many(self):
        pass

    def test_rename_bands(self):
        i = tools.rename_bands({"B1": "BLUE", "B2": "GREEN"})(self.l8SR)

        vals = tools.get_value(i, self.p_l8SR_no_cloud, 30, 'client')
        bands = i.bandNames().getInfo()

        self.assertEqual(bands, ["BLUE", "GREEN", "B3", "B4", "B5", "B6", "B7",
                                 "cfmask", "cfmask_conf"])
        self.assertEqual(vals["BLUE"], 517)

    def test_pass_prop(self):
        empty1 = ee.Image.constant(0)
        empty2 = ee.Image.constant(0).set("satellite", "None")

        pass1 = tools.pass_prop(self.l8SR, empty1, ["satellite", "WRS_PATH"])
        pass2 = tools.pass_prop(self.l8SR, empty2, ["satellite", "WRS_PATH"])

        self.assertEqual(pass1.get("satellite").getInfo(), "LANDSAT_8")
        self.assertEqual(pass2.get("satellite").getInfo(), "LANDSAT_8")
        self.assertEqual(pass1.get("WRS_PATH").getInfo(), 231)
        self.assertEqual(pass2.get("WRS_PATH").getInfo(), 231)

    def test_list_intersection(self):
        intersection = tools.list_intersection(self.list1, self.list2).getInfo()
        self.assertEqual(intersection, [4, 5])

    def test_list_diff(self):
        diff = tools.list_diff(self.list1, self.list2).getInfo()
        self.assertEqual(diff, [1, 2, 3, 6, 7])

    def test_parametrize(self):
        newimg = tools.parametrize((0, 10000), (0, 1), ["B1", "B2"])(self.l8SR)

        vals = tools.get_value(newimg, self.p_l8SR_no_cloud, 30, 'client')
        self.assertEqual(vals["B1"], 517.0/10000)
        self.assertEqual(vals["B2"], 580.0/10000)
        self.assertEqual(vals["B3"], 824)