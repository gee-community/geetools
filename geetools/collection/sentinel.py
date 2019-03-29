# coding=utf-8
""" Google Earth Engine Sentinel Collections """
from . import Collection
from .. import bitreader, cloud_mask, tools
from .. import algorithms as module_alg
import ee

NUNBERS = [1, 2]
PROCESSES = ['TOA', 'SR']


class Sentinel2(Collection):
    """ Sentinel 2 Collection """
    def __init__(self, process='TOA'):
        super(Sentinel2, self).__init__()
        if process not in PROCESSES:
            msg = '{} is not a valid process'
            raise ValueError(msg.format(process))

        # ID
        if process == 'TOA':
            self.id = 'COPERNICUS/S2'
        else:
            self.id = 'COPERNICUS/S2_SR'

        self.number = 2
        self.spacecraft = 'SENTINEL'
        self.process = process

        self.start_date = '2015-06-23'
        self.end_date = None

        self.thermal_bands = {}  # No thermal bands =(
        self.quality_bands = {
            'qa10': 'QA10',
            'qa20': 'QA20',
            'qa60': 'QA60',
        }
        self.optical_bands = {
            'aerosol': 'B1',
            'blue': 'B2',
            'green': 'B3',
            'red': 'B4',
            'red_edge_1': 'B5',
            'red_edge_2': 'B6',
            'red_edge_3': 'B7',
            'nir': 'B8',
            'red_edge_4': 'B8A',
            'water_vapor': 'B9',
            'cirrus': 'B10',
            'swir': 'B11',
            'swir2': 'B12',
        }

        self.scales = {
            'aerosol': 60, 'blue': 10, 'green': 10, 'red': 10,
            'red_edge_1': 20, 'red_edge_2': 20, 'red_edge_3': 20,
            'nir': 10, 'red_edge_4': 20, 'water_vapor': 60, 'cirrus': 60,
            'swir': 20, 'swir2': 20, 'qa10': 10, 'qa20': 20, 'qa60': 60,
        }

        self.ranges = {
            'aerosol': {'max': 10000, 'min': 0},
            'blue': {'max': 10000, 'min': 0},
            'green': {'max': 10000, 'min': 0},
            'red': {'max': 10000, 'min': 0},
            'red_edge_1': {'max': 10000, 'min': 0},
            'red_edge_2': {'max': 10000, 'min': 0},
            'red_edge_3': {'max': 10000, 'min': 0},
            'nir': {'max': 10000, 'min': 0},
            'red_edge_4': {'max': 10000, 'min': 0},
            'water_vapor': {'max': 10000, 'min': 0},
            'cirrus': {'max': 10000, 'min': 0},
            'swir': {'max': 10000, 'min': 0},
            'swir2': {'max': 10000, 'min': 0},
        }

        self.cloud_cover = 'CLOUD_COVERAGE_ASSESSMENT'
        self.algorithms = {}
        self.bits = {
            'qa60': {
                '10':{1:'cloud'},
                '11':{1:'cirrus'}
            }
        }

        if self.process == 'SR':
            self.quality_bands.update({
                'water_vapor_pressure': 'WVP',
                'aerosol_thickness': 'AOT',
                'scene_classification_map': 'SCL'
            })

            self.scales.update({
                'water_vapor_pressure': 10,
                'aerosol_thickness': 10,
                'scene_classification_map': 20
            })

            self.ranges.update({
                'water_vapor_pressure': {'max': 65535, 'min': 0},
                'aerosol_thickness': {'max': 65535, 'min': 0},
                'scene_classification_map': {'max': 11, 'min': 1}
            })
            self.visualization['SCL'] = {
                'bands':['SCL'],
                'min': 1, 'max': 11,
                'palette': ['ff0004', '868686', '774b0a', '10d22c',
                            'ffff52', '0000ff', '818181', 'c0c0c0',
                            'f1f1f1', 'bac5eb', '52fff9']
            }

    @property
    def bands(self):
        bands = {}
        # fill bands
        bands.update(self.thermal_bands)
        bands.update(self.optical_bands)
        bands.update(self.quality_bands)
        return bands

    def SCL_mask(self, image):
        """ Decodify the SCL bands and create a mask for each category """
        if self.process == 'SR':
            scl = image.select('SCL')

            data = ee.Dictionary(self.SCL_data)

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
    def SCL_data(self):
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


Sentinel2TOA = Sentinel2()
Sentinel2SR = Sentinel2('SR')