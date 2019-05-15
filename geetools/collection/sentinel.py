# coding=utf-8
""" Google Earth Engine Sentinel Collections """
from . import Collection, TODAY, Band
from .. import tools, cloud_mask
import ee

NUNBERS = [1, 2]
PROCESSES = ['TOA', 'SR']
IDS = [
    'COPERNICUS/S2',
    'COPERNICUS/S2_SR'
]


class Sentinel2(Collection):
    """ Sentinel 2 Collection """
    def __init__(self, process='TOA'):
        super(Sentinel2, self).__init__()
        if process not in PROCESSES:
            msg = '{} is not a valid process'
            raise ValueError(msg.format(process))

        if process == 'TOA':
            self.id = 'COPERNICUS/S2'
        else:
            self.id = 'COPERNICUS/S2_SR'

        self.number = 2
        self.spacecraft = 'SENTINEL2'
        self.process = process

        self.start_date = '2015-06-23'
        self.end_date = TODAY

        self.cloud_cover = 'CLOUD_COVERAGE_ASSESSMENT'
        self.algorithms = {
            'hollstein': cloud_mask.applyHollstein
        }

        if self.process == 'SR':
            self.algorithms['scl_masks'] = self.SclMasks

        self.bands = self._make_bands()

    def _make_bands(self):
        band = [None]*30
        common = {'min':0, 'max': 10000, 'precision': 'uint16',
                  'reference': 'optical'}
        band[0] = Band('B1', 'aerosol', scale=60, **common)
        band[1] = Band('B2', 'blue', scale=10, **common)
        band[2] = Band('B3', 'green', scale=10, **common)
        band[3] = Band('B4', 'red', scale=10, **common)
        band[4] = Band('B5', 'red_edge_1', scale=20, **common)
        band[5] = Band('B6', 'red_edge_2', scale=20, **common)
        band[6] = Band('B7', 'red_edge_3', scale=20, **common)
        band[7] = Band('B8', 'nir', scale=10, **common)
        band[8] = Band('B8A', 'red_edge_4', scale=20, **common)
        band[9] = Band('B9', 'water_vapor', scale=60, **common)
        swir = Band('B11', 'swir', scale=20, **common)
        swir2 = Band('B12', 'swir2', scale=20, **common)
        qa10 = Band('QA10', 'qa10', scale=10, reference='bits',
                    precision='uint16')
        qa20 = Band('QA20', 'qa20', scale=20, reference='bits',
                    precision='uint32')
        qa60 = Band('QA60', 'qa60', scale=60, reference='bits',
                    bits={'10':{1:'cloud'}, '11':{1:'cirrus'}},
                    precision='uint16')

        if self.process in ['TOA']:
            band[10] = Band('B10', 'cirrus', scale=60, **common)
            band[11] = swir
            band[12] = swir2
            band[13] = qa10
            band[14] = qa20
            band[15] = qa60

        if self.process in ['SR']:
            band[10] = swir
            band[11] = swir2
            band[12] = Band('AOT', 'aerosol_thickness', 'uint16', 10,
                            0, 65535, 'optical')
            band[13] = Band('WVP', 'water_vapor_pressure', 'uint16', 10,
                            0, 65535, 'optical')
            band[14] = Band('SCL', 'scene_classification_map', 'uint8', 20,
                            1, 11, 'classification')
            band[15] = qa10
            band[16] = qa20
            band[17] = qa60

        return [b for b in band if b]

    def SclMasks(self, image):
        """ Decodify the SCL bands and create a mask for each category """
        if self.process == 'SR':
            scl = image.select('SCL')

            data = ee.Dictionary(self.SclData)

            def wrap(band_value, name):
                band_value = ee.Number.parse(band_value)
                name = ee.String(name)
                mask = scl.eq(band_value).rename(name)
                return mask

            newbands = ee.Dictionary(data.map(wrap))
            bandslist = tools.dictionary.extractList(newbands,
                                            [str(i) for i in range(1, 12)])

            image = tools.image.addMultiBands(ee.Image(bandslist.get(0)),
                                              ee.List(bandslist.slice(1)))


        return image

    @property
    def SclData(self):
        data = None
        if self.process == 'SR':
            data = {
                1: 'saturated',
                2: 'dark',
                3: 'shadow',
                4: 'vegetation',
                5: 'bare_soil',
                6: 'water',
                7: 'cloud_low',
                8: 'cloud_medium',
                9: 'cloud_high',
                10: 'cirrus',
                11: 'snow'
            }
        return data

    @staticmethod
    def fromId(id):
        """ Create a Sentinel2 class from a GEE ID """
        if id == 'COPERNICUS/S2':
            return Sentinel2()
        elif id == 'COPERNICUS/S2_SR':
            return Sentinel2('SR')
        else:
            msg = '{} not recognized as a Sentinel 2 ID'
            raise ValueError(msg.format(id))

    # FACTORY
    @classmethod
    def Sentinel2TOA(cls):
        return cls('TOA')

    @classmethod
    def Sentienl2SR(cls):
        return cls('SR')