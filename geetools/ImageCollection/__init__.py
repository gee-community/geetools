"""Toolbox for the ``ee.ImageCollection`` class."""
from __future__ import annotations

from typing import Optional, Union

import ee
import ee_extra

from geetools.accessors import geetools_accessor


@geetools_accessor(ee.ImageCollection)
class ImageCollection:
    """Toolbox for the ``ee.ImageCollection`` class."""

    def __init__(self, obj: ee.ImageCollection):
        """Instantiate the class."""
        self._obj = obj

    # -- ee-extra wrapper ------------------------------------------------------
    def maskClouds(
        self,
        method: str = "cloud_prob",
        prob: int = 60,
        maskCirrus: bool = True,
        maskShadows: bool = True,
        scaledImage: bool = False,
        dark: float = 0.15,
        cloudDist: int = 1000,
        buffer: int = 250,
        cdi: Optional[int] = None,
    ) -> ee.ImageCollection:
        """Masks clouds and shadows in each image of an ImageCollection (valid just for Surface Reflectance products).

        Parameters:
            self: ImageCollection to mask.
            method: Method used to mask clouds. This parameter is ignored for Landsat products.
                Available options:
                    - 'cloud_prob' : Use cloud probability.
                    - 'qa' : Use Quality Assessment band.
            prob: Cloud probability threshold. Valid just for method = 'cloud_prob'. This parameter is ignored for Landsat products.
            maskCirrus: Whether to mask cirrus clouds. Default to ``True``. Valid just for method = 'qa'. This parameter is ignored for Landsat products.
            maskShadows: Whether to mask cloud shadows. Default to ``True`` This parameter is ignored for Landsat products.
            scaledImage: Whether the pixel values are scaled to the range [0,1] (reflectance values). This parameter is ignored for Landsat products.
            dark: NIR threshold. NIR values below this threshold are potential cloud shadows. This parameter is ignored for Landsat products.
            cloudDist: Maximum distance in meters (m) to look for cloud shadows from cloud edges. This parameter is ignored for Landsat products.
            buffer: Distance in meters (m) to dilate cloud and cloud shadows objects. This parameter is ignored for Landsat products.
            cdi: Cloud Displacement Index threshold. Values below this threshold are considered potential clouds. A cdi = None means that the index is not used. This parameter is ignored for Landsat products.

        Returns:
            Cloud-shadow masked image.

        Notes:
            This method may mask water as well as clouds for the Sentinel-3 Radiance product.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()
                S2 = (
                    ee.ImageCollection('COPERNICUS/S2_SR')
                    .maskClouds(prob = 75,buffer = 300,cdi = -0.5)
                    .first()
                )

        """
        return ee_extra.QA.clouds.maskClouds(
            self._obj,
            method,
            prob,
            maskCirrus,
            maskShadows,
            scaledImage,
            dark,
            cloudDist,
            buffer,
            cdi,
        )

    def closest(
        self, date: Union[ee.Date, str], tolerance: int = 1, unit: str = "month"
    ) -> ee.ImageCollection:
        """Gets the closest image (or set of images if the collection intersects a region that requires multiple scenes) to the specified date.

        Parameters:
            date: Date of interest. The method will look for images closest to this date.
            tolerance: Filter the collection to [date - tolerance, date + tolerance) before searching the closest image. This speeds up the searching process for collections with a high temporal resolution.
            unit: Units for tolerance. Available units: 'year', 'month', 'week', 'day', 'hour', 'minute' or 'second'.

        Returns:
            Closest images to the specified date.

        Examples:
            .. jupyter-execute::

                import ee
                import geetools

                s2 = ee.ImageCollection('COPERNICUS/S2_SR').closest('2020-10-15')
                s2.size().getInfo()
        """
        return ee_extra.ImageCollection.core.closest(self._obj, date, tolerance, unit)

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
    ) -> ee.ImageCollection:
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
                image = image.geetools.specralIndices(["NDVI", "NDFI"])
        """
        # fmt: off
        return ee_extra.Spectral.core.spectralIndices(
            self._obj, index, G, C1, C2, L, cexp, nexp, alpha, slope, intercept, gamma, omega,
            beta, k, fdelta, kernel, sigma, p, c, lambdaN, lambdaR, lambdaG, online,
            drop=False,
        )
        # fmt: on

    def getScaleParams(self) -> dict:
        """Gets the scale parameters for each band of the image.

        Returns:
            Dictionary with the scale parameters for each band.


        Examples:
            .. jupyter-execute::

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('MODIS/006/MOD11A2').geetools.getScaleParams()
        """
        return ee_extra.STAC.core.getScaleParams(self._obj)

    def getOffsetParams(self) -> dict:
        """Gets the offset parameters for each band of the image.

        Returns:
            Dictionary with the offset parameters for each band.

        Examples:
            .. jupyter-execute::

            import ee
            import geetools

            ee.Initialize()

            ee.ImageCollection('MODIS/006/MOD11A2').getOffsetParams()
        """
        return ee_extra.STAC.core.getOffsetParams(self._obj)

    def scaleAndOffset(self) -> ee.ImageCollection:
        """Scales bands on an image according to their scale and offset parameters.

        Returns:
            Scaled image.

        Examples:
            .. jupyter_execute::

                import ee, geetools

                ee.Initialize()

                S2 = ee.ImageCollection('COPERNICUS/S2_SR').scaleAndOffset()
        """
        return ee_extra.STAC.core.scaleAndOffset(self._obj)

    def preprocess(self, **kwargs) -> ee.ImageCollection:
        """Pre-processes the image: masks clouds and shadows, and scales and offsets the image.

        Parameters:
            **kwargs: Keywords arguments for ``maskClouds`` method.

        Returns:
            Pre-processed image.

        Examples:
            .. jupyter-execute::

            import ee
            import geetools

            ee.Initialize()
            S2 = ee.ImageCollection('COPERNICUS/S2_SR').preprocess()
        """
        return ee_extra.QA.pipelines.preprocess(self._obj, **kwargs)

    def getSTAC(self) -> dict:
        """Gets the STAC of the image.

        Returns:
            STAC of the image.

        Examples:
            .. jupyter-execute::

            import ee
            import geetools

            ee.Initialize()

            ee.ImageCollection('COPERNICUS/S2_SR').getSTAC()
        """
        return ee_extra.STAC.core.getSTAC(self._obj)

    def getDOI(self) -> str:
        """Gets the DOI of the image, if available.

        Returns:
            DOI of the ee.Image dataset.

        Examples:
            .. jupyter-execute::

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').getDOI()
        """
        return ee_extra.STAC.core.getDOI(self._obj)

    def getCitation(self) -> str:
        """Gets the citation of the image, if available.

        Returns:
            Citation of the ee.Image dataset.

        Examples:
            .. jupyter-execute::

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').getCitation()
        """
        return ee_extra.STAC.core.getCitation(self._obj)

    def panSharpen(
        self, method: str = "SFIM", qa: str = "", **kwargs
    ) -> ee.ImageCollection:
        """Apply panchromatic sharpening to the ImageCollection images.

        Optionally, run quality assessments between the original and sharpened Image to
        measure spectral distortion and set results as properties of the sharpened Image.

        Parameters:
            method: The sharpening algorithm to apply. Current options are "SFIM" (Smoothing Filter-based Intensity Modulation), "HPFA" (High Pass Filter Addition), "PCS" (Principal Component Substitution), and "SM" (simple mean). Different sharpening methods will produce different quality sharpening results in different scenarios.
            qa: One or more optional quality assessment names to apply after sharpening. Results will be stored as image properties with the pattern `geetools:metric`, e.g. `geetools:RMSE`.
            **kwargs: Keyword arguments passed to ee.Image.reduceRegion() such as "geometry", "maxPixels", "bestEffort", etc. These arguments are only used for PCS sharpening and quality assessments.

        Returns:
            The ImageCollections with all sharpenable bands sharpened to the panchromatic resolution and quality assessments run and set as properties.

        Examples:
            .. jupyter-execute::

                import ee
                import geetools

                ee.Initialize()

                source = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_047027_20160819")
                sharp = source.panSharpen(method="HPFA", qa=["MSE", "RMSE"], maxPixels=1e13)
        """
        return ee_extra.Algorithms.core.panSharpen(
            img=self._obj, method=method, qa=qa or None, prefix="geetools", **kwargs
        )

    def tasseledCap(self) -> ee.ImageCollection:
        """Calculates tasseled cap brightness, wetness, and greenness components.

        Tasseled cap transformations are applied using coefficients published for these
        supported platforms:

        * Sentinel-2 MSI Level 1C
        * Landsat 9 OLI-2 SR
        * Landsat 9 OLI-2 TOA
        * Landsat 8 OLI SR
        * Landsat 8 OLI TOA
        * Landsat 7 ETM+ TOA
        * Landsat 5 TM Raw DN
        * Landsat 4 TM Raw DN
        * Landsat 4 TM Surface Reflectance
        * MODIS NBAR

        Parameters:
            self: ee.ImageCollection to calculate tasseled cap components for. Must belong to a supported platform.

        Returns:
            ImageCollections with the tasseled cap components as new bands.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR')
                img = img.tasseledCap()
        """
        return ee_extra.Spectral.core.tasseledCap(self._obj)
