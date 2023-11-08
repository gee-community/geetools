# coding=utf-8
"""Legacy function to compute Spectral indices."""
import ee
from deprecated.sphinx import deprecated

AVAILABLE = ee.Image.geetools.index_list().keys()


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def compute(image, index, band_params, extra_params=None, bandname=None):
    """Compute a spectral index."""
    return image.geetools.spectralIndices(index)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def ndvi(image, nir, red, bandname="ndvi"):
    """Calculates NDVI index."""
    return image.geetools.spectralIndices("NDVI")


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def evi(image, nir, red, blue, G=2.5, C1=6, C2=7.5, L=1, bandname="evi"):
    """Calculates EVI index."""
    return image.geetools.spectralIndices("EVI", G=2.5, C1=6, C2=7.5, L=1)


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def nbr2(image, swir, swir2, bandname="nbr2"):
    """Calculates NBR index."""
    return image.geetools.spectralIndices("NBR2")


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def nbr(image, swir, swir2, bandname="nbr"):
    """Calculates NBR index."""
    return image.geetools.spectralIndices("NBR")


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def ndfi(image, blue, green, red, nir, swir1, swir2, clouds=0.1, bandname="NDFI"):
    """Calculate NDFI index."""
    return image.geetools.spectralIndices("NDFI")


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.spectralIndices() instead")
def tasseled_cap_s2(
    image, blue="B2", green="B3", red="B4", nir="B8", swir1="B11", swir2="B12"
):
    """Compute Tasseled Cap for Sentinel-2."""
    # Define an Array of Tasseled Cap coefficients.
    coefficients = ee.Array(
        [
            [0.3510, 0.3813, 0.3437, 0.7196, 0.2396, 0.1949],
            [-0.3599, -0.3533, -0.4734, 0.6633, 0.0087, -0.2856],
            [0.2578, 0.2305, 0.0883, 0.1071, -0.7611, -0.5308],
        ]
    )

    image = image.select([blue, green, red, nir, swir1, swir2])

    # Make an Array Image, with a 1-D Array per pixel.
    arrayImage1D = image.toArray()

    # Make an Array Image with a 2-D Array per pixel, 6x1.
    arrayImage2D = arrayImage1D.toArray(1)

    # Do a matrix multiplication: 6x6 times 6x1.
    componentsImage = ee.Image(coefficients).matrixMultiply(arrayImage2D)

    # Get rid of the extra dimensions.
    componentsImage = componentsImage.arrayProject([0]).arrayFlatten(
        [["brightness", "greenness", "wetness"]]
    )

    return componentsImage


REL = {"NDVI": ndvi, "EVI": evi, "NBR": nbr, "NBR2": nbr2, "NDFI": ndfi}
