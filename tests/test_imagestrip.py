# coding=utf-8

import ee
from geetools.ui import imagestrip
from PIL.Image import Image
ee.Initialize()


pol_L8SR = ee.Geometry.Polygon([[[-66, -25],
                                 [-66, -24.5],
                                 [-65.5, -24.5],
                                 [-65.5, -25]]])

l8SR_col = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")

def test_strip():
    strip = imagestrip.ImageStrip("test", description="just a test")

    col = l8SR_col.filterBounds(pol_L8SR).filterDate(
        "2013-01-01", "2013-06-01")

    viz_params = {'bands':["B4", "B5", "B3"], 'min':0, 'max':5000}
    region = pol_L8SR.bounds().getInfo()["coordinates"]

    i = strip.fromCollection([col], viz_param=viz_params, region=region,
                             name="test", folder="files", drawRegion=True,
                             zoom=2, properties=["CLOUD_COVER",
                                                  "solar_zenith_angle"],
                             description="test")

    assert isinstance(i, (Image,)) == True
