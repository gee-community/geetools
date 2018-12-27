# coding=utf-8
""" Google Earth Engine Landsat Collections """
from . import Collection
from .. import bitreader, cloud_mask, tools
from .. import algorithms as module_alg
import ee

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

        # Properties
        self._id = None
        self._bands = None
        self._scales = None
        self._ranges = None
        self._algorithms = None
        self._bits = None
        self._thermal_bands = None
        self._optical_bands = None
        self._quality_bands = None

    @staticmethod
    def fromId(id):
        """ Create a Landsat class from a GEE ID """
        parts = id.split('/')
        sensors = {'LT': 'TM', 'LM': 'MSS', 'LE': 'ETM', 'LC': 'OLI'}
        shortid = parts[1]
        sensor = sensors[shortid[0:2]]
        number = int(shortid[2:4])
        process_tier = parts[3]
        process_tier_split = process_tier.split('_')

        if len(process_tier_split) == 1:
            process = 'RAW'
            tier = process_tier_split[1]
        else:
            process = process_tier_split[1]
            tier = process_tier_split[0]

        return Landsat(number, process, sensor, int(tier[1]))

    @property
    def id(self):
        """ Google Earth Engine ID """
        if not self._id:
            self._id = 'LANDSAT/{}/C01/{}{}'.format(
                NUMBER_ID[self.number][self.sensor],
                TIER_ID[self.tier],
                PROCESS_ID[self.process])

        return self._id

    @property
    def bands(self):
        """ Band's name relation. Return a dict """
        if not self._bands:
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

            self._bands = band
        return self._bands

    @property
    def scales(self):
        """ Band's scales. Return a dict """
        if not self._scales:
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

            self._scales = scale
        return self._scales

    @property
    def ranges(self):
        """ Band's value ranges (min and max). Return a dict """
        if not self._ranges:
            if self.number == 8:
                max_raw = 65535
            else:
                max_raw = 255

            max_toa_optical = 1
            max_toa_thermal = 1000
            max_sr_optical = 10000
            max_sr_thermal = 10000

            RAW = {}
            TOA = {}
            SR = {}

            if self.process == 'TOA':
                for name, band in self.bands.items():
                    if name in self.optical_bands.keys():
                        TOA[name] = {'min': 0, 'max': max_toa_optical}
                    if name in self.thermal_bands.keys():
                        TOA[name] = {'min': 0, 'max': max_toa_thermal}

            if self.process == 'SR':
                for name, band in self.bands.items():
                    if name in self.optical_bands.keys():
                        SR[name] = {'min': 0, 'max': max_sr_optical}
                    if name in self.thermal_bands.keys():
                        SR[name] = {'min': 0, 'max': max_sr_thermal}

            if self.process == 'RAW':
                for name, band in self.bands.items():
                    if name in self.optical_bands.keys():
                        RAW[name] = {'min': 0, 'max': max_raw}
                    if name in self.thermal_bands.keys():
                        RAW[name] = {'min': 0, 'max': max_raw}

            ranges = {
                'RAW': RAW,
                'TOA': TOA,
                'SR': SR,
            }
            self._ranges = ranges[self.process]
        return self._ranges

    @property
    def bits(self):
        if not self._bits:
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

            self._bits = bit
        return self._bits

    @property
    def thermal_bands(self):
        """ List of thermal bands """
        if not self._thermal_bands:
            names = ['thermal', 'thermal1', 'thermal2']
            bands = {}
            for name, band in self.bands.items():
                if name in names:
                    bands[name] = band

            self._thermal_bands = bands
        return self._thermal_bands

    @property
    def optical_bands(self):
        """ List of thermal bands """
        if not self._optical_bands:
            names = ['blue', 'green', 'red', 'nir', 'nir1', 'nir2', 'swir',
                     'swir1', 'swir2', 'mir', 'ublue', 'pan', 'cirrus']
            bands = {}
            for name, band in self.bands.items():
                if name in names:
                    bands[name] = band

            self._optical_bands = bands
        return self._optical_bands

    @property
    def quality_bands(self):
        """ List of thermal bands """
        if not self._quality_bands:
            names = ['bqa', 'cloud_qa', 'pixel_qa', 'sr_aerosol']
            bands = {}
            for name, band in self.bands.items():
                if name in names:
                    bands[name] = band

            self._quality_bands = bands
        return self._quality_bands

    def harmonize(self):
        """ HARMONIZATION """
        if self.number == 8:
            if self.process == 'SR':
                def harmonize(image):
                    return module_alg.Landsat.harmonization(image, True)
            else:
                def harmonize(image):
                    return module_alg.Landsat.harmonization(image, False)
        else:
            harmonize = None

        return harmonize

    def brdf(self):
        """ BRDF Correction """
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
            return brdf
        else:
            return None

    @property
    def algorithms(self):
        if not self._algorithms:
            algorithm = {}
            algorithm['harmonization'] = self.harmonize
            algorithm['brdf'] = self.brdf

            self._algorithms = algorithm
        return self._algorithms

    @property
    def start_date(self):
        return START[self.number]

    @property
    def end_date(self):
        return END[self.number]

    def rescale(self, number=None, process=None, drop=False):
        """ Re-scale bands to match number and process

         :param number: the Landsat satellite to match with
         :type number: int
         :param process: the Landsat process to match with
         :type process: str
         :param drop: drop the bands that do not match between collections
         :type drop: bool
         :return: a function to map over an ImageCollection
         :rtype: function
         """
        # First escape
        if self.number == number and self.process == process:
            return lambda img: img

        # Helper
        # As 'parametrize' will be used several times
        param = tools.image.parametrize

        # Check if all bands have the same max and min
        def check(collection, bands):
            # Second scape
            if not check_bands(collection, bands):
                return lambda img: img

        check(self, self.optical_bands)
        check(self, self.thermal_bands)

        # Create comparative collection
        proxy = Landsat(number, process)

        check(proxy, proxy.optical_bands)
        check(proxy, proxy.thermal_bands)

        if self.thermal_bands and proxy.thermal_bands:
            def scale_thermal(image):
                bandmax = self.ranges[list(self.thermal_bands.keys())[0]]
                bandmax = ee.Number(ee.Dictionary(bandmax).get('max'))
                proxymax = proxy.ranges[list(proxy.thermal_bands.keys())[0]]
                proxymax = ee.Number(ee.Dictionary(proxymax).get('max'))
                bands = list(self.thermal_bands.values())
                toscale = image.select(bands)

                return param(toscale, (0, bandmax), (0, proxymax))
        else:
            def scale_thermal(img): return img

        if self.optical_bands and proxy.optical_bands:
            def scale_optical(image):
                bandmax = self.ranges[list(self.optical_bands.keys())[0]]
                bandmax = ee.Number(ee.Dictionary(bandmax).get('max'))
                proxymax = proxy.ranges[list(proxy.optical_bands.keys())[0]]
                proxymax = ee.Number(ee.Dictionary(proxymax).get('max'))
                bands = list(self.optical_bands.values())
                toscale = image.select(bands)

                return param(toscale, (0, bandmax), (0, proxymax))
        else:
            def scale_optical(img): return img

        intersection_optical = [band for band in self.optical_bands.values() if band in proxy.optical_bands.values()]
        intersection_thermal = [band for band in self.thermal_bands.values() if band in proxy.thermal_bands.values()]

        def final_scale(image):
            scaled_optical = scale_optical(image)
            scaled_thermal = scale_thermal(image)

            if drop:
                scaled_optical = scaled_optical.select(intersection_optical)
                scaled_thermal = scaled_thermal.select(intersection_thermal)

            # join optical and thermal bands
            scaled = scaled_optical.addBands(scaled_thermal)
            # add quality bands
            scaled = scaled.addBands(image.select(list(self.quality_bands.values())))
            scaled_bands = scaled.bandNames()
            original_bands = image.bandNames()
            rest_bands = tools.ee_list.difference(original_bands, scaled_bands)
            rest_image = image.select(rest_bands)

            return rest_image.addBands(scaled)

        return final_scale


# HELPERS
def allequal(iterable):
    """ Check if all elements inside an iterable are equal """
    first = iterable[0]
    rest = iterable[1:]
    for item in rest:
        if item == first: continue
        else: return False
        first = item
    return True


# Check if all bands have the same max and min
def check_bands(collection, bands):
    bandsmax = []
    bandsmin = []
    for name, band in bands.items():
        bandmax = collection.ranges[name]['max']
        bandmin = collection.ranges[name]['min']
        bandsmax.append(bandmax)
        bandsmin.append(bandmin)

    if not allequal(bandsmax) or not allequal(bandsmin):
        return False
    return True