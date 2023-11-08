"""Methods to compute the spectral indices for the Image class."""
from __future__ import annotations

from typing import Union

import ee_extra


def index_list(cls) -> dict:
    """Return the list of indices implemented in this module.

    Returns:
        List of indices implemented in this module

    Examples:
        .. jupyter-execute::

            import ee, geetools

            ind = ee.Image.geetools.indices()["BAIS2"]
            print(ind["long_name"])
            print(ind["formula"])
            print(ind["reference"])
    """
    return ee_extra.Spectral.core.indices()


def spectralIndices(
    self,
    index: str = "NDVI",
    G: Union[float, int] = 2.5,
    C1: Union[float, int] = 6.0,
    C2: Union[float, int] = 7.5,
    L: Union[float, int] = 1.0,
    cexp: Union[float, int] = 1.16,
    nexp: Union[float, int] = 2.0,
    alpha: Union[float, int] = 0.1,
    slope: Union[float, int] = 1.0,
    intercept: Union[float, int] = 0.0,
    gamma: Union[float, int] = 1.0,
    omega: Union[float, int] = 2.0,
    beta: Union[float, int] = 0.05,
    k: Union[float, int] = 0.0,
    fdelta: Union[float, int] = 0.581,
    kernel: str = "RBF",
    sigma: str = "0.5 * (a + b)",
    p: Union[float, int] = 2.0,
    c: Union[float, int] = 1.0,
    lambdaN: Union[float, int] = 858.5,
    lambdaR: Union[float, int] = 645.0,
    lambdaG: Union[float, int] = 555.0,
    online: Union[float, int] = False,
):
    """Computes one or more spectral indices (indices are added as bands) for an image from the Awesome List of Spectral Indices.

    Parameters:
        self: Image to compute indices on. Must be scaled to [0,1].
        index: Index or list of indices to compute, default = 'NDVI'
            Available options:
                - 'vegetation' : Compute all vegetation indices.
                - 'burn' : Compute all burn indices.
                - 'water' : Compute all water indices.
                - 'snow' : Compute all snow indices.
                - 'urban' : Compute all urban (built-up) indices.
                - 'kernel' : Compute all kernel indices.
                - 'all' : Compute all indices listed below.
                - Awesome Spectral Indices for GEE: Check the complete list of indices `here <https://awesome-ee-spectral-indices.readthedocs.io/en/latest/list.html>`_.
        G: Gain factor. Used just for index = 'EVI', default = 2.5
        C1: Coefficient 1 for the aerosol resistance term. Used just for index = 'EVI', default = 6.0
        C2: Coefficient 2 for the aerosol resistance term. Used just for index = 'EVI', default = 7.5
        L: Canopy background adjustment. Used just for index = ['EVI','SAVI'], default = 1.0
        cexp: Exponent used for OCVI, default = 1.16
        nexp: Exponent used for GDVI, default = 2.0
        alpha: Weighting coefficient used for WDRVI, default = 0.1
        slope: Soil line slope, default = 1.0
        intercept: Soil line intercept, default = 0.0
        gamma: Weighting coefficient used for ARVI, default = 1.0
        omega: Weighting coefficient  used for MBWI, default = 2.0
        beta: Calibration parameter used for NDSIns, default = 0.05
        k: Slope parameter by soil used for NIRvH2, default = 0.0
        fdelta: Adjustment factor used for SEVI, default = 0.581
        kernel: Kernel used for kernel indices, default = 'RBF'
            Available options:
                - 'linear' : Linear Kernel.
                - 'RBF' : Radial Basis Function (RBF) Kernel.
                - 'poly' : Polynomial Kernel.
        sigma: Length-scale parameter. Used for kernel = 'RBF', default = '0.5 * (a + b)'. If str, this must be an expression including 'a' and 'b'. If numeric, this must be positive.
        p: Kernel degree. Used for kernel = 'poly', default = 2.0
        c: Free parameter that trades off the influence of higher-order versus lower-order terms in the polynomial kernel. Used for kernel = 'poly', default = 1.0. This must be greater than or equal to 0.
        lambdaN: NIR wavelength used for NIRvH2 and NDGI, default = 858.5
        lambdaR: Red wavelength used for NIRvH2 and NDGI, default = 645.0
        lambdaG: Green wavelength used for NDGI, default = 555.0
        drop: Whether to drop all bands except the new spectral indices, default = False

    Returns:
        Image with the computed spectral index, or indices, as new bands.

    Examples:
        .. jupyter-execute::

            import ee, geetools

            ee.Initialize()
            image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
            image = image.specralIndices(["NDVI", "NDFI"])
    """
    # fmt: off
    return ee_extra.Spectral.core.spectralIndices(
        self._obj, index, G, C1, C2, L, cexp, nexp, alpha, slope, intercept, gamma, omega,
        beta, k, fdelta, kernel, sigma, p, c, lambdaN, lambdaR, lambdaG, online,
        drop=False,
    )
    # fmt: on
