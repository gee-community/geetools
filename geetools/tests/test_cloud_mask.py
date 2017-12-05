# coding=utf-8
import unittest
import ee
from geetools import tools
ee.Initialize()

class TestCloudMask(unittest.TestCase):

    def setUp(self):
        self.l1 = ee.Image("LANDSAT/LM1_L1T/LM12500851973064AAA05")
        self.l2 = ee.Image("LANDSAT/LM2_L1T/LM22480891976038FAK05")
        self.l3 = ee.Image("LANDSAT/LM3_L1T/LM32490891979068XXX01")
        self.l4toa = ee.Image("LANDSAT/LT4_L1T_TOA_FMASK/LT42310911992007XXX02")
        self.l5SR = ee.Image("LANDSAT/LT5_SR/LT52310772000341")
        self.l5led = ee.Image("LEDAPS/LT5_L1T_SR/LT52310901984169XXX03")
        self.l5toa = ee.Image("LANDSAT/LT5_L1T_TOA_FMASK/LT52320881999345COA00")
        self.l7SR = ee.Image("LANDSAT/LE7_SR/LE72300782012135")
        self.l7led = ee.Image("LEDAPS/LE7_L1T_SR/LE72300781999227CUB00")
        self.l7toa = ee.Image("LANDSAT/LE7_L1T_TOA_FMASK/LE72300781999227CUB00")
        self.l8toa = ee.Image("LANDSAT/LC8_L1T_TOA_FMASK/LC82310902013344LGN00")
        self.l8SR = ee.Image("LANDSAT/LC8_SR/LC82310772014043")
        self.sentinel2 = ee.Image("COPERNICUS/S2/20160122T144426_20160127T174646_T18GYT")
        self.modis_terra = ee.Image("MODIS/MOD09GA/MOD09GA_005_2000_02_24")
        self.modis_aqua = ee.Image("MODIS/MYD09GA/MYD09GA_005_2002_07_04")

        self.p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
        self.p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

    def test_cloud_mask(self):
        from geetools import cloud_mask
        # LANDSAT 4 TOA
        masked_l4toa = cloud_mask.fmask("fmask")(self.l4toa)
        p_l4toa = ee.Geometry.Point([-72.2736, -44.6062])
        vals_l4toa = tools.get_value(masked_l4toa, p_l4toa, 30, 'client')
        self.assertEqual(vals_l4toa["B1"], None)

        # LANDSAT 5 USGS
        p_l5usgs = ee.Geometry.Point([-65.4991, -24.534])
        masked_l5usgs = cloud_mask.fmask("cfmask")(self.l5SR)
        vals_l5usgs = tools.get_value(masked_l5usgs, p_l5usgs, 30, 'client')
        self.assertEqual(vals_l5usgs["B1"], None)

        # LANDSAT 5 LEDAPS
        p_l5led = ee.Geometry.Point([-70.3455, -43.8306])
        masked_l5led = cloud_mask.ledaps(self.l5led)
        vals_l5led = tools.get_value(masked_l5led, p_l5led, 30, 'client')
        self.assertEqual(vals_l5led["B1"], None)

        # LANDSAT 5 TOA
        masked_l5toa = cloud_mask.fmask("fmask")(self.l5toa)
        p_l5toa = ee.Geometry.Point([-70.9003, -39.7421])
        vals_l5toa = tools.get_value(masked_l5toa, p_l5toa, 30, 'client')
        self.assertEqual(vals_l5toa["B1"], None)

        # LANDSAT 7 USGS
        p_l7usgs = ee.Geometry.Point([-64.8533, -26.1052])
        masked_l7usgs = cloud_mask.fmask("cfmask")(self.l7SR)
        vals_l7usgs = tools.get_value(masked_l7usgs, p_l7usgs, 30, 'client')
        self.assertEqual(vals_l7usgs["B1"], None)

        # LANDSAT 7 LEDAPS
        p_l7led = ee.Geometry.Point([-64.9141, -25.2264])
        masked_l7led = cloud_mask.ledaps(self.l7led)
        vals_l7led = tools.get_value(masked_l7led, p_l7led, 30, 'client')
        self.assertEqual(vals_l7led["B1"], None)

        # LANDSAT 7 TOA
        masked_l7toa = cloud_mask.fmask("fmask")(self.l7toa)
        p_l7toa = ee.Geometry.Point([-64.8495, -25.2354])
        vals_l7toa = tools.get_value(masked_l7toa, p_l7toa, 30, 'client')
        self.assertEqual(vals_l7toa["B1"], None)

        # LANDSAT 8 USGS
        p_l8usgs = ee.Geometry.Point([-65.5568, -24.3327])
        masked_l8usgs = cloud_mask.fmask("cfmask")(self.l8SR)
        vals_l8usgs = tools.get_value(masked_l8usgs, p_l8usgs, 30, 'client')
        self.assertEqual(vals_l8usgs["B1"], None)

        # LANDSAT 8 TOA
        masked_l8toa = cloud_mask.fmask("fmask")(self.l8toa)
        p_l8toa = ee.Geometry.Point([-71.7833, -43.6634])
        vals_l8toa = tools.get_value(masked_l8toa, p_l8toa, 30, 'client')
        self.assertEqual(vals_l8toa["B1"], None)

        # LANDSAT SENTINEL 2
        masked_s2 = cloud_mask.sentinel2(self.sentinel2)
        p_s2 = ee.Geometry.Point([-72.2104, -42.7592])
        vals_s2 = tools.get_value(masked_s2, p_s2, 10, 'client')
        self.assertEqual(vals_s2["B1"], None)

        # LANDSAT MODIS AQ
        masked_ma = cloud_mask.modis(self.modis_aqua)
        p_ma = ee.Geometry.Point([-69.071, -43.755])
        vals_ma = tools.get_value(masked_ma, p_ma, 500, 'client')
        self.assertEqual(vals_ma["sur_refl_b01"], None)

        # LANDSAT MODIS TE
        masked_te = cloud_mask.modis(self.modis_terra)
        p_te = ee.Geometry.Point([-71.993, -43.692])
        vals_te = tools.get_value(masked_te, p_te, 500, 'client')
        self.assertEqual(vals_te["sur_refl_b01"], None)