# coding=utf-8
""" Google Earth Engine Landsat Collections """
from . import Collection, TODAY, Band
from .. import tools
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
       4: '1993-12-14', 5: '2012-05-05', 7: TODAY, 8: TODAY}
DEFAULTS = {
    1: {'process': 'RAW', 'sensor':'MSS'},
    2: {'process': 'RAW', 'sensor':'MSS'},
    3: {'process': 'RAW', 'sensor':'MSS'},
    4: {'process': 'SR', 'sensor':'TM'},
    5: {'process': 'SR', 'sensor':'TM'},
    7: {'process': 'SR', 'sensor':'ETM'},
    8: {'process': 'SR', 'sensor':'OLI'},
}
NUMBER_PROCESS = {
    1: ['RAW'], 2: ['RAW'], 3: ['RAW'],
    4: ['RAW', 'TOA', 'SR'], 5: ['RAW', 'TOA', 'SR'],
    7: ['RAW', 'TOA', 'SR'], 8: ['RAW', 'TOA', 'SR']
}
NUMBER_SENSOR = {k: list(v.keys()) for k, v in NUMBER_ID.items()}
IDS = [
    'LANDSAT/LM01/C01/T1',
    'LANDSAT/LM01/C01/T2',
    'LANDSAT/LM02/C01/T1',
    'LANDSAT/LM02/C01/T2',
    'LANDSAT/LM03/C01/T1',
    'LANDSAT/LM03/C01/T2',
    'LANDSAT/LM04/C01/T1',
    'LANDSAT/LM04/C01/T2',
    'LANDSAT/LM05/C01/T1',
    'LANDSAT/LM05/C01/T2',
    'LANDSAT/LT04/C01/T1', 'LANDSAT/LT04/C01/T1_TOA', 'LANDSAT/LT04/C01/T1_SR',
    'LANDSAT/LT04/C01/T2', 'LANDSAT/LT04/C01/T2_TOA', 'LANDSAT/LT04/C01/T2_SR',
    'LANDSAT/LT05/C01/T1', 'LANDSAT/LT05/C01/T1_TOA', 'LANDSAT/LT05/C01/T1_SR',
    'LANDSAT/LT05/C01/T1', 'LANDSAT/LT05/C01/T1_TOA', 'LANDSAT/LT05/C01/T1_SR',
    'LANDSAT/LE07/C01/T1', 'LANDSAT/LE07/C01/T1_TOA', 'LANDSAT/LE07/C01/T1_SR',
    'LANDSAT/LE07/C01/T2', 'LANDSAT/LE07/C01/T2_TOA', 'LANDSAT/LE07/C01/T2_SR',
    'LANDSAT/LC08/C01/T1', 'LANDSAT/LC08/C01/T1_TOA', 'LANDSAT/LC08/C01/T1_SR',
    'LANDSAT/LC08/C01/T2', 'LANDSAT/LC08/C01/T2_TOA', 'LANDSAT/LC08/C01/T2_SR',
]

class Landsat(Collection):
    """  Landsat Collection """

    def __init__(self, number, process=None, sensor=None, tier=1):
        """ Landsat Collection

        :param number: One of 1, 2, 3, 4, 5, 7, 8
        :param process: One of 'RAW', 'TOA', 'SR'
        :param sensor: One of 'TM', 'MSS', 'ETM', 'OLI'
        :param tier: One of 1, 2
        """
        super(Landsat, self).__init__()
        self.number = number
        self.process = process if process else DEFAULTS[number]['process']
        self.sensor = sensor if sensor else DEFAULTS[number]['sensor']
        self.tier = tier

        # CHECK AVAILABLE
        if self.process not in NUMBER_PROCESS[number]:
            msg = "Process {} not available for Landsat {}"
            raise ValueError(msg.format(self.process, number))

        if self.sensor not in NUMBER_SENSOR[number]:
            msg = "Sensor {} not available for Landsat {}"
            raise ValueError(msg.format(self.sensor, number))

        # Catch L4 MSS TOA or SR
        if self.sensor == 'MSS' and self.process in ['SR', 'TOA']:
            msg = 'Process {} not available for sensor {}'
            self.process = 'RAW'

        # Landsat common properties
        self.cloud_cover = 'CLOUD_COVER'
        self.spacecraft = 'LANDSAT'

        # set algorithms
        self.algorithms['brdf'] = self.brdf
        self.algorithms['harmonize'] = self.harmonize
        self.algorithms['rescale'] = self.rescaleAll

        # dates
        self.start_date = START[self.number]
        self.end_date = END[self.number]

        # ID
        self.id = self._make_id()

        # BANDS
        self.bands = self._make_bands()

    @staticmethod
    def fromId(id):
        """ Create a Landsat class from a GEE ID """
        if id not in IDS:
            msg = 'Collection {} not available'
            raise ValueError(msg.format(id))

        sensors = {'LT': 'TM', 'LM': 'MSS', 'LE': 'ETM', 'LC': 'OLI'}
        # decompose id
        parts = id.split('/')
        shortid = parts[1]
        sensor = sensors[shortid[0:2]]
        number = int(shortid[2:4])
        process_tier = parts[3]
        process_tier_split = process_tier.split('_')

        if len(process_tier_split) == 1:
            process = 'RAW'
            tier = process_tier_split[0]
        else:
            process = process_tier_split[1]
            tier = process_tier_split[0]

        return Landsat(number, process, sensor, int(tier[1]))

    def _make_id(self):
        """ Make ID from parsed data """
        return 'LANDSAT/{}/C01/{}{}'.format(
            NUMBER_ID[self.number][self.sensor],
            TIER_ID[self.tier],
            PROCESS_ID[self.process])

    def _make_bands(self):
        """ Band's name relation. Return a list of bands (Band instances) """
        band = [None]*20
        number = self.number
        process = self.process
        sensor = self.sensor

        max_raw_8 = 65535
        max_raw = 255
        max_toa_optical = 1
        max_toa_thermal = 1000
        max_sr = 10000

        # 457 SR
        atm_op = Band('sr_atmos_opacity', 'atmos_opacity', 'int16', 30,
                      -32768, 32767, reference='classification')
        cloud_qa_bits = {'0': {1:'ddv'},
                         '1': {1:'cloud'},
                         '2': {1:'shadow'},
                         '3': {1:'adjacent'},
                         '4': {1:'snow'},
                         '5': {1:'water'}}
        sr_cloud_qa = Band('sr_cloud_qa', 'cloud_qa', 'uint8', 30,
                           reference='bits', bits=cloud_qa_bits)

        pixel_qa = Band('pixel_qa', 'pixel_qa', 'uint16', 30,
                        reference='bits')

        radsat_qa_457 = Band('radsat_qa', 'radsat_qa', 'uint8', 30,
                             reference='bits',
                             bits={
                                 1: {1:'B1_saturated'},
                                 2: {1:'B2_saturated'},
                                 3: {1:'B3_saturated'},
                                 4: {1:'B4_saturated'},
                                 5: {1:'B5_saturated'},
                                 6: {1:'B6_saturated'},
                                 7: {1:'B7_saturated'},
                             })

        radsat_qa_8 = Band('radsat_qa', 'radsat_qa', 'uint16', 30,
                           reference='bits',
                           bits={
                               1: {1:'B1_saturated'},
                               2: {1:'B2_saturated'},
                               3: {1:'B3_saturated'},
                               4: {1:'B4_saturated'},
                               5: {1:'B5_saturated'},
                               6: {1:'B6_saturated'},
                               7: {1:'B7_saturated'},
                               9: {1:'B9_saturated'},
                               10: {1:'B10_saturated'},
                               11: {1:'B11_saturated'},
                           })

        bqa = Band('BQA', 'bqa', 'uint16', 30, reference='bits',
                   bits={'4': {1:'cloud'},
                         '5-6': {3:'high_confidence_cloud'},
                         '7-8': {3:'shadow'},
                         '9-10': {3:'snow'}})

        sr_aerosol = Band('sr_aerosol', 'sr_aerosol', 'uint8', 30,
                          reference='bits',
                          bits={
                              '3': {1: 'water'},
                              '6-7': {0: 'climatology',
                                      1: 'low',
                                      2:'medium',
                                      3: 'high'}
                          })

        if sensor in ['MSS']:
            green = Band('B1', 'green', 'int8', 60, 0, 255, 'optical')
            red = Band('B2', 'red', 'int8', 60, 0, 255, 'optical')
            nir = Band('B3', 'nir', 'int8', 60, 0, 255, 'optical')
            nir2 = Band('B4', 'nir2', 'int8', 30, 0, 255, 'optical')
            qa = Band('BQA', 'bqa', 'int16', 60, reference='bits',
                       bits={'4': {1: 'cloud'}})
            if number in [1, 2, 3]:
                green.id = 'B4'
                red.id = 'B5'
                nir.id = 'B6'
                nir2.id = 'B7'
            band[0] = green
            band[1] = red
            band[2] = nir
            band[3] = nir2
            band[4] = qa

        # Opticals
        if number in [4, 5, 7]:
            common = dict(scale=30, reference='optical')
            band[0] = Band('B1', 'blue', **common)
            band[1] = Band('B2', 'green', **common)
            band[2] = Band('B3', 'red', **common)
            band[3] = Band('B4', 'nir', **common)
            band[4] = Band('B5', 'swir', **common)
            band[5] = Band('B6', 'thermal', scale=30, reference='thermal')
            band[6] = Band('B7', 'swir2', **common)
            if process in ['SR']:
                # set precision for SR
                for b in band:
                    if not b: continue
                    b.precision = 'int16'
                    b.min = 0
                    b.max = max_sr
                band[7] = atm_op
                band[8] = sr_cloud_qa
                pixel_qa.bits = {'1': {1:'clear'}, '2': {1:'water'},
                                 '3': {1:'shadow'}, '4': {1:'snow'},
                                 '5': {1:'cloud'},
                                 '6-7':{3:'high_confidence_cloud'}}
                band[9] = pixel_qa
                band[10] = radsat_qa_457
            if process in ['TOA']:
                for b in band:
                    if not b: continue
                    b.precision = 'float'
                    b.min = 0
                    b.max = max_toa_optical
            if process in ['RAW']:
                for b in band:
                    if not b: continue
                    b.precision = 'uint8'
                    b.min = 0
                    b.max = max_raw

        # BQA
        if number in [4, 5] and process in ['RAW', 'TOA']:
            band[7] = bqa

        if number in [7] and process in ['RAW', 'TOA']:
            band[9] = bqa
            # change swir2 from position 6 to 7
            band[7] = band[6]

        # B6_VCID_1/2 bands. Overwrites band 5 set before
        if number in [7] and process in ['TOA']:
            band[5] = Band('B6_VCID_1', 'thermal', 'float', 30, 0,
                           max_toa_thermal, reference='thermal')
            band[6] = Band('B6_VCID_2', 'thermal2', 'float', 30, 0,
                           max_toa_thermal, reference='thermal')
            # set pan band
            band[8] = Band('B8', 'pan', 'float', 15, 0, max_toa_optical,
                           reference='optical')

        if number in [7] and process in ['RAW']:
            band[5] = Band('B6_VCID_1', 'thermal', 'uint8', 30, 0, max_raw,
                           reference='thermal')
            band[6] = Band('B6_VCID_2', 'thermal2', 'uint8', 30, 0,
                           max_raw, reference='thermal')
            # set pan band
            band[8] = Band('B8', 'pan', 'uint8', 15, 0, max_raw,
                           reference='optical')

        if self.number == 8:
            common = dict(scale=30)
            thermal = Band('B10', 'thermal', reference='thermal', **common)
            thermal2 = Band('B11', 'thermal2', reference='thermal',**common)
            pan = Band('B8', 'pan', reference='optical', scale=15)
            cirrus = Band('B9', 'cirrus', reference='optical', scale=15)

            band[0] = Band('B1', 'aerosol', reference='optical', **common)
            band[1] = Band('B2', 'blue', reference='optical', **common)
            band[2] = Band('B3', 'green', reference='optical', **common)
            band[3] = Band('B4', 'red', reference='optical',**common)
            band[4] = Band('B5', 'nir', reference='optical',**common)
            band[5] = Band('B6', 'swir', reference='optical',**common)
            band[6] = Band('B7', 'swir2', reference='optical', **common)
            if process in ['SR']:
                band[7] = thermal
                band[8] = thermal2
                for b in band:
                    if not b: continue
                    b.precision = 'int16'
                    b.min = 0
                    b.max = max_sr
                band[9] = sr_aerosol
                pixel_qa.bits = {'1': {1:'clear'}, '2': {1:'water'},
                                 '3': {1:'shadow'}, '4': {1:'snow'},
                                 '5': {1:'cloud'},
                                 '6-7':{3:'high_confidence_cloud'},
                                 '8-9':{3:'high_confidence_cirrus'}
                                 }
                band[10] = pixel_qa
                band[11] = radsat_qa_8
            if process in ['TOA']:
                band[7] = pan
                band[8] = cirrus
                band[9] = thermal
                band[10] = thermal2
                for b in band:
                    if not b: continue
                    b.precision = 'float'
                    b.min = 0
                    if b.reference == 'optical':
                        b.max = max_toa_optical
                    elif b.reference == 'thermal':
                        b.max = max_toa_thermal
                band[11] = bqa
            if process in ['RAW']:
                band[7] = pan
                band[8] = cirrus
                band[9] = thermal
                band[10] = thermal2
                for b in band:
                    if not b: continue
                    b.precision = 'uint16'
                    b.min = 0
                    b.max = max_raw_8
                band[11] = bqa

        return [b for b in band if b]

    def harmonize(self, image, renamed=False):
        """ HARMONIZATION """
        options = ['blue', 'green', 'red', 'nir', 'swir', 'swir2']
        if self.number == 8:
            if renamed:
                bands = {band.name:band.name for band in self.bands if band.name in options}
            else:
                bands = {band.name:band.id for band in self.bands if band.name in options}

            max_value = max(
                [band.max for band in self.bands if band.name in options])
            harmonized = module_alg.Landsat.harmonization(
                image, max_value=max_value, **bands)
        else:
            harmonized = image

        return harmonized

    def brdf(self, image, renamed=False):
        """ BRDF Correction """
        # BRDF
        bands = []
        all_present = True
        for band in ['red', 'green', 'blue', 'nir', 'swir', 'swir2']:
            if not renamed:
                bid = self.getBand(band, 'name').id
            else:
                bid = self.getBand(band, 'name').name
            if not bid:
                all_present = False
                break
            bands.append(bid)

        if all_present:
            return module_alg.Landsat.brdfCorrect(image, *bands)
        else:
            return image

    def _rescale(self, band_type, image, number, process, drop=False,
                 renamed=False):
        # Create comparative collection
        bands = ee.Dictionary(self.bands)

        proxy = Landsat(number, process)

        if band_type == 'thermal':
            this_band = list(self.thermalBands.keys())
            proxy_band = list(proxy.thermalBands.keys())

        if band_type == 'optical':
            this_band = list(self.opticalBands.keys())
            proxy_band = list(proxy.opticalBands.keys())

        # get common bands for thermal (thermal1, etc..)
        # common_bands = ee.List([band for band in this_band if band in
        # proxy_band])
        common_bands = tools.ee_list.intersection(ee.List(this_band),
                                                  ee.List(proxy_band))

        ranges_this = ee.Dictionary(self.ranges)
        ranges_proxy = ee.Dictionary(proxy.ranges)

        def iteration(band, ini):
            ini = ee.Image(ini)
            band = ee.String(band)
            ranges_this_band = ee.Dictionary(ranges_this.get(band))
            ranges_proxy_band = ee.Dictionary(ranges_proxy.get(band))
            min_this = ee.Number(ranges_this_band.get('min'))
            min_proxy = ee.Number(ranges_proxy_band.get('min'))
            max_this = ee.Number(ranges_this_band.get('max'))
            max_proxy = ee.Number(ranges_proxy_band.get('max'))
            if not renamed:
                band = ee.String(bands.get(band))
            return tools.image.parametrize(ini,
                                           (min_this, max_this),
                                           (min_proxy, max_proxy),
                                           bands=[band])

        final = ee.Image(common_bands.iterate(iteration, image))
        if drop:
            if not renamed:
                common_bands = tools.dictionary.extractList(self.bands,
                                                            common_bands)
            final = final.select(common_bands)

        return final

    def rescaleThermal(self, image, number, process, drop=False,
                       renamed=False):
        """ Re-scale only the thermal bands of an image to match the band
        from the given number and process """
        return self._rescale('thermal', image, number, process, drop, renamed)

    def rescaleOptical(self, image, number, process, drop=False,
                       renamed=False):
        """ Re-scale only the optical bands of an image to match the band
        from the given number and process """
        return self._rescale('optical', image, number, process, drop, renamed)

    def rescaleAll(self, image, number, process, drop=False, renamed=False):
        """ Re-scale only the optical and thermal bands of an image to match
        the band from the given number and process """
        if drop:
            optical = self._rescale('optical', image, number,
                                    process, True, renamed)

            thermal = self._rescale('thermal', image, number,
                                process, True, renamed)

            all = optical.addBands(thermal)
        else:
            optical = self._rescale('optical', image, number,
                                    process, False, renamed)

            all = self._rescale('thermal', optical, number,
                                process, False, renamed)

        return all

    # FACTORY
    @classmethod
    def Landsat1(cls, tier=1):
        return cls(1, tier=tier)

    @classmethod
    def Landsat2(cls, tier=1):
        return cls(2, tier=tier)

    @classmethod
    def Landsat3(cls, tier=1):
        return cls(3, tier=tier)

    @classmethod
    def Landsat4SR(cls, tier=1):
        return cls(4, sensor='TM', process='SR', tier=tier)

    @classmethod
    def Landsat4TOA(cls, tier=1):
        return cls(4, sensor='TM', process='TOA', tier=tier)

    @classmethod
    def Landsat5SR(cls, tier=1):
        return cls(5, process='SR', tier=tier)

    @classmethod
    def Landsat5TOA(cls, tier=1):
        return cls(5, process='TOA', tier=tier)

    @classmethod
    def Landsat7SR(cls, tier=1):
        return cls(7, process='SR', tier=tier)

    @classmethod
    def Landsat7TOA(cls, tier=1):
        return cls(7, process='TOA', tier=tier)

    @classmethod
    def Landsat8SR(cls, tier=1):
        return cls(8, process='SR', tier=tier)

    @classmethod
    def Landsat8TOA(cls, tier=1):
        return cls(8, process='TOA', tier=tier)
