# coding=utf-8
""" Functions for calculation indices """
from __future__ import print_function
import ee

import ee.data
if not ee.data._initialized: ee.Initialize()

true = ee.Number(1)
false = ee.Number(0)

FORMULAS = {
    'NDVI': '(NIR-RED)/(NIR+RED)',
    'EVI': 'G*((NIR-RED)/(NIR+(C1*RED)-(C2*BLUE)+L))',
    'NBR': '(NIR-SWIR2)/(NIR+SWIR2)',
    'NBR2': '(SWIR-SWIR2)/(SWIR+SWIR2)'
}

AVAILABLE = FORMULAS.keys()

def compute(index, band_params, extra_params=None, addBand=True,
            bandname=None):
    if index not in AVAILABLE:
        raise ValueError('Index not available')

    if not bandname:
        bandname = index

    addBandEE = true if addBand else false
    extra_params = extra_params if extra_params else {}

    formula = FORMULAS[index]

    def calc(img):
        band_params_mapped = {
            key: img.select([val]) for key, val in band_params.items()}
        band_params_mapped.update(extra_params)
        nd = img.expression(formula, band_params_mapped).select([0], [bandname])
        result = ee.Algorithms.If(addBandEE, img.addBands(nd), nd)
        return ee.Image(result)

    return calc

def ndvi(nir, red, bandname='ndvi', addBand=True):
    """ Calculates NDVI index

    :USE:

    .. code:: python

        # use in a collection
        col = ee.ImageCollection(ID)
        ndvi = col.map(indices.ndvi("B4", "B3"))

        # use in a single image
        img = ee.Image(ID)
        ndvi = Indices.ndvi("NIR", "RED")(img)

    :param nir: name of the Near Infrared () band
    :type nir: str
    :param red: name of the red () band
    :type red: str
    :param addBand: if True adds the index band to the others, otherwise
        returns just the index band
    :type addBand: bool
    :return: The function to apply a map() over a collection
    :rtype: function
    """
    return compute('NDVI', {'NIR':nir, 'RED':red},
                   addBand=addBand, bandname=bandname)


def evi(nir, red, blue, G=2.5, C1=6, C2=7.5, L=1,
        bandname='evi', addBand=True):
    """ Calculates EVI index

    :param nir: name of the Near Infrared () band
    :type nir: str
    :param red: name of the red () band
    :type red: str
    :param blue: name of the blue () band
    :type blue: str
    :param G: G coefficient for the EVI index
    :type G: float
    :param C1: C1 coefficient for the EVI index
    :type C1: float
    :param C2: C2 coefficient for the EVI index
    :type C2: float
    :param L: L coefficient for the EVI index
    :type L: float
    :param addBand: if True adds the index band to the others, otherwise
        returns just the index band
    :return: The function to apply a map() over a collection
    :rtype: function
    """
    G = float(G)
    C1 = float(C1)
    C2 = float(C2)
    L = float(L)

    return compute('EVI', {'NIR':nir, 'RED':red, 'BLUE':blue},
                          {'G':G, 'C1':C1, 'C2':C2, 'L':L},
                   addBand=addBand, bandname=bandname)


def nbr(nir, swir2, bandname='nbr', addBand=True):
    """ Calculates NBR index

    :USE:

    .. code:: python

        # use in a collection
        col = ee.ImageCollection(ID)
        ndvi = col.map(indices.ndvi("B4", "B3"))

        # use in a single image
        img = ee.Image(ID)
        ndvi = Indices.ndvi("NIR", "RED")(img)

    :param nir: name of the Near Infrared () band
    :type nir: str
    :param red: name of the red () band
    :type red: str
    :param addBand: if True adds the index band to the others, otherwise
        returns just the index band
    :type addBand: bool
    :return: The function to apply a map() over a collection
    :rtype: function
    """
    return compute('NBR', {'NIR':nir, 'SWIR2':swir2}, addBand=addBand,
                   bandname=bandname)


def nbr2(swir, swir2, bandname='nbr2', addBand=True):
    """ Calculates NBR index

    :USE:

    .. code:: python

        # use in a collection
        col = ee.ImageCollection(ID)
        ndvi = col.map(indices.ndvi("B4", "B3"))

        # use in a single image
        img = ee.Image(ID)
        ndvi = Indices.ndvi("NIR", "RED")(img)

    :param nir: name of the Near Infrared () band
    :type nir: str
    :param red: name of the red () band
    :type red: str
    :param addBand: if True adds the index band to the others, otherwise
        returns just the index band
    :type addBand: bool
    :return: The function to apply a map() over a collection
    :rtype: function
    """
    return compute('NBR2', {'SWIR':swir, 'SWIR2':swir2}, addBand=addBand,
                   bandname=bandname)


REL = {"NDVI": ndvi,
       "EVI": evi,
       "NBR": nbr,
       "NBR2": nbr2
       }