# coding=utf-8
""" Google Earth Engine MODIS Collections """

from . import Collection, TODAY, Band
from functools import partial

IDS = [
    'MODIS/006/MOD09GQ', 'MODIS/006/MYD09GQ',
    'MODIS/006/MOD09GA', 'MODIS/006/MYD09GA',
    'MODIS/006/MOD13Q1', 'MODIS/006/MYD13Q1'
]

START = {
    'MODIS/006/MOD09GQ': '2000-02-24',
    'MODIS/006/MYD09GQ': '2000-02-24',
    'MODIS/006/MOD09GA': '2000-02-24',
    'MODIS/006/MYD09GA': '2000-02-24',
    'MODIS/006/MOD13Q1': '2000-02-18',
    'MODIS/006/MYD13Q1': '2000-02-18',
}

END = {
    'MODIS/006/MOD09GQ': TODAY,
    'MODIS/006/MYD09GQ': TODAY,
    'MODIS/006/MOD09GA': TODAY,
    'MODIS/006/MYD09GA': TODAY,
    'MODIS/006/MOD13Q1': TODAY,
    'MODIS/006/MYD13Q1': TODAY,
}


class MODIS(Collection):
    """ MODIS Collections """
    def __init__(self, product_id):
        """ Initialize a MODIS collection with it's product id """
        super(MODIS, self).__init__()
        self.product_id = product_id
        self._id = self._make_id()
        self._bands = self._make_bands()

        # dates
        self.start_date = START[self._id]
        self.end_date = END[self._id]

        self.spacecraft = 'MODIS'

        self.cloud_cover = None

    def _make_bands(self):
        bands = [None]*30

        # Partial bands
        sur_refl_b01 = partial(Band, id='sur_refl_b01', name='red',
                               precision='int16', min=-100,
                               max=16000, reference='optical')

        sur_refl_b02 = partial(Band, id='sur_refl_b02', name='nir',
                               precision='int16', min=-100,
                               max=16000, reference='optical')

        num_observations = partial(Band, precision='int8', min=0, max=127,
                                   reference='classification')

        QC_250m = Band('QC_250m', 'QC_250m', 'uint16', 250, 0, 4096,
                       'bits', bits={
                            '4-7': {0: 'B1_highest_quality'},
                            '8-11': {0: 'B2_highest_quality'},
                            '12': {1: 'atmospheric_corrected'}
                        })

        obscov = partial(Band, precision='int8', min=0, max=100,
                         reference='classification')

        iobs_res = partial(Band, id='iobs_res', name='obs_number',
                           precision='uint8', min=0, max=254,
                           reference='classification')

        orbit_pnt = partial(Band, id='orbit_pnt', name='orbit_pointer',
                            precision='int8', min=0, max=15,
                            reference='classification')

        granule_pnt = partial(Band, id='granule_pnt', name='granule_pointer',
                              precision='uint8', min=0, max=254,
                              reference='classification')

        state_1km = Band('state_1km', 'state_1km', 'uint16', 1000, 0, 57335,
                         'bits', bits={
                            '0-1': {0: 'clear', 1:'cloud', 2:'mix'},
                            '2':   {1: 'shadow'},
                            '8-9': {1: 'small_cirrus', 2: 'average_cirrus',
                                    3: 'high_cirrus'},
                            '13':  {1: 'adjacent'},
                            '15':  {1: 'snow'}
                        })
        sezenith = Band('SensorZenith', 'sensor_zenith', 'int16', 1000, 0,
                        18000, 'classification')
        seazimuth = Band('SensorAzimuth', 'sensor_azimuth', 'int16', 1000,
                         -18000, 18000, 'classification')
        range_band = Band('Range', 'range', 'uint16', 1000, 27000, 65535,
                     'classification')
        sozenith = Band('SolarZenith', 'solar_zenith', 'int16', 1000, 0,
                        18000, 'classification')
        soazimuth = Band('SolarAzimuth', 'solar_azimuth', 'int16', 1000,
                         -18000, 18000, 'classification')
        gflags = Band('gflags', 'geolocation_flags', 'uint8', 1000, 0, 248,
                      'bits')

        sur_refl_b03 = partial(Band, id='sur_refl_b03', name='blue',
                               precision='int16', min=-100, max=16000,
                               reference='optical')

        sur_refl_b04 = partial(Band, id='sur_refl_b04', name='green',
                               precision='int16', min=-100, max=16000,
                               reference='optical')

        sur_refl_b05 = partial(Band, id='sur_refl_b05', name='swir3',
                               precision='int16', min=-100, max=16000,
                               reference='optical')

        sur_refl_b06 = partial(Band, id='sur_refl_b06', name='swir',
                               precision='int16', min=-100, max=16000,
                               reference='optical')

        sur_refl_b07 = partial(Band, id='sur_refl_b07', name='swir2',
                               precision='int16', min=-100, max=16000,
                               reference='optical')

        QC_500m = Band('QC_500m', 'QC_500m', 'uint32', 500, 0, 4294966019,
                       'bits', bits={
                            '2-5': {0: 'B1_highest_quality'},
                            '6-9': {0: 'B2_highest_quality'},
                            '10-13': {0: 'B3_highest_quality'},
                            '14-17': {0: 'B4_highest_quality'},
                            '18-21': {0: 'B5_highest_quality'},
                            '22-25': {0: 'B6_highest_quality'},
                            '26-29': {0: 'B7_highest_quality'},
                        })

        qscan = Band('q_scan', 'q_scan', 'uint8', 250, 0, 254, 'bits')

        NDVI = Band('NDVI', 'ndvi', 'int16', 250, -2000, 10000, 'classification')

        EVI = Band('EVI', 'evi', 'int16', 250, -2000, 10000, 'classification')

        DetailedQA = Band('DetailedQA', 'detailed_qa', 'uint16', 250, 0, 65534,
                          'bits', bits={
                            '0-1': {0: 'good_qa'},
                            '2-5': {0: 'highest_qa'},
                            '8':   {1: 'adjacent'},
                            '10':  {1: 'cloud'},
                            '14':  {1: 'snow'},
                            '15':  {1: 'shadow'}
                          })

        view_zenith = Band('ViewZenith', 'view_zenith', 'int16', 250, 0, 18000,
                           'classification')

        relative_azimuth = Band('RelativeAzimuth', 'relative_azimuth', 'int16',
                                250, -18000, 18000, 'classification')

        DayOfYear = Band('DayOfYear', 'day_of_year', 'int16', 250, 1, 366,
                         'classification')

        SummaryQA = Band('SummaryQA', 'summary_qa', 'int8', 250, 0, 3, 'bits',
                         bits={
                             '0-1': {0: 'clear', 1: 'marginal', 2: 'snow',
                                     3: 'cloud'}
                         })

        if self.product_id in ['MOD09GQ', 'MYD09GQ']:
            bands[0] = num_observations(id='num_observations',
                                        name='num_observations', scale=250)
            bands[1] = sur_refl_b01(scale=250)
            bands[2] = sur_refl_b02(scale=250)
            bands[3] = QC_250m
            bands[4] = obscov(id='obscov', name='observation_coverage', scale=250)
            bands[5] = iobs_res(scale=250)
            bands[6] = orbit_pnt(scale=250)
            bands[7] = granule_pnt(scale=250)

        if self.product_id in ['MOD09GA', 'MYD09GA']:
            bands[0] = num_observations(id='num_observations_1km', scale=1000,
                                        name='num_observations_1km')
            bands[1] = state_1km
            bands[2] = sezenith
            bands[3] = seazimuth
            bands[4] = range_band
            bands[5] = sozenith
            bands[6] = soazimuth
            bands[7] = gflags
            bands[8] = orbit_pnt(scale=500)
            bands[9] = granule_pnt(scale=500)
            bands[10] = num_observations(id='num_observations_500m', scale=500,
                                         name='num_observations_500m')
            bands[11] = sur_refl_b01(scale=500)
            bands[12] = sur_refl_b02(scale=500)
            bands[13] = sur_refl_b03(scale=500)
            bands[14] = sur_refl_b04(scale=500)
            bands[15] = sur_refl_b05(scale=500)
            bands[16] = sur_refl_b06(scale=500)
            bands[17] = sur_refl_b07(scale=500)
            bands[18] = QC_500m
            bands[19] = obscov(id='obscov_500m', scale=500,
                               name='observation_coverage_500m')
            bands[20] = iobs_res(scale=500)
            bands[21] = qscan

        if self.product_id in ['MOD13Q1', 'MYD13Q1']:
            bands[0] = NDVI
            bands[1] = EVI
            bands[2] = DetailedQA
            bands[3] = sur_refl_b01(scale=250)
            bands[4] = sur_refl_b02(scale=250)
            bands[5] = sur_refl_b03(scale=250)
            bands[6] = sur_refl_b07(scale=250)
            bands[7] = view_zenith
            bands[8] = sozenith
            bands[9] = relative_azimuth
            bands[10] = DayOfYear
            bands[11] = SummaryQA

        return [b for b in bands if b]

    def _make_id(self):
        return 'MODIS/006/{}'.format(self.product_id)

    @staticmethod
    def fromId(id):
        """ Make a MODIS collection from its ID """
        def error():
            msg = 'Collection {} not available'
            raise ValueError(msg.format(id))

        if id not in IDS: error()

        splitted = id.split('/')
        prod = splitted[2]

        return MODIS(prod)

    @classmethod
    def MOD09GQ(cls):
        return cls(product_id='MOD09GQ')

    @classmethod
    def MYD09GQ(cls):
        return cls(product_id='MYD09GQ')

    @classmethod
    def MOD09GA(cls):
        return cls(product_id='MOD09GA')

    @classmethod
    def MYD09GA(cls):
        return cls(product_id='MYD09GA')

    @classmethod
    def MOD13Q1(cls):
        return cls(product_id='MOD13Q1')

    @classmethod
    def MYD13Q1(cls):
        return cls(product_id='MYD13Q1')
