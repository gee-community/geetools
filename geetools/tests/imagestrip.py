# coding=utf-8
import unittest
import ee
from ..ui import imagestrip
from PIL.Image import Image
ee.Initialize()

class TestStrip(unittest.TestCase):

    def setUp(self):
        self.pol_L8SR = ee.Geometry.Polygon([[[-66, -25],
                                              [-66, -24.5],
                                              [-65.5, -24.5],
                                              [-65.5, -25]]])

        self.l8SR_col = ee.ImageCollection("LANDSAT/LC8_SR")

    def test_strip(self):
        strip = imagestrip.ImageStrip("test", description="just a test")

        col = self.l8SR_col.filterBounds(self.pol_L8SR).filterDate(
            "2013-01-01", "2013-06-01")

        list_imgs = col.toList(10)

        viz_params = {'bands':["B4", "B5", "B3"], 'min':0, 'max':5000}
        region = self.pol_L8SR.bounds().getInfo()["coordinates"]

        i = strip.from_collection([col], viz_param=viz_params, region=region,
                                  name="test", folder="files", drawRegion=True,
                                  zoom=2, properties=["CLOUD_COVER",
                                                      "solar_zenith_angle"],
                                  description="test")

        self.assertIsInstance(i, Image)
