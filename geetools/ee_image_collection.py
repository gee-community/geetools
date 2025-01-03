"""Toolbox for the :py:class:`ee.ImageCollection` class."""
from __future__ import annotations

import uuid
from datetime import datetime as dt
from typing import Any, Iterable

import ee
import ee_extra
import requests
import xarray
from ee import apifunction
from matplotlib.axes import Axes
from xarray import Dataset
from xee.ext import REQUEST_BYTE_LIMIT

from .accessors import register_class_accessor
from .utils import plot_data

PY_DATE_FORMAT = "%Y-%m-%dT%H-%M-%S"
"The python format to use to parse dates coming from GEE."

EE_DATE_FORMAT = "YYYY-MM-dd'T'HH-mm-ss"
"The javascript format to use to burn date object in GEE."


@register_class_accessor(ee.ImageCollection, "geetools")
class ImageCollectionAccessor:
    """Toolbox for the :py:class:`ee.ImageCollection` class."""

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
        cdi: int | None = None,
    ) -> ee.ImageCollection:
        """Masks clouds and shadows in each image of an :py:class:`ee.ImageCollection` (valid just for Surface Reflectance products).

        Parameters:
            self: :py:class:`ee.ImageCollection` to mask.
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
            .. code-block:: python

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
        self, date: ee.Date | str, tolerance: int = 1, unit: str = "month"
    ) -> ee.ImageCollection:
        """Gets the closest image (or set of images if the collection intersects a region that requires multiple scenes) to the specified date.

        Parameters:
            self: :py:class:`ee.ImageCollection` from which to get the closest image to the specified date.
            date: Date of interest. The method will look for images closest to this date.
            tolerance: Filter the collection to [date - tolerance, date + tolerance) before searching the closest image. This speeds up the searching process for collections with a high temporal resolution.
            unit: Units for tolerance. Available units: ``year``, ``month``, ``week``, ``day``, ``hour``, ``minute`` or ``second``.

        Returns:
            Closest images to the specified date.

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()
                geom = ee.Geometry.point(-122.196, 41.411)
                s2 = (
                    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                    .filterBounds(geom)
                    .geetools.closest('2020-10-15')
                )
                s2.size().getInfo()
        """
        return ee_extra.ImageCollection.core.closest(self._obj, date, tolerance, unit)

    def spectralIndices(
        self,
        index: str = "NDVI",
        G: float | int = 2.5,
        C1: float | int = 6.0,
        C2: float | int = 7.5,
        L: float | int = 1.0,
        cexp: float | int = 1.16,
        nexp: float | int = 2.0,
        alpha: float | int = 0.1,
        slope: float | int = 1.0,
        intercept: float | int = 0.0,
        gamma: float | int = 1.0,
        omega: float | int = 2.0,
        beta: float | int = 0.05,
        k: float | int = 0.0,
        fdelta: float | int = 0.581,
        kernel: str = "RBF",
        sigma: str = "0.5 * (a + b)",
        p: float | int = 2.0,
        c: float | int = 1.0,
        lambdaN: float | int = 858.5,
        lambdaR: float | int = 645.0,
        lambdaG: float | int = 555.0,
        online: bool = False,
    ) -> ee.ImageCollection:
        """Computes one or more spectral indices (indices are added as bands) for an image collection from the Awesome List of Spectral Indices.

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
            omega: Weighting coefficient used for MBWI, default = 2.0
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
            Image collection with the computed spectral index, or indices, as new bands.

        See Also:
            - :docstring:`ee.Image.geetools.scaleAndOffset`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()
                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                image = image.geetools.spectralIndices(["NDVI", "NDFI"])
        """
        # fmt: off
        return ee_extra.Spectral.core.spectralIndices(
            self._obj, index, G, C1, C2, L, cexp, nexp, alpha, slope, intercept, gamma, omega,
            beta, k, fdelta, kernel, sigma, p, c, lambdaN, lambdaR, lambdaG, online,
            drop=False,
        )
        # fmt: on

    def getScaleParams(self) -> dict[str, float]:
        """Gets the scale parameters for each band of the image.

        Returns:
            Dictionary with the scale parameters for each band.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.getOffsetParams`
            - :docstring:`ee.ImageCollection.geetools.scaleAndOffset`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('MODIS/006/MOD11A2').geetools.getScaleParams()
        """
        return ee_extra.STAC.core.getScaleParams(self._obj)

    def getOffsetParams(self) -> dict[str, float]:
        """Gets the offset parameters for each band of the image.

        Returns:
            Dictionary with the offset parameters for each band.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.getScaleParams`
            - :docstring:`ee.ImageCollection.geetools.scaleAndOffset`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('MODIS/006/MOD11A2').geetools.getOffsetParams()
        """
        return ee_extra.STAC.core.getOffsetParams(self._obj)

    def scaleAndOffset(self) -> ee.ImageCollection:
        """Scales bands on an image according to their scale and offset parameters.

        Returns:
            Scaled image.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.getOffsetParams`
            - :docstring:`ee.ImageCollection.geetools.getScaleParams`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                S2 = ee.ImageCollection('COPERNICUS/S2_SR').scaleAndOffset()
        """
        return ee_extra.STAC.core.scaleAndOffset(self._obj)

    def preprocess(self, **kwargs) -> ee.ImageCollection:
        """Pre-processes the image: masks clouds and shadows, and scales and offsets the image collection.

        Parameters:
            **kwargs: Keywords arguments for :py:meth:`ee.ImageCollection.geetools.maskClouds <geetools.ee_image_collection.ImageCollectionAccessor.maskClouds>` method.

        Returns:
            Pre-processed image.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.getScaleParams`
            - :docstring:`ee.ImageCollection.geetools.getOffsetParams`
            - :docstring:`ee.ImageCollection.geetools.scaleAndOffset`
            - :docstring:`ee.ImageCollection.geetools.maskClouds`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()
                S2 = ee.ImageCollection('COPERNICUS/S2_SR').preprocess()
        """
        return ee_extra.QA.pipelines.preprocess(self._obj, **kwargs)

    def getSTAC(self) -> dict[str, Any]:
        """Gets the STAC of the image collection.

        Returns:
            STAC of the image collection.

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('COPERNICUS/S2_SR').geetools.getSTAC()
        """
        # extract the Asset id from the imagecollection
        assetId = self._obj.get("system:id").getInfo()

        # search for the project in the GEE catalog and extract the project catalog URL
        project = assetId.split("/")[0]
        catalog = "https://earthengine-stac.storage.googleapis.com/catalog/catalog.json"
        links = requests.get(catalog).json()["links"]
        project_catalog = next((i["href"] for i in links if i.get("title") == project), None)
        if project_catalog is None:
            raise ValueError(f"Project {project} not found in the catalog")

        # search for the collection in the project catalog and extract the collection STAC URL
        collection = "_".join(assetId.split("/"))
        links = requests.get(project_catalog).json()["links"]
        collection_stac = next((i["href"] for i in links if i.get("title") == collection), None)
        if collection_stac is None:
            raise ValueError(f"Collection {collection} not found in the {project} catalog")

        return requests.get(collection_stac).json()

    def getDOI(self) -> str:
        """Gets the DOI of the collection, if available.

        Returns:
            DOI of the :py:class:`ee.Image` dataset.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.getCitation`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').geetools.getDOI()
        """
        return ee_extra.STAC.core.getDOI(self._obj)

    def getCitation(self) -> str:
        """Gets the citation of the image, if available.

        Returns:
            Citation of the :py:class:`ee.Image` dataset.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.getDOI`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').geetools.getCitation()
        """
        return ee_extra.STAC.core.getCitation(self._obj)

    def panSharpen(self, method: str = "SFIM", qa: str = "", **kwargs) -> ee.ImageCollection:
        """Apply panchromatic sharpening to the :py:class:`ee.ImageCollection` images.

        Optionally, run quality assessments between the original and sharpened Image to
        measure spectral distortion and set results as properties of the sharpened Image.

        Parameters:
            method: The sharpening algorithm to apply. Current options are "SFIM" (Smoothing Filter-based Intensity Modulation), "HPFA" (High Pass Filter Addition), "PCS" (Principal Component Substitution), and "SM" (simple mean). Different sharpening methods will produce different quality sharpening results in different scenarios.
            qa: One or more optional quality assessment names to apply after sharpening. Results will be stored as image properties with the pattern `geetools:metric`, e.g. `geetools:RMSE`.
            **kwargs: Keyword arguments passed to ee.Image.reduceRegion() such as "geometry", "maxPixels", "bestEffort", etc. These arguments are only used for PCS sharpening and quality assessments.

        Returns:
            The ImageCollections with all sharpenable bands sharpened to the panchromatic resolution and quality assessments run and set as properties.

        Examples:
            .. code-block:: python

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
        """Calculates tasseled cap brightness, wetness, and greenness components for all images in the collection.

        Tasseled cap transformations are applied using coefficients published for these
        supported platforms:

        * Sentinel-2 MSI Level 1C [1]_
        * Landsat 9 OLI-2 SR [2]_
        * Landsat 9 OLI-2 TOA [2]_
        * Landsat 8 OLI SR [2]_
        * Landsat 8 OLI TOA [2]_
        * Landsat 7 ETM+ TOA [3]_
        * Landsat 5 TM Raw DN [4]_
        * Landsat 4 TM Raw DN [5]_
        * Landsat 4 TM Surface Reflectance [6]_
        * MODIS NBAR [7]_

        Parameters:
            self: :py:class:`ee.ImageCollection` to calculate tasseled cap components for. Must belong to a supported platform.

        Returns:
            Image Collections with the tasseled cap components as new bands.

        References:
            .. [1] Shi, T., & Xu, H. (2019). Derivation of Tasseled Cap Transformation
                Coefficients for Sentinel-2 MSI At-Sensor Reflectance Data. IEEE Journal
                of Selected Topics in Applied Earth Observations and Remote Sensing, 1-11.
                doi:10.1109/jstars.2019.2938388
            .. [2] Zhai, Y., Roy, D.P., Martins, V.S., Zhang, H.K., Yan, L., Li, Z. 2022.
                Conterminous United States Landsat-8 top of atmosphere and surface reflectance
                tasseled cap transformation coefficients. Remote Sensing of Environment,
                274(2022). doi:10.1016/j.rse.2022.112992
            .. [3] Huang, C., Wylie, B., Yang, L., Homer, C. and Zylstra, G., 2002.
                Derivation of a tasselled cap transformation based on Landsat 7 at-satellite
                reflectance. International journal of remote sensing, 23(8), pp.1741-1748.
            .. [4] Crist, E.P., Laurin, R. and Cicone, R.C., 1986, September. Vegetation and
                soils information contained in transformed Thematic Mapper data. In
                Proceedings of IGARSS`86 symposium (pp. 1465-1470). Paris: European Space
                Agency Publications Division.
            .. [5] Crist, E.P. and Cicone, R.C., 1984. A physically-based transformation of
                Thematic Mapper data---The TM Tasseled Cap. IEEE Transactions on Geoscience
                and Remote sensing, (3), pp.256-263.
            .. [6] Crist, E.P., 1985. A TM tasseled cap equivalent transformation for
                reflectance factor data. Remote sensing of Environment, 17(3), pp.301-306.
            .. [7] Lobser, S.E. and Cohen, W.B., 2007. MODIS tasselled cap: land cover
                characteristics expressed through transformed MODIS data. International
                Journal of Remote Sensing, 28(22), pp.5079-5101.


        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ic = ee.ImageCollection("LANDSAT/LT05/C01/T1")
                ic = ic.geetools.tasseledCap()
        """
        return ee_extra.Spectral.core.tasseledCap(self._obj)

    def append(self, image: ee.Image) -> ee.ImageCollection:
        """Append an image to the existing image collection.

        Args:
            image: Image to append to the collection.

        Returns:
            :py:class:`ee.ImageCollection` with the new image appended.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ic = ee.ImageCollection('COPERNICUS/S2_SR');

                geom = ee.Geometry.Point(-122.196, 41.411);
                ic2018 = ic.filterBounds(geom).filterDate('2019-07-01', '2019-10-01')
                ic2021 = ic.filterBounds(geom).filterDate('2021-07-01', '2021-10-01')

                ic = ic2018.geetools.append(ic2021.first())
                ic.getInfo()
        """
        return self._obj.merge(ee.ImageCollection([image]))

    def collectionMask(self) -> ee.Image:
        """A binary :py:class:`ee.Image` where only pixels that are masked in all images of the collection get masked.

        Returns:
            :py:class:`ee.Image` of the mask. 1 where at least 1 pixel is valid 0 elsewhere

        Examples:
            .. code-block::

                import ee, geetools

                ee.Initialize()

                ic = ee.ImageCollection('COPERNICUS/S2_SR');

                geom = ee.Geometry.Point(-122.196, 41.411);
                ic2018 = ic.filterBounds(geom).filterDate('2019-07-01', '2019-10-01')
                ic = ic2018.geetools.collectionMask()
                ic.getInfo()
        """
        masks = self._obj.map(lambda i: i.mask())
        return ee.Image(masks.sum().gt(0))

    def iloc(self, index: int) -> ee.Image:
        """Get Image from the :py:class:`ee.ImageCollection` by index.

        Args:
            index: Index of the image to get.

        Returns:
            :py:class:`ee.Image` at the specified index.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ic = ee.ImageCollection('COPERNICUS/S2_SR');

                geom = ee.Geometry.Point(-122.196, 41.411);
                ic2018 = ic.filterBounds(geom).filterDate('2019-07-01', '2019-10-01')
                ic2018.geetools.iloc(0).getInfo()
        """
        return ee.Image(self._obj.toList(self._obj.size()).get(index))

    def integral(self, band: str, time: str = "system:time_start", unit: str = "") -> ee.Image:
        """Compute the integral of a band over time or a specified property.

        Args:
            band: the name of the band to integrate.
            time: the name of the property to use as time. It must be a date property of the images.
            unit: the time unit use to compute the integral. It can be one of the following: ``year``, ``month``, ``day``, ``hour``, ``minute``, ``second``. If non is set, the time will be normalized on the integral length.

        Returns:
            An :py:class:`ee.Image` object with the integrated band for each pixel.

        Examples:
            .. code-block:: python

                import ee, geetools

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                integral = collection.geetools.integral("B1")
                print(integral.getInfo())
        """
        # compute the intervals along the x axis
        # the GEE time is stored as a milliseconds timestamp. If the time unit is not set,
        # the integral is normalized on the total time length of the time series
        minTime = self._obj.aggregate_min(time)
        maxTime = self._obj.aggregate_max(time)
        intervals = {
            "year": ee.Number(1000 * 60 * 60 * 24 * 365),  # 1 year in milliseconds
            "month": ee.Number(1000 * 60 * 60 * 24 * 30),  # 1 month in milliseconds
            "day": ee.Number(1000 * 60 * 60 * 24),  # 1 day in milliseconds
            "hour": ee.Number(1000 * 60 * 60),  # 1 hour in milliseconds
            "minute": ee.Number(1000 * 60),  # 1 minute in milliseconds
            "second": ee.Number(1000),  # 1 second in milliseconds
            "": ee.Number(maxTime).subtract(ee.Number(minTime)),
        }
        interval = intervals[unit]

        # initialize the sum with a 0 value initial item
        # all the properties of the first image of the collection are copied
        first = self._obj.first()
        zero = ee.Image.constant(0).copyProperties(first, first.propertyNames())
        s = ee.Image(zero).rename("integral").set("last", zero)

        # compute the approximation of the integral using the trapezoidal method
        # each local interval is aproximated by the corresponding trapez and the
        # sum is updated
        def computeIntegral(image, integral):
            image = ee.Image(image).select(band)
            integral = ee.Image(integral)
            last = ee.Image(integral.get("last"))
            locMinTime = ee.Number(last.get(time))
            locMaxTime = ee.Number(image.get(time))
            locInterval = locMaxTime.subtract(locMinTime).divide(interval)
            locIntegral = last.add(image).multiply(locInterval).divide(2)
            return integral.add(locIntegral).set("last", image)

        return ee.Image(self._obj.iterate(computeIntegral, s))

    def outliers(
        self, bands: list | ee.List = [], sigma: float | int | ee.Number = 2, drop: bool = False
    ) -> ee.ImageCollection:
        """Compute the outlier for each pixel in the specified bands.

        A pixel is considered as an outlier if:

        .. code-block::

            outlier = value > mean+(sigma*stddev)
            outlier = value < mean-(sigma*stddev)

        In a 1D example it would be:
            - values = [1, 5, 6, 4, 7, 10]
            - mean = 5.5
            - std dev = 3
            - mean + (sigma*stddev) = 8.5
            - mean - (sigma*stddev) = 2.5
            - outliers = values between 2.5 and 8.5 = [1, 10]

        Here in this function an extra band is added to each image for each of the evaluated bands with the outlier status. The band name is the original band name with the suffix "_outlier". A value of 1 means that the pixel is an outlier, 0 means that it is not.

        Optionally users can discard this band by setting ``drop`` to ``True`` and the outlier will simply be masked from each image. This is useful when the outlier band is not needed and the user wants to save space.

        idea from: https://www.kdnuggets.com/2017/02/removing-outliers-standard-deviation-python.html

        Args:
            bands: The bands to evaluate for outliers. If empty, all bands are evaluated.
            sigma: The number of standard deviations to use to compute the outlier.
            drop: Whether to drop the outlier band from the images.

        Returns:
            A :py:class:`ee.ImageCollection` with the outlier band added to each image or masked if ``drop`` is ``True``.

        Examples:
            .. code-block:: python

                import ee, geetools

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                outliers = collection.geetools.outliers(["B1", "B2"], 2)
                print(outliers.getInfo())
        """
        # cast parameters and compute the outlier band names
        initBands = self._obj.first().bandNames()
        statBands = ee.List(bands) if bands else initBands
        outBands = statBands.map(lambda b: ee.String(b).cat("_outlier"))

        # compute the mean and std dev for each band
        statCollection = self._obj.select(statBands)
        mean = statCollection.mean()
        stdDev = statCollection.reduce(ee.Reducer.stdDev())
        minValues = mean.subtract(stdDev.multiply(sigma))
        maxValues = mean.add(stdDev.multiply(sigma))

        # compute the outlier band for each image
        def computeOutlierBands(i):
            outImage = i.select(statBands)
            outImage = outImage.gt(maxValues).Or(outImage.lt(minValues))
            return i.addBands(outImage.rename(outBands))

        ic = self._obj.map(computeOutlierBands)

        # drop the outlier band and mask each image if requested
        def maskOutliers(i):
            maskedBands = i.select(statBands).updateMask(i.select(outBands).Not())
            return i.addBands(maskedBands, overwrite=True).select(initBands)

        ic = ic if drop is False else ic.map(maskOutliers)

        return ee.ImageCollection(ic)

    def to_xarray(
        self,
        drop_variables: str | Iterable[str] | None = None,
        io_chunks: object = None,
        n_images: int = -1,
        mask_and_scale: bool = True,
        decode_times: bool = True,
        decode_timedelta: bool | None = None,
        use_cftime: bool | None = None,
        concat_characters: bool = True,
        decode_coords: bool = True,
        crs: str | None = None,
        scale: float | int | None = None,
        projection: ee.Projection | None = None,
        geometry: ee.Geometry | None = None,
        primary_dim_name: str | None = None,
        primary_dim_property: str | None = None,
        ee_mask_value: float | None = None,
        request_byte_limit: int = REQUEST_BYTE_LIMIT,
    ) -> Dataset:
        """Open an Earth Engine :py:class:`ee.ImageCollection` as an ``xarray.Dataset``.

        Args:
            drop_variables: Variables or bands to drop before opening.
            io_chunks: Specifies the chunking strategy for loading data from EE. By default, this automatically calculates optional chunks based on the ``request_byte_limit``.
            n_images: The max number of EE images in the collection to open. Useful when there are a large number of images in the collection since calculating collection size can be slow. -1 indicates that all images should be included.
            mask_and_scale: Lazily scale (using scale_factor and add_offset) and mask (using _FillValue).
            decode_times: Decode cf times (e.g., integers since "hours since 2000-01-01") to np.datetime64.
            decode_timedelta: If True, decode variables and coordinates with time units in {"days", "hours", "minutes", "seconds", "milliseconds", "microseconds"} into timedelta objects. If False, leave them encoded as numbers. If None (default), assume the same value of decode_time.
            use_cftime: Only relevant if encoded dates come from a standard calendar (e.g. "gregorian", "proleptic_gregorian", "standard", or not specified).  If None (default), attempt to decode times to ``np.datetime64[ns]`` objects; if this is not possible, decode times to ``cftime.datetime`` objects. If True, always decode times to ``cftime.datetime`` objects, regardless of whether or not they can be represented using ``np.datetime64[ns]`` objects.  If False, always decode times to ``np.datetime64[ns]`` objects; if this is not possible raise an error.
            concat_characters: Should character arrays be concatenated to strings, for example: ["h", "e", "l", "l", "o"] -> "hello"
            decode_coords: bool or {"coordinates", "all"}, Controls which variables are set as coordinate variables: - "coordinates" or True: Set variables referred to in the ``'coordinates'`` attribute of the datasets or individual variables as coordinate variables. - "all": Set variables referred to in ``'grid_mapping'``, ``'bounds'`` and other attributes as coordinate variables.
            crs: The coordinate reference system (a CRS code or WKT string). This defines the frame of reference to coalesce all variables upon opening. By default, data is opened with 'EPSG:4326'.
            scale: The scale in the ``crs`` or ``projection``'s units of measure -- either meters or degrees. This defines the scale that all data is represented in upon opening. By default, the scale is 1° when the CRS is in degrees or 10,000 when in meters.
            projection: Specify an ``ee.Projection`` object to define the ``scale`` and ``crs`` (or other coordinate reference system) with which to coalesce all variables upon opening. By default, the scale and reference system is set by the ``crs`` and ``scale`` arguments.
            geometry: Specify an ``ee.Geometry`` to define the regional bounds when opening the data. When not set, the bounds are defined by the CRS's ``area_of_use`` boundaries. If those aren't present, the bounds are derived from the geometry of the first image of the collection.
            primary_dim_name: Override the name of the primary dimension of the output Dataset. By default, the name is 'time'.
            primary_dim_property: Override the ``ee.Image`` property for which to derive the values of the primary dimension. By default, this is 'system:time_start'.
            ee_mask_value: Value to mask to EE nodata values. By default, this is 'np.iinfo(np.int32).max' i.e. 2147483647.
            request_byte_limit: the max allowed bytes to request at a time from Earth Engine. By default, it is 48MBs.

        Returns:
            An ``xarray.Dataset`` that streams in remote data from Earth Engine.
        """
        return xarray.open_dataset(
            self._obj,
            engine="ee",
            drop_variables=drop_variables,
            io_chunks=io_chunks,
            n_images=n_images,
            mask_and_scale=mask_and_scale,
            decode_times=decode_times,
            decode_timedelta=decode_timedelta,
            use_cftime=use_cftime,
            concat_characters=concat_characters,
            decode_coords=decode_coords,
            crs=crs,
            scale=scale,
            projection=projection,
            geometry=geometry,
            primary_dim_name=primary_dim_name,
            primary_dim_property=primary_dim_property,
            ee_mask_value=ee_mask_value,
            request_byte_limit=request_byte_limit,
        )

    def validPixel(self, band: str | ee.String = "") -> ee.Image:
        """Compute the number of valid pixels in the specified band.

        Compute the number of valid pixels in the specified band. 2 bands will be created:
        one with the number of valid pixels (``valid``) and another with the percentage of valid pixels (``pct_valid``).

        Args:
            band: the band to evaluate for valid pixels. If empty, use the first band.

        Returns:
            An Image with the number of valid pixels or the percentage of valid pixels.

        Examples:
            .. code-block:: python

                import ee, geetools
                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )
                valid = collection.geetools.validPixels("B1")
                print(valid.getInfo())
        """
        # compute the mask for the specified band
        band = self._obj.first().bandNames().get(0) if band == "" else ee.String(band)
        masks = self._obj.select([band]).map(lambda i: i.mask().eq(1))
        validPixel = masks.sum().rename("valid").clip(self._obj.geometry())
        validPct = validPixel.divide(self._obj.size()).multiply(100).rename("pct_valid")
        return validPixel.addBands(validPct)

    def containsBandNames(self, bandNames: list | ee.List, filter: str) -> ee.ImageCollection:
        """Filter the :py:class:`ee.ImageCollection` by band names using the provided filter.

        Args:
            bandNames: list of band names to filter
            filter: type of filter to apply. To keep images that contains all the specified bands use ``"ALL"``. To get the images including at least one of the specified band use ``"ANY"``.

        Returns:
            A filtered :py:class:`ee.ImageCollection`

        Examples:
            .. code-block:: python

                import ee, geetools

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                filtered = collection.geetools.containsBandNames(["B1", "B2"], "ALL")
                print(filtered.getInfo())
        """
        # cast parameters
        filter = {"ALL": "Filter.and", "ANY": "Filter.or"}[filter]
        bandNames = ee.List(bandNames)

        # add bands as metadata in a temporary property
        band_name = uuid.uuid4().hex
        ic = self._obj.map(lambda i: i.set(band_name, i.bandNames()))

        # create a filter by combining a listContain filter over all the band names from the
        # user list. Combine them with a "Or" to get a "any" filter and "And" to get a "all".
        # We use a workaround until this is solved: https://issuetracker.google.com/issues/322838709
        filterList = bandNames.map(lambda b: ee.Filter.listContains(band_name, b))
        filterCombination = apifunction.ApiFunction.call_(filter, ee.List(filterList))

        # apply this filter and remove the temporary property. Exclude parameter is additive so
        # we do a blank multiplication to remove all the properties beforhand
        ic = ee.ImageCollection(ic.filter(filterCombination))
        ic = ic.map(lambda i: ee.Image(i.multiply(1).copyProperties(i, exclude=[band_name])))

        return ee.ImageCollection(ic)

    def containsAllBands(self, bandNames: list | ee.List) -> ee.ImageCollection:
        """Filter the :py:class:`ee.ImageCollection` keeping only the images with all the provided bands.

        Args:
            bandNames: list of band names to filter

        Returns:
            A filtered :py:class:`ee.ImageCollection`

        Examples:
            .. code-block::

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                filtered = collection.geetools.containsAllBands(["B1", "B2"])
                print(filtered.getInfo())
        """
        return self.containsBandNames(bandNames, "ALL")

    def containsAnyBands(self, bandNames: list | ee.List) -> ee.ImageCollection:
        """Filter the :py:class:`ee.ImageCollection` keeping only the images with any of the provided bands.

        Args:
            bandNames: list of band names to filter

        Returns:
            A filtered :py:class:`ee.ImageCollection`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                filtered = collection.geetools.containsAnyBands(["B1", "B2"])
                print(filtered.getInfo())
        """
        return self.containsBandNames(bandNames, "ANY")

    def aggregateArray(self, properties: list | ee.List | None = None) -> ee.Dictionary:
        """Aggregate the :py:class:`ee.ImageCollection` selected properties into a dictionary.

        Args:
            properties: list of properties to aggregate. If None, all properties are aggregated.

        Returns:
            A dictionary with the properties as keys and the aggregated values as values.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                aggregated = collection.geetools.aggregateArray(["CLOUD_COVER", "system:time_start"])
                print(aggregated.getInfo())
        """
        keys = ee.List(properties) if properties is not None else self._obj.first().propertyNames()
        values = keys.map(lambda p: self._obj.aggregate_array(p))
        return ee.Dictionary.fromLists(keys, values)

    def groupInterval(self, unit: str = "month", duration: int = 1) -> ee.List:
        """Transform the :py:class:`ee.ImageCollection` into a list of smaller collection of the specified duration.

        For example using unit as "month" and duration as 1, the :py:class:`ee.ImageCollection` will be transformed
        into a list of :py:class:`ee.ImageCollection` with each :py:class:`ee.ImageCollection` containing images for each month.
        Make sure the collection is filtered beforehand to reduce the number of images that needs to be
        processed.

        Args:
            unit: The unit of time to split the collection. Available units: ``year``, ``month``, ``week``, ``day``, ``hour``, ``minute`` or ``second``.
            duration: The duration of each split.

        Returns:
            A list of :py:class:`ee.ImageCollection` grouped by interval

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                split = collection.geetools.groupInterval("month", 1)
                print(split.getInfo())
        """
        sizeName = "__geetools_generated_size__"  # set generated properties name

        # as everything is relyin on the "system:time_start" property
        # we sort the image collection in the first place. In most collection it will change nothing
        # so free of charge unless for plumbing
        ic = self._obj.sort("system:time_start")
        toCopy = ic.first().propertyNames()

        # transform the interval into a duration in milliseconds
        # I can use the DateRangeAccessor as it's imported earlier in the __init__.py file
        # I don't know if it should be properly imported here, let's see with user feedback
        timeList = ic.aggregate_array("system:time_start")
        start, end = timeList.get(0), timeList.get(-1)
        DateRangeList = ee.DateRange(start, end).geetools.split(duration, unit)
        imageCollectionList = DateRangeList.map(
            lambda dr: ic.filterDate(ee.DateRange(dr).start(), ee.DateRange(dr).end())
        )

        def add_size(ic):
            ic = ee.ImageCollection(ic)
            return ic.set({sizeName: ic.size()})

        def delete_size_property(ic):
            ic = ee.ImageCollection(ic)
            return ee.ImageCollection(ic.copyProperties(ic, properties=toCopy))

        imageCollectionList = (
            imageCollectionList.map(add_size)
            .filter(ee.Filter.gt(sizeName, 0))
            .map(delete_size_property)
        )

        return ee.List(imageCollectionList)

    def reduceInterval(
        self,
        reducer: str | ee.Reducer = "mean",
        unit: str = "month",
        duration: int = 1,
    ) -> ee.ImageCollection:
        """Reduce the images included in the same duration interval using the provided reducer.

        For example using unit as "month" and duration as 1, the :py:class:`ee.ImageCollection` will be reduced
        into a new :py:class:`ee.ImageCollection` with each image containing the reduced values for each month.
        Make sure the collection is filtered beforehand to reduce the number of images that needs to be
        processed.

        Args:
            reducer: The name of the reducer to use or a Reducer object. Default is ``"mean"``.
            unit: The unit of time to split the collection. Available units: ``year``, ``month``, ``week``, ``day``, ``hour``, ``minute`` or ``second``.
            duration: The duration of each split.

        Returns:
            A new :py:class:`ee.ImageCollection` with the reduced images.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                reduced = collection.geetools.reduceInterval("mean", "month", 1)
                print(reduced.getInfo())
        """
        # create a list of image collections to be reduced
        # Every subcollection is sorted in case one use the "first" reducer
        imageCollectionList = self.groupInterval(unit, duration)

        # create a reducer from user parameters
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer

        def reduce(ic):
            ic = ee.ImageCollection(ic)
            timeList = ic.aggregate_array("system:time_start")
            start, end = timeList.get(0), timeList.get(-1)
            firstImg = ic.first()
            bandNames = firstImg.bandNames()
            propertyNames = firstImg.propertyNames()
            image = ic.reduce(red).rename(bandNames).copyProperties(firstImg, propertyNames)
            return image.set("system:time_start", start, "system:time_end", end)

        reducedImagesList = imageCollectionList.map(reduce)

        # set back the original properties
        propertyNames = self._obj.propertyNames()
        ic = ee.ImageCollection(reducedImagesList).copyProperties(self._obj, propertyNames)

        return ee.ImageCollection(ic)

    def closestDate(self) -> ee.ImageCollection:
        """Fill masked pixels with the first valid pixel in the stack of images.

        The method will for every image, fill all the pixels with the latest nono masked pixel in the stack of images.
        It requires the image to have a valid ``"system:time_start"`` property.
        As the imageCollection will need to be sorted limit the analysis to a reasonable number of image by filtering your data beforehand.

        Returns:
            An :py:class:`ee.ImageCollection` with all pixels unmasked in every image.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                filled = collection.geetools.fillWithFirst()
                print(filled.getInfo())
        """
        # retrieve all the time starts as an ordered list to iterate
        timeList = self._obj.aggregate_array("system:time_start").sort()

        # for each time start find all the images thata are before and use the mosaic reducer
        # to only keep the first one with a non masked pixel
        def fill(date):
            return self._obj.filter(ee.Filter.lte("system:time_start", date)).mosaic()

        imageList = timeList.map(fill)

        return ee.ImageCollection(imageList)

    def medoid(self) -> ee.Image:
        """Compute the medoid of the :py:class:`ee.ImageCollection`.

        The medoid is the image that has the smallest sum of distances to all other images in the collection.
        The distance is computed using the Euclidean distance between the pixels of the images.

        Returns:
            An Image that is the medoid of the :py:class:`ee.ImageCollection`.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                medoid = collection.geetools.medoid()
                print(medoid.getInfo())
        """
        # create a random name for the sum of distances band to avoid conflicts
        sumOfDistancesName = uuid.uuid4().hex

        # discover bandname from the first image of the collection
        bandNames = self._obj.first().bandNames()

        # normalize the band used to compute the distance
        # first extract the min and max value of each band pixelwizse along the stac and then
        # normalize the pixel values.
        minMax = self._obj.reduce(ee.Reducer.minMax())

        def normalizeBands(image):
            def normalizeBand(bandName):
                band = image.select([bandName])
                bandMin = minMax.select(ee.String(bandName).cat("_min"))
                bandMax = minMax.select(ee.String(bandName).cat("_max"))
                return band.subtract(bandMin).divide(bandMax.subtract(bandMin))

            return ee.ImageCollection(bandNames.map(normalizeBand)).toBands().rename(bandNames)

        normalized = self._obj.map(normalizeBands)

        # compute the distance between each image and all the others
        def computeSumDistance(image):
            def computeDistance(other):
                return image.subtract(other).pow(2).reduce(ee.Reducer.sum()).sqrt()

            sumDistances = normalized.map(computeDistance).reduce(ee.Reducer.sum())
            return image.addBands(sumDistances.rename(sumOfDistancesName))

        sumDistance = normalized.map(computeSumDistance)

        # use the computed sum of distances as a sorting band for a quality mossaic
        # to get the image with the smallest sum of distances
        medoid = sumDistance.qualityMosaic(sumOfDistancesName)

        return ee.Image(medoid).select(bandNames)

    def datesByBands(
        self,
        region: ee.Geometry,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        bands: list = [],
        labels: list = [],
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Reduce the data for each image in the collection by bands on a specific region.

        This method is returning a dictionary with all the bands as keys and their reduced value for each date over the specified region as value.

        .. code-block::

            {
                "band1": {"date1": value1, "date2": value2, ...},
                "band2": {"date1": value1, "date2": value2, ...},
                ...
            }

        Parameters:
            region: The region to reduce the data on.
            reducer: The name of the reducer or a reducer object use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            bands: The bands to reduce. If empty, all bands are reduced.
            labels: The labels to use for the bands. If empty, the bands names are used.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each band and each date.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.datesByRegions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                region = ee.Geometry.Point(-122.262, 37.8719).buffer(10000)
                reduced = collection.geetools.datesByBands(region, "mean", 10000, "system:time_start")
                print(reduced.getInfo())
        """
        # cast parameters
        eeBands = ee.List(bands) if len(bands) else self._obj.first().bandNames()
        eeLabels = ee.List(labels) if len(labels) else eeBands

        # recast band names as labels in the source collection
        ic = self._obj.select(eeBands).map(lambda i: i.rename(eeLabels))

        # aggregate all the dates contained in the collection
        dateList = ic.aggregate_array(dateProperty).map(lambda d: ee.Date(d).format(EE_DATE_FORMAT))

        # create a reducer from the specified parameters
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer

        # create a list of dictionaries with the reduced values for each band
        def reduce(lbl: ee.String) -> ee.Dictionary:
            image = ic.select([lbl]).toBands().rename(dateList)
            return image.reduceRegion(
                reducer=red,
                geometry=region,
                scale=scale,
                crs=crs,
                crsTransform=crsTransform,
                bestEffort=bestEffort,
                maxPixels=maxPixels,
                tileScale=tileScale,
            )

        return ee.Dictionary.fromLists(eeLabels, eeLabels.map(reduce))

    def datesByRegions(
        self,
        band: str,
        regions: ee.FeatureCollection,
        label: str = "system:index",
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Reduce the data for each image in the collection by regions for a single band.

        This method is returning a dictionary with all the regions as keys and their reduced value for each date over the specified region for a specific band as value.

        .. code-block::

            {
                "region1": {"date1": value1, "date2": value2, ...},
                "region2": {"date1": value1, "date2": value2, ...},
                ...
            }

        Parameters:
            band: The band to reduce.
            regions: The regions to reduce the data on.
            label: The property to use as label for each region. Default is ``"system:index"``.
            reducer: The name of the reducer or a reducer object use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each region and each date.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.datesByBands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                regions = ee.FeatureCollection([
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(10000), {"name": "region1"}),
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(20000), {"name": "region2"})
                ])

                reduced = collection.geetools.datesByRegions("B1", regions, "name", "mean", 10000, "system:time_start")
                print(reduced.getInfo())
        """
        # aggregate all the dates of the image collection into bands of a single image
        def to_string(date: ee.Date) -> ee.String:
            return ee.Date(date).format(EE_DATE_FORMAT)

        dateList = self._obj.aggregate_array(dateProperty).map(to_string)

        # reduce the data for each region
        image = self._obj.select([band]).toBands().rename(dateList)
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer
        reduced = image.reduceRegions(
            collection=regions,
            reducer=red,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        )

        # create a list of dictionaries for each region and aggregate them into a dictionary
        values = reduced.toList(regions.size()).map(lambda f: ee.Feature(f).toDictionary(dateList))
        keys = ee.List(regions.aggregate_array(label))

        return ee.Dictionary.fromLists(keys, values)

    def doyByBands(
        self,
        region: ee.Geometry,
        spatialReducer: str | ee.Reducer = "mean",
        timeReducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        bands: list = [],
        labels: list = [],
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Aggregate the images that occurs on the same day and then reduce each band on a single region.

        This method is returning a dictionary with all the bands as keys and their reduced value for each day over the specified region as value.

        .. code-block::

            {
                "band1": {"doy1": value1, "doy2": value2, ...},
                "band2": {"doy1": value1, "doy2": value2, ...},
                ...
            }

        Parameters:
            region: The region to reduce the data on.
            spatialReducer: The name of the reducer or a reducer object to use for spatial reduction. Default is ``"mean"``.
            timeReducer: The name of the reducer or a reducer object to use for time reduction. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            bands: The bands to reduce. If empty, all bands are reduced.
            labels: The labels to use for the bands. If empty, the bands names are used.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each band and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`
        """
        # cast parameters
        bands = ee.List(bands) if len(bands) else self._obj.first().bandNames()
        labels = ee.List(labels) if len(labels) else bands

        # recast band names as labels in the source collection
        ic = self._obj.select(bands).map(lambda i: i.rename(labels))

        # create 2 metadata name as random string to avoid any risk of conflicts
        doy_metadata, size_metadata = uuid.uuid4().hex, uuid.uuid4().hex

        # add the day of year as metadata to each image
        def doy_tag(i: ee.Image) -> ee.Image:
            doy = ee.Date(i.get(dateProperty)).getRelative("day", "year")
            return i.set(doy_metadata, doy)

        ic = self._obj.map(doy_tag)

        # create a list of :py:class:`ee.ImageCollection` where every images of the same day are grouped together
        dayList = ee.List.sequence(0, 366)

        def filter_doy(d: ee.Number) -> ee.ImageCollection:
            c = ic.filter(ee.Filter.eq(doy_metadata, d))
            c = c.set(size_metadata, c.size())
            return c.set(doy_metadata, d)

        icList = dayList.map(filter_doy)

        # reduce every sub ImageCollection in the list into images (it's the temporal reduction)
        # and aggregate the result as a single ImageCollection
        timeRed = (
            getattr(ee.Reducer, timeReducer)() if isinstance(timeReducer, str) else timeReducer
        )

        def timeReduce(c: ee.imageCollection) -> ee.image:
            c = ee.ImageCollection(c)
            i = c.reduce(timeRed).rename(labels)
            i = i.set(size_metadata, c.get(size_metadata))
            return i.set(doy_metadata, c.get(doy_metadata))

        ic = ee.ImageCollection(icList.map(timeReduce)).filter(ee.Filter.gt(size_metadata, 0))

        # spatially reduce the generated imagecollection over the region for each band
        doyList = ic.aggregate_array(doy_metadata).map(lambda d: ee.Number(d).int().format())
        spatialRed = (
            getattr(ee.Reducer, spatialReducer)()
            if isinstance(spatialReducer, str)
            else spatialReducer
        )

        def spatialReduce(label: ee.String) -> ee.Dictionary:
            image = ic.select([label]).toBands().rename(doyList)
            return image.reduceRegion(
                reducer=spatialRed,
                geometry=region,
                scale=scale,
                crs=crs,
                crsTransform=crsTransform,
                bestEffort=bestEffort,
                maxPixels=maxPixels,
                tileScale=tileScale,
            )

        return ee.Dictionary.fromLists(labels, ee.List(labels).map(spatialReduce))

    def doyByRegions(
        self,
        band: str,
        regions: ee.FeatureCollection,
        label: str = "system:index",
        spatialReducer: str | ee.Reducer = "mean",
        timeReducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Aggregate the images that occurs on the same day and then reduce a single band on multiple regions.

        This method is returning a dictionary with all the regions as keys and their reduced value for each day over the specified region for a specific band as value.

        .. code-block::

            {
                "region1": {"doy1": value1, "doy2": value2, ...},
                "region2": {"doy1": value1, "doy2": value2, ...},
                ...
            }

        Parameters:
            band: The band to reduce.
            regions: The regions to reduce the data on.
            label: The property to use as label for each region. Default is ``"system:index"``.
            spatialReducer: The name of the reducer or a reducer object to use for spatial reduction. Default is ``"mean"``.
            timeReducer: The name of the reducer or a reducer object to use for time reduction. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each region and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`
        """
        # create 2 metadata name as random string to avoid any risk of conflicts
        doy_metadata, size_metadata = uuid.uuid4().hex, uuid.uuid4().hex

        # add the day of year as metadata to each image
        def doy_tag(i: ee.Image) -> ee.Image:
            doy = ee.Date(i.get(dateProperty)).getRelative("day", "year")
            return i.set(doy_metadata, doy)

        ic = self._obj.select([band]).map(doy_tag)

        # create a list of ImageCollection where every images of the same day are grouped together
        dayList = ee.List.sequence(0, 366)

        def filter_doy(d: ee.Number) -> ee.ImageCollection:
            c = ic.filter(ee.Filter.eq(doy_metadata, d))
            c = c.set(size_metadata, c.size())
            return c.set(doy_metadata, d)

        icList = dayList.map(filter_doy)

        # reduce every sub ImageCollection in the list into images (it's the temporal reduction)
        # and aggregate the result as a single ImageCollection
        timeRed = (
            getattr(ee.Reducer, timeReducer)() if isinstance(timeReducer, str) else timeReducer
        )

        def timeReduce(c: ee.imageCollection) -> ee.image:
            c = ee.ImageCollection(c)
            i = c.reduce(timeRed).rename([band])
            i = i.set(size_metadata, c.get(size_metadata))
            return i.set(doy_metadata, c.get(doy_metadata))

        ic = ee.ImageCollection(icList.map(timeReduce)).filter(ee.Filter.gt(size_metadata, 0))

        # reduce the data for each region
        doyList = ic.aggregate_array(doy_metadata).map(lambda d: ee.Number(d).int().format())
        spatialRed = (
            getattr(ee.Reducer, spatialReducer)()
            if isinstance(spatialReducer, str)
            else spatialReducer
        )
        image = ic.toBands().rename(doyList)
        reduced = image.reduceRegions(
            collection=regions,
            reducer=spatialRed,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        )

        # create a list of dictionaries for each region and aggregate them into a dictionary
        values = reduced.toList(regions.size()).map(lambda f: ee.Feature(f).toDictionary(doyList))
        keys = ee.List(regions.aggregate_array(label))

        return ee.Dictionary.fromLists(keys, values)

    def doyBySeasons(
        self,
        band: str,
        region: ee.Geometry,
        seasonStart: int | ee.Number,
        seasonEnd: int | ee.Number,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Aggregate for each year on a single region a single band.

        This method is returning a dictionary with all the years as keys and their reduced value for each day of the season over the specified region for a specific band as value.
        To set the start and end of the season, use the :py:meth:`ee.Date.getRelative` or :py:class:`time.struct_time` method to get the day of the year.

        .. code-block::

            {
                "year1": {"doy1": value1, "doy2": value2, ...},
                "year2": {"doy1": value1, "doy2": value2, ...},
                ...
            }

        Parameters:
            band: The band to reduce.
            region: The region to reduce the data on.
            seasonStart: The day of the year that marks the start of the season.
            seasonEnd: The day of the year that marks the end of the season.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each year and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filter(ee.Filter.Or(
                        ee.Filter.date("2022-01-01", "2022-12-31"),
                        ee.Filter.date("2016-01-01", "2016-12-31"),
                    ))
                    .map(lambda i: ee.Image(i).addBands(
                        ee.Image(i)
                        .normalizedDifference(["B5", "B4"])
                        .rename("NDVI")
                    ))
                )

                reduced = collection.geetools.doyBySeasons(
                    band = "NDVI",
                    region = ee.Geometry.Point(-122.262, 37.8719).buffer(1000),
                    seasonStart = ee.Date("2016-05-01").getRelative("day", "year"),
                    seasonEnd = ee.Date("2016-10-31").getRelative("day", "year"),
                    reducer = "mean",
                    dateProperty = "system:time_start",
                    scale = 10000
                )
                reduced.getInfo()
        """
        # force cast the start and end of season as ee.Number
        seasonStart, seasonEnd = ee.Number(seasonStart), ee.Number(seasonEnd)

        # add a doy metadata to the images
        doy_metadata, year_metadata = uuid.uuid4().hex, uuid.uuid4().hex

        def date_tag(i: ee.Image) -> ee.Image:
            date = ee.Date(i.get(dateProperty))
            doy = date.getRelative("day", "year")
            year = date.get("year")
            return i.set(doy_metadata, doy).set(year_metadata, year)

        ic = self._obj.select([band]).map(date_tag)

        # create a List of image collection where every images from the same year are grouped together
        yearList = ic.aggregate_array(year_metadata).distinct().sort()
        yearKeys = yearList.map(lambda y: ee.Number(y).int().format())
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer

        def reduce(year: ee.Number) -> ee.Dictionary:
            c = ic.filter(ee.Filter.eq(year_metadata, year))
            c = c.filter(ee.Filter.rangeContains(doy_metadata, seasonStart, seasonEnd))
            doyList = c.aggregate_array(doy_metadata).map(lambda d: ee.Number(d).int().format())
            return (
                c.toBands()
                .rename(doyList)
                .reduceRegion(
                    reducer=red,
                    geometry=region,
                    scale=scale,
                    crs=crs,
                    crsTransform=crsTransform,
                    bestEffort=bestEffort,
                    maxPixels=maxPixels,
                    tileScale=tileScale,
                )
            )

        return ee.Dictionary.fromLists(yearKeys, yearList.map(reduce))

    def doyByYears(
        self,
        band: str,
        region: ee.Geometry,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Aggregate for each year on a single region a single band.

        This method is returning a dictionary with all the years as keys and their reduced value for each day over the specified region for a specific band as value.

        .. code-block::

            {
                "year1": {"doy1": value1, "doy2": value2, ...},
                "year2": {"doy1": value1, "doy2": value2, ...},
                ...
            }

        Parameters:
            band: The band to reduce.
            region: The region to reduce the data on.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each year and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filter(ee.Filter.Or(
                        ee.Filter.date("2022-01-01", "2022-12-31"),
                        ee.Filter.date("2016-01-01", "2016-12-31"),
                    ))
                    .map(lambda i: ee.Image(i).addBands(
                        ee.Image(i)
                        .normalizedDifference(["B5", "B4"])
                        .rename("NDVI")
                    ))
                )

                reduced = collection.geetools.doyByYears(
                    band = "NDVI",
                    region = ee.Geometry.Point(-122.262, 37.8719).buffer(1000),
                    reducer = "mean",
                    dateProperty = "system:time_start",
                    scale = 10000
                )
                reduced.getInfo()
        """
        return self.doyBySeasons(
            band=band,
            region=region,
            seasonStart=ee.Number(0),
            seasonEnd=ee.Number(366),
            reducer=reducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        )

    def plot_dates_by_bands(
        self,
        region: ee.Geometry,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        bands: list = [],
        labels: list = [],
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced data for each image in the collection by bands on a specific region.

        This method is plotting the reduced data for each image in the collection by bands on a specific region.

        Parameters:
            region: The region to reduce the data on.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            bands: The bands to reduce. If empty, all bands are reduced.
            labels: The labels to use for the bands. If empty, the bands names are used.
            colors: The colors to use for the bands. If empty, the default colors are used.
            ax: The matplotlib axes to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A matplotlib axes with the reduced values for each band and each date.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                region = ee.Geometry.Point(-122.262, 37.8719).buffer(10000)
                collection.geetools.plot_dates_by_bands(region, "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self.datesByBands(
            region=region,
            reducer=reducer,
            dateProperty=dateProperty,
            bands=bands,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates int datetime objects
        def to_date(dict):
            return {dt.strptime(d, PY_DATE_FORMAT): v for d, v in dict.items()}

        data = {l: to_date(dict) for l, dict in raw_data.items()}

        # create the plot
        ax = plot_data("date", data, "Date", colors, ax)

        return ax

    def plot_dates_by_regions(
        self,
        band: str,
        regions: ee.FeatureCollection,
        label: str = "system:index",
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced data for each image in the collection by regions for a single band.

        This method is plotting the reduced data for each image in the collection by regions for a single band.

        Parameters:
            band: The band to reduce.
            regions: The regions to reduce the data on.
            label: The property to use as label for each region. Default is ``"system:index"``.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            ax: The matplotlib axes to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A matplotlib axes with the reduced values for each region and each date.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                regions = ee.FeatureCollection([
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(10000), {"name": "region1"}),
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(20000), {"name": "region2"})
                ])

                collection.geetools.plot_dates_by_regions("B1", regions, "name", "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self.datesByRegions(
            band=band,
            regions=regions,
            label=label,
            reducer=reducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates int datetime objects
        def to_date(dict):
            return {dt.strptime(d, PY_DATE_FORMAT): v for d, v in dict.items()}

        data = {l: to_date(dict) for l, dict in raw_data.items()}

        # create the plot
        ax = plot_data("date", data, "Date", colors, ax)

        return ax

    def plot_doy_by_bands(
        self,
        region: ee.Geometry,
        spatialReducer: str | ee.Reducer = "mean",
        timeReducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        bands: list = [],
        labels: list = [],
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced data for each image in the collection by bands on a specific region.

        This method is plotting the reduced data for each image in the collection by bands on a specific region.

        Parameters:
            region: The region to reduce the data on.
            spatialReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            timeReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            bands: The bands to reduce. If empty, all bands are reduced.
            labels: The labels to use for the bands. If empty, the bands names are used.
            colors: The colors to use for the bands. If empty, the default colors are used.
            ax: The matplotlib axes to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A matplotlib axes with the reduced values for each band and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                region = ee.Geometry.Point(-122.262, 37.8719).buffer(10000)
                collection.geetools.plot_doy_by_bands(region, "mean", "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self.doyByBands(
            region=region,
            spatialReducer=spatialReducer,
            timeReducer=timeReducer,
            dateProperty=dateProperty,
            bands=bands,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates strings into int object and reorder the dictionary
        def to_int(d):
            return {int(k): v for k, v in d.items()}

        data = {l: dict(sorted(to_int(raw_data[l]).items())) for l in raw_data}

        # create the plot
        ax = plot_data("doy", data, "Day of Year", colors, ax)

        return ax

    def plot_doy_by_regions(
        self,
        band: str,
        regions: ee.FeatureCollection,
        label: str = "system:index",
        spatialReducer: str | ee.Reducer = "mean",
        timeReducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced data for each image in the collection by regions for a single band.

        This method is plotting the reduced data for each image in the collection by regions for a single band.

        Parameters:
            band: The band to reduce.
            regions: The regions to reduce the data on.
            label: The property to use as label for each region. Default is ``"system:index"``.
            spatialReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            timeReducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            ax: The matplotlib axes to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A matplotlib axes with the reduced values for each region and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filterDate("2014-01-01", "2014-12-31")
                )

                regions = ee.FeatureCollection([
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(10000), {"name": "region1"}),
                    ee.Feature(ee.Geometry.Point(-122.262, 37.8719).buffer(20000), {"name": "region2"})
                ])

                collection.geetools.plot_doy_by_regions("B1", regions, "name", "mean", "mean", 10000, "system:time_start")
        """
        # get the reduced data
        raw_data = self.doyByRegions(
            band=band,
            regions=regions,
            label=label,
            spatialReducer=spatialReducer,
            timeReducer=timeReducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates strings into int object and reorder the dictionary
        def to_int(d):
            return {int(k): v for k, v in d.items()}

        data = {l: dict(sorted(to_int(raw_data[l]).items())) for l in raw_data}

        # create the plot
        ax = plot_data("doy", data, "Day of Year", colors, ax)

        return ax

    def plot_doy_by_seasons(
        self,
        band: str,
        region: ee.Geometry,
        seasonStart: int | ee.Number,
        seasonEnd: int | ee.Number,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced data for each image in the collection by years for a single band.

        This method is plotting the reduced data for each image in the collection by years for a single band.
        To set the start and end of the season, use the :py:meth:`ee.Date.getRelative` or :py:class:`time.struct_time` method to get the day of the year.

        Parameters:
            band: The band to reduce.
            region: The region to reduce the data on.
            seasonStart: The day of the year that marks the start of the season.
            seasonEnd: The day of the year that marks the end of the season.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            ax: The matplotlib axes to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A matplotlib axes with the reduced values for each year and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_years`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filter(ee.Filter.Or(
                        ee.Filter.date("2022-01-01", "2022-12-31"),
                        ee.Filter.date("2016-01-01", "2016-12-31"),
                    ))
                    .map(lambda i: ee.Image(i).addBands(
                        ee.Image(i)
                        .normalizedDifference(["B5", "B4"])
                        .rename("NDVI")
                    ))
                )

                collection.geetools.plot_doy_by_seasons(
                    band = "NDVI",
                    region = ee.Geometry.Point(-122.262, 37.8719).buffer(1000),
                    seasonStart = ee.Date("2016-05-01").getRelative("day", "year"),
                    seasonEnd = ee.Date("2016-10-31").getRelative("day", "year"),
                    reducer = "mean",
                    dateProperty = "system:time_start",
                    scale = 10000
                )
        """
        # get the reduced data
        raw_data = self.doyBySeasons(
            band=band,
            region=region,
            seasonStart=seasonStart,
            seasonEnd=seasonEnd,
            reducer=reducer,
            dateProperty=dateProperty,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        ).getInfo()

        # transform all the dates strings into int object and reorder the dictionary
        def to_int(d):
            return {int(k): v for k, v in d.items()}

        data = {l: dict(sorted(to_int(raw_data[l]).items())) for l in raw_data}

        # create the plot
        ax = plot_data("doy", data, "Day of Year", colors, ax)

        return ax

    def plot_doy_by_years(
        self,
        band: str,
        region: ee.Geometry,
        reducer: str | ee.Reducer = "mean",
        dateProperty: str = "system:time_start",
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = 10**7,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced data for each image in the collection by years for a single band.

        This method is plotting the reduced data for each image in the collection by years for a single band.

        Parameters:
            band: The band to reduce.
            region: The region to reduce the data on.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            dateProperty: The property to use as date for each image. Default is ``"system:time_start"``.
            colors: The colors to use for the regions. If empty, the default colors are used.
            ax: The matplotlib axes to plot the data on. If None, a new figure is created.
            scale: The scale in meters to use for the reduction. default is 10000m
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. Defaults to 1e7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A matplotlib axes with the reduced values for each year and each day.

        See Also:
            - :docstring:`ee.ImageCollection.geetools.doyByBands`
            - :docstring:`ee.ImageCollection.geetools.doyByRegions`
            - :docstring:`ee.ImageCollection.geetools.doyBySeasons`
            - :docstring:`ee.ImageCollection.geetools.doyByYears`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_bands`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_regions`
            - :docstring:`ee.ImageCollection.geetools.plot_doy_by_seasons`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
                    .filterBounds(ee.Geometry.Point(-122.262, 37.8719))
                    .filter(ee.Filter.Or(
                        ee.Filter.date("2022-01-01", "2022-12-31"),
                        ee.Filter.date("2016-01-01", "2016-12-31"),
                    ))
                    .map(lambda i: ee.Image(i).addBands(
                        ee.Image(i)
                        .normalizedDifference(["B5", "B4"])
                        .rename("NDVI")
                    ))
                )

                collection.geetools.plot_doy_by_years(
                    band = "NDVI",
                    region = ee.Geometry.Point(-122.262, 37.8719).buffer(1000),
                    reducer = "mean",
                    dateProperty = "system:time_start",
                    scale = 10000
                )
        """
        return self.plot_doy_by_seasons(
            band=band,
            region=region,
            seasonStart=ee.Number(0),
            seasonEnd=ee.Number(366),
            reducer=reducer,
            dateProperty=dateProperty,
            colors=colors,
            ax=ax,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        )

    def reduceRegion(
        self,
        reducer: str,
        geometry: ee.Geometry,
        idProperty: str = "system:index",
        idType: type = ee.Number,
        idReducer: str | ee.Reducer = "first",
        idFormat: str | ee.String | None = None,
        scale: int | float | None = None,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int | None = None,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Apply a reducer to all the pixels in a specific region on each image of the collection.

        The result will be shaped as a dictionary with the idProperty as key and for each of them the reduced band values.

        .. code-block::

            {
                "image1": {"band1": value1, "band2": value2, ...},
                "image2": {"band1": value1, "band2": value2, ...},
            }

        Warning:
            The method makes a call to the pure Python ``uuid`` package, so it cannot be used in a server-side ``map`` function.

        Parameters:
            idProperty: The property to use as the key of the resulting dictionary. If not specified, the key of the dictionary is the index of the image in the collection. One should use a meaningful property to avoid conflicts. in case of conflicts, the images with the same property will be mosaicked together (e.g. all raw satellite imagery with the same date) to make sure the final reducer have 1 single entry per idProperty.
            reducer: THe reducer to apply.
            idType: The type of the idProperty. Default is ee.Number. As Dates are stored as numbers in metadata, we need to know what parsing to apply to the property in advance.
            idReducer: If the multiple images have the same idProperty, they will be aggregated beforehand using the provided reducer. default to a mosaic behaviour to match most of the satellite imagery collection where the world is split for each date between multiple images.
            idFormat: If a date format is used for the IdProperty, the values will be formatted as "YYYY-MM-ddThh-mm-ss". If a number format is used for the IdProperty, the values will be formatted as a string ("%s"). You can specify any other format compatible with band names.
            geometry: The region over which to reduce the data.
            scale: A nominal scale in meters to work in.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with the reduced values for each image.

        Examples:
            .. jupyter-execute::

                import ee
                import geetools
                from geetools.utils import initialize_documentation
                import pandas as pd

                initialize_documentation()

                ## Import the example feature collection and drop the data property.
                ecoregion = (
                    ee.FeatureCollection("projects/google/charts_feature_example")
                    .select(["label", "value", "warm"])
                    .first()
                )

                ## Load MODIS vegetation indices data and subset a decade of images.
                vegIndices = (
                    ee.ImageCollection("MODIS/061/MOD13A1")
                    .filter(ee.Filter.date("2010-01-01", "2010-05-30"))
                    .select(["NDVI", "EVI"])
                )

                data = vegIndices.geetools.reduceRegion(
                    geometry=ecoregion.geometry(),
                    reducer="mean",
                    idProperty="system:time_start",
                    idType=ee.Date,
                    scale=10000,
                )

                # display them as a dataframe
                df = pd.DataFrame(data.getInfo()).transpose()
                df.head(15)
        """
        # filter the imageCollection with the region parameter to reduce the number of manipulated images and speed up the computation
        ic = self._obj.filterBounds(geometry)

        # raise an error if the idType is not supported
        if idType not in [ee.String, ee.Number, ee.Date]:
            msg = f"idPropertyType format {idType} not supported (yet)!"
            raise ValueError(msg)

        # create a unique property name to avoid conflict with any
        # existing property in the image collection
        pname = uuid.uuid4().hex

        # add to each image the idProperty as metadata converted to string according
        # to the idPropertyType parameter
        def addIdProperty(i: ee.Image) -> ee.Image:
            p = i.get(idProperty)
            if idType == ee.String:
                p = ee.String(p)
            elif idType == ee.Number:
                p = ee.Number(p).format(idFormat or "%s")
            elif idType == ee.Date:
                p = ee.Date(p).format(idFormat or EE_DATE_FORMAT)
            return i.set(pname, p)

        ic = ic.map(addIdProperty)

        # reduce the images collection to an collection of image with unique idproperty
        # in case of duplication the images arereduced together using the idReducer
        idRed = idReducer  # renaming of the variable to save space
        red = getattr(ee.Reducer, idRed)() if isinstance(idRed, str) else idRed
        pList = ic.aggregate_array(pname).distinct()
        bands = ic.first().bandNames()
        iList = pList.map(lambda p: ic.filter(ee.Filter.eq(pname, p)).reduce(red).rename(bands))
        ic = ee.ImageCollection(iList)

        # The tobands method will produce an image with the following band names: <system:index>_<bandName>
        # What we want is: <idProperty>_<bandName> so we can make more advance filtering downstream.
        bandNames = pList.map(lambda p: bands.map(lambda b: ee.String(p).cat("_").cat(b)))
        bandNames = bandNames.flatten()

        # reduce the collection  to a single image and run the reducer on it
        image = ic.toBands().rename(bandNames)
        reduced = image.reduceRegion(
            reducer=reducer,
            geometry=geometry,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            bestEffort=bestEffort,
            maxPixels=maxPixels,
            tileScale=tileScale,
        )

        # reshape the result dictionary into the desired structure
        def getProp(p: ee.String) -> ee.Dictionary:
            p = ee.String(p)
            keys = reduced.keys().filter(ee.Filter.stringStartsWith("item", p))
            values = reduced.select(keys).values()
            keys = keys.map(lambda k: ee.String(k).replace(p, "").slice(1))
            return ee.Dictionary.fromLists(keys, values)

        values = pList.map(lambda p: getProp(p))

        return ee.Dictionary.fromLists(pList, values)

    def reduceRegions(
        self,
        reducer: str | ee.Reducer,
        collection: ee.FeatureCollection,
        idProperty: str | ee.String = "system:index",
        idType: type = ee.Number,
        idReducer: str | ee.Reducer = "first",
        idFormat: str | ee.String | None = None,
        scale: int | float | None = None,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float | ee.Number = 1,
    ) -> ee.FeatureCollection:
        """Apply a reducer to all the pixels in specific regions on each images of a collection.

        The result will be shaped as a :py:class:`ee.FeatureCollection` with the ``idProperty`` as key and for each of them the reduced band values over one region.
        Each feature will have the same properties as the original feature collection and thus be identified by a key pair:
        "system:id" + "system:image_property"

        Here is a simple table representation of the result striped from the geometry:

        .. csv-table::
            :header: image_id,feature_id,property1,property2,...,reduced_band1,reduced_band2,...
            :widths: auto

            sentinel2_id_1,feature_1,feature1_prop1,feature1_prop2,...,reduced_image1_band1_feature1,reduced_image1_band2_feature1,...
            sentinel2_id_2,feature_1,feature1_prop1,feature1_prop2,...,reduced_image2_band1_feature1,reduced_image2_band2_feature1,...
            sentinel2_id_3,feature_1,feature1_prop1,feature1_prop2,...,reduced_image3_band1_feature1,reduced_image3_band2_feature1,...
            sentinel2_id_1,feature_2,feature2_prop1,feature2_prop2,...,reduced_image1_band1_feature2,reduced_image1_band2_feature2,...
            sentinel2_id_2,feature_2,feature2_prop1,feature2_prop2,...,reduced_image2_band1_feature2,reduced_image2_band2_feature2,...
            sentinel2_id_3,feature_2,feature2_prop1,feature2_prop2,...,reduced_image3_band1_feature2,reduced_image3_band2_feature2,...

        Warning:
            The method makes a call to the pure Python uuid package, so it cannot be used in a server-side map function.

        Parameters:
            reducer: The reducer to apply.
            collection: The regions to reduce the data on.
            idProperty: The property to use as the key of the resulting dictionary. If not specified, the key of the dictionary is the index of the image in the collection. One should use a meaningful property to avoid conflicts. in case of conflicts, the images with the same property will be mosaicked together (e.g. all raw satellite imagery with the same date) to make sure the final reducer have 1 single entry per idProperty.
            idType: The type of the idProperty. Default is ee.Number. As Dates are stored as numbers in metadata, we need to know what parsing to apply to the property in advance.
            idReducer: If the multiple images have the same idProperty, they will be aggregated beforehand using the provided reducer. default to a mosaic behaviour to match most of the satellite imagery collection where the world is split for each date between multiple images.
            idFormat: If a date format is used for the IdProperty, the values will be formatted as "YYYY-MM-ddThh-mm-ss". If a number format is used for the IdProperty, the values will be formatted as a string ("%s"). You can specify any other format compatible with band names.
            scale: A nominal scale in meters to work in.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A FeatureCollection with the reduced values for each image.

        Examples:
            .. jupyter-execute::

                import ee
                import geetools
                from geetools.utils import initialize_documentation
                import geopandas as gpd

                initialize_documentation()

                ## Import the example feature collection and drop the data property.
                ecoregions = (
                    ee.FeatureCollection("projects/google/charts_feature_example")
                    .select(["label", "value", "warm"])
                )

                ## Load MODIS vegetation indices data and subset a decade of images.
                vegIndices = (
                    ee.ImageCollection("MODIS/061/MOD13A1")
                    .filter(ee.Filter.date("2010-01-01", "2010-05-30"))
                    .select(["NDVI", "EVI"])
                )

                data = vegIndices.geetools.reduceRegions(
                    collection=ecoregions,
                    reducer="mean",
                    idProperty="system:time_start",
                    idType=ee.Date,
                    scale=10000,
                )

                # display them as a dataframe
                gdf = gpd.GeoDataFrame.from_features(data.getInfo()["features"])
                gdf.head(15)
        """
        # raise an error if the idType is not supported
        if idType not in [ee.String, ee.Number, ee.Date]:
            msg = f"idPropertyType format {idType} not supported (yet)!"
            raise ValueError(msg)

        # filter the imageCollection with the region parameter to reduce the number of manipulated
        # images and speed up the computation
        ic = self._obj.filterBounds(collection)

        # create a unique property name to avoid conflict with any
        # existing property in the image collection
        pname = uuid.uuid4().hex

        # add to each image the idProperty as metadata converted to string according
        # to the idPropertyType parameter
        def addIdProperty(i: ee.Image) -> ee.Image:
            p = i.get(idProperty)
            if idType == ee.String:
                p = ee.String(p)
            elif idType == ee.Number:
                p = ee.Number(p).format(idFormat or "%s")
            elif idType == ee.Date:
                p = ee.Date(p).format(idFormat or EE_DATE_FORMAT)
            return i.set(pname, p)

        ic = ic.map(addIdProperty)

        # reduce the images collection to a collection of image with unique idproperty
        # in case of duplication the images are reduced together using the idReducer
        idRed = idReducer  # renaming of the variable to save space
        red = getattr(ee.Reducer, idRed)() if isinstance(idRed, str) else idRed
        pList = ic.aggregate_array(pname).distinct()
        bands = ic.first().bandNames()
        iList = pList.map(lambda p: ic.filter(ee.Filter.eq(pname, p)).reduce(red).rename(bands))
        ic = ee.ImageCollection(iList)

        # The tobands method will produce an image with the following band names: <system:index>_<bandName>
        # What we want is: <idProperty>_<bandName> so we can make more advance filtering downstream.
        bandNames = pList.map(lambda p: bands.map(lambda b: ee.String(p).cat("_").cat(b)))
        bandNames = bandNames.flatten()

        # reduce the collection  to a single image and run the reducer on it
        image = ic.toBands().rename(bandNames)
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer
        reduced = image.reduceRegions(
            collection=collection,
            reducer=red,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        )

        # reshape the result featurecollection to match the requirements
        # at this stage each feature contains all the reduced values for each band and each image
        # store in props like <image_id>_<band_name> for all regions. We want to duplicate each feature
        # into single elements that store only the result of the reducer i.e. <band_name> and add an extra id
        # property to identify the image/region combination: system:image_id/system:id

        # get the list of original property names, they will be transported to each duplicated instances
        originalProps = collection.first().propertyNames()

        def splitFeatures(f: ee.Feature) -> ee.List:
            f = ee.Feature(f)

            def splitId(loc_id: ee.String) -> ee.Feature:
                loc_id = ee.String(loc_id)
                loc_f = ee.Feature(f).select([loc_id.cat("_.*")])
                oldNames = loc_f.propertyNames().filter(
                    ee.Filter.stringStartsWith("item", "system:").Not()
                )
                newNames = oldNames.map(lambda n: ee.String(n).replace(loc_id.cat("_"), ""))
                loc_f = ee.Feature(ee.Feature(loc_f).select(oldNames, newNames))
                loc_f = ee.Feature(loc_f.copyProperties(f, properties=originalProps))
                loc_f = ee.Feature(loc_f.set("image_id", loc_id))
                loc_f = ee.Feature(loc_f.set("feature_id", f.get("system:index")))
                return loc_f

            return ee.List(pList.map(splitId))

        fclist = reduced.toList(reduced.size()).map(splitFeatures).flatten()

        return ee.FeatureCollection(fclist)
