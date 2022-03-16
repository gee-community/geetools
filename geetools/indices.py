# coding=utf-8
""" Functions for calculation indices """
import ee

FORMULAS = {
    'NDVI': '(NIR-RED)/(NIR+RED)',
    'EVI': 'G*((NIR-RED)/(NIR+(C1*RED)-(C2*BLUE)+L))',
    'NBR': '(NIR-SWIR2)/(NIR+SWIR2)',
    'NBR2': '(SWIR-SWIR2)/(SWIR+SWIR2)',
    'NDWI': '(NIR-SWIR)/(NIR+SWIR)'
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


def ndfi(image, blue, green, red, nir, swir1, swir2, clouds=0.1,
         bandname='NDFI'):
    """ Calculate NDFI using endmembers from Souza et al., 2005.
    Image values must be float. Returns an Image with the following bands:
     - GV: Green Vegetation
     - Shade: Shadow
     - NPV: Not Photosynthetic Vegetation
     - Soil: Soil
     - {bandname}: index name as passed in arguments. Defaults to NDFI, which
        stands for Normalized Difference Fraction Index
     """
    gv = [.0500, .0900, .0400, .6100, .3000, .1000]
    shade = [0, 0, 0, 0, 0, 0]
    npv = [.1400, .1700, .2200, .3000, .5500, .3000]
    soil = [.2000, .3000, .3400, .5800, .6000, .5800]
    cloud = [.9000, .9600, .8000, .7800, .7200, .6500]
    cfThreshold = ee.Image.constant(clouds)
    image = image.select([blue, green, red, nir, swir1, swir2])
    unmixImage = ee.Image(image).unmix(
        [gv, shade, npv, soil, cloud], True, True
    )
    unmixImage = unmixImage.rename(['band_0', 'band_1', 'band_2',
                                    'band_3', 'band_4'])
    newImage = ee.Image(image).addBands(unmixImage)
    mask = newImage.select('band_4').lt(cfThreshold)
    ndfi = ee.Image(unmixImage).expression(
        '((GV / (1 - SHADE)) - (NPV + SOIL)) / ((GV / (1 - SHADE)) + NPV + SOIL)',
        {
            'GV': ee.Image(unmixImage).select('band_0'),
            'SHADE': ee.Image(unmixImage).select('band_1'),
            'NPV': ee.Image(unmixImage).select('band_2'),
            'SOIL': ee.Image(unmixImage).select('band_3')
        })

    final = ee.Image(newImage).addBands(ee.Image(ndfi).rename(['NDFI']))
    final = final.select(['band_0', 'band_1', 'band_2', 'band_3', 'NDFI'])
    final = final.rename(['GV', 'Shade', 'NPV', 'Soil', bandname])
    final = final.updateMask(mask)
    return final


def tasseled_cap_s2(image, blue='B2', green='B3', red='B4', nir='B8',
                    swir1='B11', swir2='B12'):
    # Define an Array of Tasseled Cap coefficients.
    coefficients = ee.Array([
        [0.3510, 0.3813, 0.3437, 0.7196, 0.2396, 0.1949],
        [-0.3599, -0.3533, -0.4734, 0.6633, 0.0087, -0.2856],
        [0.2578, 0.2305, 0.0883, 0.1071, -0.7611, -0.5308]
    ])

    image = image.select([blue, green, red, nir, swir1, swir2])

    # Make an Array Image, with a 1-D Array per pixel.
    arrayImage1D = image.toArray()

    # Make an Array Image with a 2-D Array per pixel, 6x1.
    arrayImage2D = arrayImage1D.toArray(1)

    # Do a matrix multiplication: 6x6 times 6x1.
    componentsImage = ee.Image(coefficients).matrixMultiply(arrayImage2D)

    # Get rid of the extra dimensions.
    componentsImage = componentsImage.arrayProject([0]).arrayFlatten(
    [['brightness', 'greenness', 'wetness']])

    return componentsImage


REL = {"NDVI": ndvi,
       "EVI": evi,
       "NBR": nbr,
       "NBR2": nbr2,
       "NDFI": ndfi
       }