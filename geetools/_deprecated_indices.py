# coding=utf-8
"""Legacy function to compute Spectral indices."""
from deprecated.sphinx import deprecated


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


@deprecated(version="1.0.0", reason="Use ee.Image.geetools.tasseledCap() instead")
def tasseled_cap_s2(image, *args, **kwargs):
    """Compute Tasseled Cap for Sentinel-2."""
    return image.geetools.tasseledCap()
