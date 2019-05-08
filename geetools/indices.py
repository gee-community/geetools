# coding=utf-8
""" Functions for calculation indices """
from __future__ import print_function
import ee


FORMULAS = {
    'NDVI': '(NIR-RED)/(NIR+RED)',
    'EVI': 'G*((NIR-RED)/(NIR+(C1*RED)-(C2*BLUE)+L))',
    'NBR': '(NIR-SWIR2)/(NIR+SWIR2)',
    'NBR2': '(SWIR-SWIR2)/(SWIR+SWIR2)'
}

AVAILABLE = FORMULAS.keys()

def compute(image, index, band_params, extra_params=None, bandname=None):
    if index not in AVAILABLE:
        raise ValueError('Index not available')

    if not bandname:
        bandname = index

    extra_params = extra_params if extra_params else {}

    formula = FORMULAS[index]

    band_params_mapped = {
        key: image.select([val]) for key, val in band_params.items()}
    band_params_mapped.update(extra_params)
    nd = image.expression(formula, band_params_mapped).rename(bandname)

    return nd

def ndvi(image, nir, red, bandname='ndvi'):
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
    return compute(image, 'NDVI', {'NIR':nir, 'RED':red}, bandname=bandname)


def evi(image, nir, red, blue, G=2.5, C1=6, C2=7.5, L=1, bandname='evi'):
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

    return compute(image, 'EVI', {'NIR':nir, 'RED':red, 'BLUE':blue},
                   {'G':G, 'C1':C1, 'C2':C2, 'L':L}, bandname=bandname)


def nbr(image, nir, swir2, bandname='nbr'):
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
    return compute(image, 'NBR', {'NIR':nir, 'SWIR2':swir2}, bandname=bandname)


def nbr2(image, swir, swir2, bandname='nbr2'):
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
    return compute(image, 'NBR2', {'SWIR':swir, 'SWIR2':swir2}, bandname=bandname)


REL = {"NDVI": ndvi,
       "EVI": evi,
       "NBR": nbr,
       "NBR2": nbr2
       }