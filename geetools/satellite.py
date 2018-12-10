# coding=utf-8
""" Module holding common data for common satellites, such as Landsat, Sentinel
 MODIS, etc

All properties are lower case and spaces are underscores
"""
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()

from . import cloud_mask
from . import bitreader

from datetime import datetime

def today():
    return datetime.today().isoformat()[0:10]

_SHORT_RELATION = {
    'LANDSAT_8_SR': 'LANDSAT/LC08/C01/T1_SR',
    'LANDSAT_7_SR': 'LANDSAT/LE07/C01/T1_SR'
}

_AVAILABLE_IDS = [
    'LANDSAT/LC08/C01/T1_SR', 'LANDSAT/LE07/C01/T1_SR'
]


class Satellite(object):
    def __init__(self, col_id):
        """ Initialize a Satellite object giving its Google Earth Engine ID

        :param col_id: Google Earth Engine collection ID
            (example: 'LANDSAT/LC08/C01/T1_SR')
        :type col_id: str
        """
        if col_id in _SHORT_RELATION.keys():
            col_id = _SHORT_RELATION[col_id]

        options = _AVAILABLE_IDS+list(_SHORT_RELATION.keys())

        if col_id not in options:
            msg = 'ImageCollection {} not available in this module. Available'\
                  ' collections are {}'
            raise ValueError(msg.format(col_id, options))

        self.col_id = col_id

        self._band_names = None
        self._property_names = None

    @property
    def information(self):
        return SATELLITE_ID_INFO[self.col_id]

    @property
    def band_names(self):
        # return self.information.get('band_names')
        if not self._band_names:
            image = ee.Image(self.collection.first())
            self._band_names = image.bandNames().getInfo()

        return self._band_names

    @property
    def property_names(self):
        # return self.information.get('band_names')
        if not self._property_names:
            image = ee.Image(self.collection.first())
            self._property_names = image.propertyNames().getInfo()

        return self._property_names

    @property
    def bands(self):
        return self.information['bands']

    @property
    def band_resolution(self):
        return self.information['band_resolution']

    @property
    def collection(self):
        return ee.ImageCollection(self.col_id)

    @property
    def short_id(self):
        return self.information['short_id']

    @property
    def cloud_cover(self):
        return self.information['cloud_cover']

    @property
    def bitmasks(self):
        return self.information['bitmasks']

    @property
    def start(self):
        """ Start date """
        return self.information['start']

    @property
    def end(self):
        """ End date """
        return self.information['end']

    def get_band_name(self, band):
        """ Gets the band name. For example

        get_band_name('B4') = 'red'
        """
        if band in self.bands.values():
            inverse = {val:key for key, val in self.bands.items()}
            return inverse[band]
        else:
            msg = 'band {} not founds in collection {}'
            raise ValueError(msg.format(band, self.col_id))

BANDS_RELATION = {
    "LANDSAT_8":
        {
            'blue': 'B2',
            'green': 'B3',
            'red': 'B4',
            'nir': 'B5',
            'swir': 'B6',
            'swir2': 'B7',
            'thermal': 'B10',
            'thermal2': 'B11'
        },
    "LANDSAT_4":
        {
            'blue': 'B1',
            'green': 'B2',
            'red': 'B3',
            'nir': 'B4',
            'swir': 'B5',
            'swir2': 'B7',
            'thermal': 'B6'
        }

}

BAND_SCALES = {
    "LANDSAT_8":
        {
        'B1': 30,
        'B2': 30,
        'B3': 30,
        'B4': 30,
        'B5': 30,
        'B6': 30,
        'B7': 30,
        'B10': 30,
        'B11': 30,
        'pixel_qa': 30,
        'sr_aerosol': 30,
        'radsat_qa': 30}
}

LANDSAT_8_SR = {
    'LANDSAT/LC08/C01/T1_SR': {
        'short_id': 'LANDSAT_8_SR',
        'band_names': Satellite('LANDSAT/LC08/C01/T1_SR').band_names,
        'bands': BANDS_RELATION['LANDSAT_8'],
        'band_resolution': BAND_SCALES['LANDSAT_8'],
        'extra_bands': {},
        'property_names': Satellite('LANDSAT/LC08/C01/T1_SR').property_names,
        'cloud_cover': {
            'property': 'CLOUD_COVER',
            'range': [0, 100]
        },
        'bitmasks': [
            {
                'band': 'pixel_qa',
                'bitreader': bitreader.BitReader(
                    cloud_mask.BITS_LANDSAT_PIXEL_QA_L8, 16),
                'bits': cloud_mask.BITS_LANDSAT_PIXEL_QA_L8
            },
            {
                'band': 'sr_aerosol',
                'bitreader': None,
                'bits': None
            },
            {
                'band': 'radsat_qa',
                'bitreader': None,
                'bits': None
            }
        ],
        'start': '2013-04-11',
        'end': today()
    }
}

LANDSAT_7_SR = {
    'LANDSAT/LE07/C01/T1_SR': {
        'short_id': 'LANDSAT_7_SR',
        'band_names': Satellite('LANDSAT/LE07/C01/T1_SR').band_names,
        'bands': {
            'blue': 'B1',
            'green': 'B2',
            'red': 'B3',
            'nir': 'B4',
            'swir1': 'B5',
            'swir2': 'B7',
            'thermal1': 'B6'
        },
        'extra_bands': {
            'atmos_opacity': 'sr_atmos_opacity'
        },
        'band_resolution': {
            'B1': 30,
            'B2': 30,
            'B3': 30,
            'B4': 30,
            'B5': 30,
            'B6': 30,
            'B7': 30,
            'sr_atmos_opacity': 30,
            'sr_cloud_qa': 30,
            'pixel_qa': 30,
            'radsat_qa': 30
        },
        'property_names': Satellite('LANDSAT/LE07/C01/T1_SR').property_names,
        'cloud_cover': {
            'property': 'CLOUD_COVER',
            'range': [0, 100]
        },
        'bitmasks': [
            {
                'band': 'pixel_qa',
                'bitreader': bitreader.BitReader(
                    cloud_mask.BITS_LANDSAT_PIXEL_QA, 16),
                'bits': cloud_mask.BITS_LANDSAT_PIXEL_QA
            },
            {
                'band': 'sr_cloud_qa',
                'bitreader': bitreader.BitReader(
                    cloud_mask.BITS_LANDSAT_CLOUD_QA, 8),
                'bits': cloud_mask.BITS_LANDSAT_CLOUD_QA
            },
            {
                'band': 'radsat_qa',
                'bitreader': None,
                'bits': None
            }
        ],
        'start': '1999-01-01',
        'end': today()
    }
}

SATELLITE_ID_INFO = dict()

def update(*sat):
    for s in sat:
        SATELLITE_ID_INFO.update(s)

update(LANDSAT_8_SR, LANDSAT_7_SR)
