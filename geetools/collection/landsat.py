# coding=utf-8
""" Google Earth Engine Landsat Collections """
from . import Collection
from .. import bitreader, cloud_mask
from .. import algorithms as module_alg

NUMBERS = [1, 2, 3, 4, 5, 7, 8]
PROCESSES = ['RAW', 'TOA', 'SR']
SENSORS = ['TM', 'MSS', 'ETM', 'OLI']
TIERS = [1, 2]
NUMBER_ID = {
    1: {'MSS': 'LM01'},
    2: {'MSS': 'LM02'},
    3: {'MSS': 'LM03'},
    4: {'TM':'LT04', 'MSS':'LM04'},
    5: {'TM':'LT05', 'MSS':'LM05'},
    7: {'ETM':'LE07'},
    8: {'OLI':'LC08'}
}
TIER_ID = {1: 'T1', 2: 'T2'}
PROCESS_ID = {'RAW': '', 'SR': '_SR', 'TOA': '_TOA'}
START = {1: '1972-07-23', 2: '1975-01-22', 3: '1978-03-05',
         4: '1982-07-16', 5: '1984-01-01', 7: '1999-01-01',
         8: '2013-04-11'}
END = {1: '1978-01-07', 2: '1982-02-26', 3: '1983-03-31',
       4: '1993-12-14', 5: '2012-05-05', 7: None, 8: None}
DEFAULTS = {
    1: {'process': 'RAW', 'sensor':'MSS'},
    2: {'process': 'RAW', 'sensor':'MSS'},
    3: {'process': 'RAW', 'sensor':'MSS'},
    4: {'process': 'SR', 'sensor':'TM'},
    5: {'process': 'SR', 'sensor':'TM'},
    7: {'process': 'SR', 'sensor':'TM'},
    8: {'process': 'SR', 'sensor':'OLI'},
}
BITS = {
    'pixel_qa': {
        '1': {1:'clear'},
        '2': {1:'water'},
        '3': {1:'shadow'},
        '4': {1:'snow'},
        '5': {1:'cloud'},
        '6-7':{3:'high_confidence_cloud'}
    },
    'cloud_qa': {
        '0': {1:'ddv'},
        '1': {1:'cloud'},
        '2': {1:'shadow'},
        '3': {1:'adjacent'},
        '4': {1:'snow'},
        '5': {1:'water'}
    },

}


class Landsat(Collection):
    """  Landsat Collection """

    def __init__(self, number, process=None, sensor=None, tier=1):
        """ Landsat Collection

        :param number: One of 1, 2, 3, 4, 5, 7, 8
        :param process: One of 'RAW', 'TOA', 'SR'
        :param sensor: One of 'TM', 'MSS', 'ETM', 'OLI'
        :param tier: One of 1, 2
        """
        self.number = number
        self.process = process if process else DEFAULTS[number]['process']
        self.sensor = sensor if sensor else DEFAULTS[number]['sensor']
        self.tier = tier

        self.cloud_cover = 'CLOUD_COVER'

    @staticmethod
    def fromId(id):
        """ Create a Landsat class from a GEE ID """
        parts = id.split('/')
        sensors = {'LT': 'TM', 'LM': 'MSS', 'LE': 'ETM', 'LC': 'OLI'}
        shortid = parts[1]
        number = int(shortid[2:4])
        sensor = sensors[shortid[0:2]]
        process_tier = parts[3]
        process_tier_split = process_tier.split('_')
        if len(process_tier_split) == 1:
            process = 'RAW'
            tier = process_tier_split[0]
        else:
            process = process_tier_split[0]
            tier = process_tier_split[1]

        return Landsat(number, process, sensor, int(tier[1]))

    @property
    def id(self):
        return 'LANDSAT/{}/C01/{}{}'.format(
            NUMBER_ID[self.number][self.sensor],
            TIER_ID[self.tier],
            PROCESS_ID[self.process]
        )

    @property
    def bands(self):
        """ Band's name relation. Return a dict """
        band = {}

        # COMMON
        if self.number in [1, 2, 3]:
            band = {
                'green': 'B4', 'red': 'B5', 'nir': 'B6', 'nir2': 'B7'
            }

        if self.number in [4, 5, 7]:
            if self.sensor in ['TM', 'ETM']:
                band = {
                    'blue':'B1', 'green':'B2', 'red':'B3', 'nir':'B4',
                    'swir':'B5', 'swir2': 'B7'
                }
            else:
                band = {
                    'green': 'B1', 'red': 'B2', 'nir': 'B3', 'nir2': 'B4'
                }

        if self.number == 8:
            band = {
                'ublue': 'B1', 'blue': 'B2', 'green': 'B3', 'red': 'B4',
                'nir':'B5', 'swir':'B6', 'swir2':'B7', 'thermal':'B10',
                'thermal2':'B11'
            }

        # EXTRA
        if self.process == 'SR':
            band['pixel_qa'] = 'pixel_qa'
            band['radsat_qa'] = 'radsat_qa'

            if self.number in [4, 5, 7]:
                band['atmos_opacity'] = 'sr_atmos_opacity'
                band['cloud_qa'] = 'sr_cloud_qa'
                band['thermal'] = 'B6'

            if self.number == 8:
                band['aerosol'] = 'sr_aerosol'

        if self.process in ['TOA', 'RAW']:
            band['bqa'] = 'BQA'

            if self.number in [4, 5] and self.sensor == 'TM':
                band['thermal'] = 'B6'

            if self.number in [7, 8]:
                band['pan'] = 'B8'

            if self.number == 7:
                band['thermal1'] = 'B6_VCID_1'
                band['thermal2'] = 'B6_VCID_2'

            if self.number == 8:
                band['cirrus'] = 'B9'
                band['thermal'] = 'B10'
                band['thermal2'] = 'B11'

        return band

    @property
    def scales(self):
        """ Band's scales. Return a dict """
        scale = {}

        if self.number in [1, 2, 3]:
            scale = {
                'green': 60, 'red': 60, 'nir': 60, 'nir2': 30
            }

        if self.number in [4, 5]:
            if self.sensor == 'TM':
                scale = {
                    'blue':30, 'green':30, 'red':30, 'nir':30, 'swir':30,
                    'swir2':30, 'thermal':120
                }
            if self.sensor == 'MSS':
                scale = {
                    'green': 60, 'red': 60, 'nir': 60, 'nir2': 60
                }

        if self.number == 7:
            scale = {
                'blue': 30, 'green': 30, 'red': 30, 'nir':30, 'swir':30,
                'swir2':30, 'pan':15, 'thermal':100,
            }

        if self.number == 8:
            scale = {
                'ublue': 30, 'blue': 30, 'green': 30, 'red': 30, 'nir':30,
                'swir':30, 'swir2':30, 'pan':15, 'thermal':100, 'thermal2':100
            }

        return scale

    @property
    def range(self):
        """ Band's value ranges (min and max). Return a dict """
        ranges = {
            'RAW': {'min':0, 'max': 255},
            'TOA': {'min':0, 'max': 1},
            'SR': {'min':0, 'max': 10000},
        }
        return ranges[self.process]

    @property
    def bits(self):
        bit = {}
        if self.number == 8:
            if self.bands.get('pixel_qa'):
                bit['pixel_qa'] = {'1': {1:'clear'}, '2': {1:'water'},
                    '3': {1:'shadow'}, '4': {1:'snow'}, '5': {1:'cloud'},
                    '6-7':{3:'high_confidence_cloud'}, '8-9':{3:'cirrus'},
                    '10': {1:'occlusion'}}

            bit['bqa'] = {'4': {1:'cloud'}, '5-6': {3:'high_confidence_cloud'},
                '7-8': {3:'shadow'}, '9-10': {3:'snow'}, '11-12': {3:'cirrus'}}

        if self.number in [1, 2, 3, 4, 5, 7]:
            if self.bands.get('bqa'):
                bit['bqa'] = {'4': {1:'cloud'},
                    '5-6': {3:'high_confidence_cloud'},
                    '7-8': {3:'shadow'}, '9-10': {3:'snow'}}

            if self.bands.get('pixel_qa'):
                bit['pixel_qa'] = {'1': {1:'clear'}, '2': {1:'water'},
                    '3': {1:'shadow'}, '4': {1:'snow'}, '5': {1:'cloud'},
                    '6-7':{3:'high_confidence_cloud'}}

            if self.bands.get('cloud_qa'):
                bit['cloud_qa'] = {'0': {1:'ddv'}, '1': {1:'cloud'},
                    '2': {1:'shadow'}, '3': {1:'adjacent'}, '4': {1:'snow'},
                    '5': {1:'water'}}

        return bit

    @property
    def algorithms(self):
        algorithm = {}

        # HARMONIZATION
        if self.number == 8:
            if self.process == 'SR':
                def harmonize(image):
                    return module_alg.Landsat.harmonization(image, True)
            else:
                def harmonize(image):
                    return module_alg.Landsat.harmonization(image, False)

            algorithm['harmonization'] = harmonize

        # BRDF
        r = self.bands.get('red')
        g = self.bands.get('green')
        b = self.bands.get('blue')
        n = self.bands.get('nir')
        s1 = self.bands.get('swir1')
        s2 = self.bands.get('swir2')

        if r and g and b and n and s1 and s2:
            def brdf(image):
                return module_alg.Landsat.brdf_correct(image, r, g, b, n, s1,
                                                       s2)
            algorithm['brdf_correction'] = brdf

        return algorithm

    @property
    def start_date(self):
        return START[self.number]

    @property
    def end_date(self):
        return END[self.number]