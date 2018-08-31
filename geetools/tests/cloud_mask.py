# coding=utf-8
# coding=utf-8
import unittest
import ee
from .. import tools, cloud_mask
from ..tools.image import get_value
from ..tools.geometry import getRegion
ee.Initialize()

area = ee.Geometry.Point([-65.80, -25.01])

l1 = ee.Image("LANDSAT/LM1_L1T/LM12500851973064AAA05")
l2 = ee.Image("LANDSAT/LM2_L1T/LM22480891976038FAK05")
l3 = ee.Image("LANDSAT/LM3_L1T/LM32490891979068XXX01")
l5led = ee.Image("LEDAPS/LT5_L1T_SR/LT52310901984169XXX03")
l7led = ee.Image("LEDAPS/LE7_L1T_SR/LE72300781999227CUB00")
sentinel2 = ee.Image("COPERNICUS/S2/20160122T144426_20160127T174646_T18GYT")
modis_terra = ee.Image("MODIS/MOD09GA/MOD09GA_005_2000_02_24")
modis_aqua = ee.Image("MODIS/MYD09GA/MYD09GA_005_2002_07_04")

p_l8SR_cloud = ee.Geometry.Point([-65.8109, -25.0185])
p_l8SR_no_cloud = ee.Geometry.Point([-66.0306, -24.9338])

bands457 = ['B4', 'B7', 'B3']
bands8 = ['B5', 'B7', 'B4']
bandsS2 = ['B8', 'B12', 'B4']


def getimage(collection, date, area):
    image = ee.Image(collection.filterDate(ee.Date(date).advance(-1, 'day'),
                                           ee.Date(date).advance(1, 'day'))
                     .filterBounds(area)
                     .first())
    return image


def show(iid, image, masked, bands, min, max):
    thumb_original = image.select(bands).getThumbURL(
        {'min':min, 'max':max, 'region': getRegion(image)})
    thumb_masked = masked.select(bands).getThumbURL(
        {'min':min, 'max':max, 'region': getRegion(image)})

    print('{}\noriginal: {}\nmasked {}\n'.format(iid, thumb_original,
                                                 thumb_masked))


class TestL4TOA(unittest.TestCase):
    def setUp(self):
        self.iid = 'LANDSAT/LT04/C01/T1_TOA'
        collection = ee.ImageCollection(self.iid)
        date = '1989-07-25'
        self.p_cloud = ee.Geometry.Point([-65.506, -24.9263])
        p_clear = ee.Geometry.Point([-64.6133, -24.4522])

        self.image = getimage(collection, date, area)

    def test_all(self):
        masked = cloud_mask.landsat457TOA_BQA()(self.image)
        vals = get_value(masked, self.p_cloud, 30, 'client')

        show(self.iid, self.image, masked, bands457, 0, 0.5)

        self.assertEqual(vals["B1"], None)

    def test_clouds(self):
        masked = cloud_mask.landsat457TOA_BQA(['cloud'])(self.image)
        vals = get_value(masked, self.p_cloud, 30, 'client')

        show(self.iid, self.image, masked, bands457, 0, 0.5)

        self.assertEqual(vals["B1"], None)

    def test_shadows(self):
        masked = cloud_mask.landsat457TOA_BQA(['shadow'])(self.image)
        vals = get_value(masked, self.p_cloud, 30, 'client')

        show(self.iid, self.image, masked, bands457, 0, 0.5)

        # self.assertEqual(vals["B1"], None)

    def test_snow(self):
        masked = cloud_mask.landsat457TOA_BQA(['snow'])(self.image)
        vals = get_value(masked, self.p_cloud, 30, 'client')

        show(self.iid, self.image, masked, bands457, 0, 0.5)

        # self.assertEqual(vals["B1"], None)


class TestL5TOA(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LT05/C01/T1_TOA'
        collection = ee.ImageCollection(iid)
        date = '2010-03-21'
        p_cloud = ee.Geometry.Point([-65.2835, -24.3422])
        p_clear = ee.Geometry.Point([-64.6106, -24.7469])

        image = getimage(collection, date, area)

        masked = cloud_mask.landsat457TOA_BQA()(image)
        vals = get_value(masked, p_cloud, 30, 'client')

        show(iid, image, masked, bands457, 0, 0.5)

        self.assertEqual(vals["B1"], None)


class TestL7TOA(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LE07/C01/T1_TOA'
        collection = ee.ImageCollection(iid)
        date = '2010-03-13'
        p_cloud = ee.Geometry.Point([-65.5784, -24.773])
        p_clear = ee.Geometry.Point([-65.599, -24.9313])

        image = getimage(collection, date, area)

        masked = cloud_mask.landsat457TOA_BQA()(image)
        vals = get_value(masked, p_cloud, 30, 'client')

        show(iid, image, masked, bands457, 0, 0.5)

        self.assertEqual(vals["B1"], None)


class TestL8TOA(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LC08/C01/T1_TOA'
        collection = ee.ImageCollection(iid)
        date = '2017-03-08'
        p_cloud = ee.Geometry.Point([-65.7539, -25.0327])
        p_clear = ee.Geometry.Point([-66.034, -24.9512])

        image = getimage(collection, date, area)

        masked = cloud_mask.landsat8TOA_BQA()(image)
        vals = get_value(masked, p_cloud, 30, 'client')

        show(iid, image, masked, bands457, 0, 0.5)

        self.assertEqual(vals["B1"], None)


class TestL4SR(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LT04/C01/T1_SR'
        collection = ee.ImageCollection(iid)
        date = '1989-07-25'
        p_cloud = ee.Geometry.Point([-65.506, -24.9263])
        p_clear = ee.Geometry.Point([-64.6133, -24.4522])

        image = getimage(collection, date, area)

        # masked = cloud_mask.cfmask_bits(image)
        masked = cloud_mask.landsatSR()(image)
        vals = get_value(masked, p_cloud, 30, 'client')

        show(iid, image, masked, bands457, 0, 5000)

        self.assertEqual(vals["B1"], None)


class TestL5SR(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LT05/C01/T1_SR'
        collection = ee.ImageCollection(iid)
        date = '2010-03-21'
        p_cloud = ee.Geometry.Point([-65.2835, -24.3422])
        p_clear = ee.Geometry.Point([-64.6106, -24.7469])

        image = getimage(collection, date, area)

        # masked = cloud_mask.cfmask_bits(image)
        masked = cloud_mask.landsatSR()(image)
        vals = get_value(masked, p_cloud, 30, 'client')
        show(iid, image, masked, bands457, 0, 5000)

        self.assertEqual(vals["B1"], None)


class TestL7SR(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LE07/C01/T1_SR'
        collection = ee.ImageCollection(iid)
        date = '2010-03-13'
        p_cloud = ee.Geometry.Point([-65.5784, -24.773])
        p_clear = ee.Geometry.Point([-65.599, -24.9313])

        image = getimage(collection, date, area)

        # masked = cloud_mask.cfmask_bits(image)
        masked = cloud_mask.landsatSR()(image)
        vals = get_value(masked, p_cloud, 30, 'client')
        show(iid, image, masked, bands457, 0, 5000)

        self.assertEqual(vals["B1"], None)


class TestL8SR(unittest.TestCase):
    def test(self):
        iid = 'LANDSAT/LC08/C01/T1_SR'
        collection = ee.ImageCollection(iid)
        date = '2017-03-08'
        p_cloud = ee.Geometry.Point([-65.7539, -25.0327])
        p_clear = ee.Geometry.Point([-66.034, -24.9512])

        image = getimage(collection, date, area)

        # masked = cloud_mask.cfmask_bits(image)
        masked = cloud_mask.landsatSR()(image)
        vals = get_value(masked, p_cloud, 30, 'client')
        show(iid, image, masked, bands8, 0, 5000)

        self.assertEqual(vals["B1"], None)


class TestSentinel2(unittest.TestCase):
    def test(self):
        iid = 'COPERNICUS/S2'
        collection = ee.ImageCollection(iid)
        date = '2017-03-07'
        p_cloud = ee.Geometry.Point([-65.84304, -24.82382])
        p_clear = ee.Geometry.Point([-65.88415, -24.82608])

        image = getimage(collection, date, area)

        masked = cloud_mask.sentinel2()(image)
        vals = get_value(masked, p_cloud, 30, 'client')

        show(iid, image, masked, bandsS2, 0, 5000)

        self.assertEqual(vals["B1"], None)


class TestHollstein(unittest.TestCase):
    def test(self):
        iid = 'COPERNICUS/S2'
        collection = ee.ImageCollection(iid)
        date = '2017-03-07'
        p_cloud = ee.Geometry.Point([-65.84304, -24.82382])
        p_clear = ee.Geometry.Point([-65.88415, -24.82608])

        image = getimage(collection, date, area)

        masked = cloud_mask.hollstein_S2(['cloud','snow','shadow', 'cirrus'])(image)
        vals = get_value(masked, p_cloud, 30, 'client')

        show(iid, image, masked, bandsS2, 0, 5000)

        self.assertEqual(vals["B1"], None)
