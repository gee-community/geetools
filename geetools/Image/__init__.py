"""Toolbox for the ``ee.Image`` class."""
from __future__ import annotations

from typing import Optional, Union

import ee

from geetools.accessors import geetools_accessor

from . import _indices


@geetools_accessor(ee.Image)
class Image:
    """Toolbox for the ``ee.Image`` class."""

    def __init__(self, obj: ee.Image):
        """Initialize the Image class."""
        self._obj = obj

    # -- Indices manipulation --------------------------------------------------
    index_list = classmethod(_indices.index_list)
    spectralIndices = _indices.spectralIndices
    tasseledCap = _indices.tasseledCap

    # -- the rest --------------------------------------------------------------

    def addDate(self) -> ee.Image:
        """Add a band with the date of the image in the provided format.

        The date is stored as a Timestamp in millisecond in a band date.

        Returns:
            The image with the date band added.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image.geetools.addDate()
                date = image.select('date')
                buffer = ee.Geometry.Point([12.4534, 41.9033]).buffer(100)
                value = date.reduceRegion(ee.Reducer.first(), buffer, 10).get("date")
                ee.Date(value).format('YYYY-MM-dd').getInfo()
        """
        return self._obj.addBands(
            ee.Image.constant(self._obj.date().millis()).rename("date")
        )

    def addSuffix(
        self, suffix: Union[str, ee.String], bands: Union[ee.List, list] = []
    ) -> ee.Image:
        """Add a suffix to the image selected band.

        Add a suffix to the selected band. If no band is specified, the suffix is added to all bands.

        Parameters:
            suffix: The suffix to add to the band.
            bands: The bands to add the suffix to. If None, all bands are selected.

        Returns:
            The image with the suffix added to the selected bands.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image.geetools.addSuffix('_suffix')
                print(image.bandNames().getInfo())
        """
        suffix = ee.String(suffix)
        bands = self._obj.bandNames() if bands == [] else ee.List(bands)
        bandNames = bands.iterate(
            lambda b, n: ee.List(n).replace(b, ee.String(b).cat(suffix)),
            self._obj.bandNames(),
        )
        return self._obj.rename(bandNames)

    def addPrefix(
        self, prefix: Union[str, ee.String], bands: Union[ee.List, list] = []
    ):
        """Add a prefix to the image selected band.

        Add a prefix to the selected band. If no band is specified, the prefix is added to all bands.

        Parameters:
            prefix: The prefix to add to the band.
            bands: The bands to add the prefix to. If None, all bands are selected.

        Returns:
            The image with the prefix added to the selected bands.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image.geetools.addPrefix('prefix_')
                print(image.bandNames().getInfo())
        """
        prefix = ee.String(prefix)
        bands = self._obj.bandNames() if bands == [] else ee.List(bands)
        bandNames = bands.iterate(
            lambda b, n: ee.List(n).replace(b, prefix.cat(ee.String(b))),
            self._obj.bandNames(),
        )
        return self._obj.rename(bandNames)

    def getValues(
        self, point: ee.Geometry.Point, scale: Union[ee.Number, int] = 0
    ) -> ee.Dictionary:
        """Get the value of the image at the given point using specified geometry.

        The result is presented as a dictionary where the keys are the bands name and the value the mean value of the band at the given point.

        Parameters:
            point: The geometry to get the value from.

        Returns:
            A dictionary with the band names and the value at the given point.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                point = ee.Geometry.Point([11.0, 45.0])
                value = image.geetools.getValues(point, 10)
                print(value.getInfo())
        """
        scale = (
            self._obj.select(0).projection().nominalScale()
            if scale == 0
            else ee.Number(scale)
        )
        return self._obj.reduceRegion(ee.Reducer.mean(), point, scale)

    def minScale(self) -> ee.Number:
        """Return the minimum scale of the image.

        It will be looking at all bands available so Select specific values before using this method.

        Returns:
            The minimum scale of the image.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image.geetools.minScale().getInfo()
        """
        bandNames = self._obj.bandNames()
        scales = bandNames.map(
            lambda b: self._obj.select(ee.String(b)).projection().nominalScale()
        )
        return ee.Number(scales.sort().get(0))

    def merge(self, images: Union[ee.List, list]) -> ee.Image:
        """Merge images into a single image.

        Parameters:
            images: The images to merge.

        Returns:
            The merged image.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image1 = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image2 = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQL')
                image3 = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image1.geetools.merge([image2, image3])
                print(image.bandNames().getInfo())
        """
        images = ee.List(images)
        merged = images.iterate(lambda dst, src: ee.Image(src).addBands(dst), self._obj)
        return ee.Image(merged)

    def rename(self, names: Union[ee.Dictionary, dict]) -> ee.Image:
        """Rename the bands of the image.

        It's the same function as the one from GEE but it takes a dictionary as input.
        Keys are the old names and values are the new names.

        Parameters:
            names: The new names of the bands.

        Returns:
            The image with the new band names.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                src = 'COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM'
                image = ee.Image(src).select(['B1', 'B2', 'B3'])
                image = image.geetools.rename({'B1': 'Aerosol', 'B2': 'Blue'})
                print(image.bandNames().getInfo())
        """
        names = ee.Dictionary(names)
        bands = names.keys().iterate(
            lambda b, n: ee.List(n).replace(b, names.get(b)), self._obj.bandNames()
        )
        return self._obj.rename(bands)

    def remove(self, bands: Union[list, ee.List]) -> ee.Image:
        """Remove bands from the image.

        Parameters:
            bands: The bands to remove.

        Returns:
            The image without the specified bands.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                src = 'COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM'
                image = ee.Image(src).select(['B1', 'B2', 'B3'])
                image = image.geetools.remove(['B1', 'B2'])
                print(image.bandNames().getInfo())
        """
        bands = self._obj.bandNames().removeAll(ee.List(bands))
        return self._obj.select(bands)

    def toGrid(
        self,
        size: Union[ee.Number, int] = 1,
        band: Union[str, ee.String] = "",
        geometry: Optional[ee.Geometry] = None,
    ) -> ee.FeatureCollection:
        """Convert an image to a grid of polygons.

        Based on the size given by the user, the tool will build a grid of size*pixelSize x size * pixelSize cells. Each cell will be a polygon. Note that for images that have multiple scale depending on the band, we will use the first one or the one stated in the parameters.

        Parameters:
            size: The size of the grid. It will be size * pixelSize x size * pixelSize cells.
            band: The band to burn into the grid.
            geometry: The geometry to use as reference for the grid. If None, the image footprint will be used.

        Returns:
            The grid as a FeatureCollection.

        Note:
            The method has a known bug when the projection of the image is different than 3857. As we use a buffer, the grid cells can slightly overlap. Feel free to open a Issue and contribute if you feel it needs improvements.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                src = 'COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM'
                image = ee.Image(src)
                buffer = ee.Geometry.Point([12.4534, 41.9033]).buffer(100)
                grid = image.geetools.toGrid(1, 'B2', buffer)
                print(grid.getInfo())
        """
        band = ee.String(band) if band else self._obj.bandNames().get(0)
        projection = self._obj.select(band).projection()
        size = projection.nominalScale().multiply(ee.Number(size).toInt())

        # extract the centers at the correct resolution
        lonLat = ee.Image.pixelLonLat().reproject(projection)
        coords = lonLat.reduceRegion(ee.Reducer.toList(), geometry, size)

        # extract them as lists
        lat, lon = ee.List(coords.get("latitude")), ee.List(coords.get("longitude"))

        # we can now map them user their index to point -> buffer -> square
        index = ee.List.sequence(0, lat.size().subtract(2))
        squares = index.map(
            lambda i: (
                ee.Geometry.Point([lon.get(i), lat.get(i)])
                .buffer(size.divide(2))
                .bounds(0.01, projection)
            )
        )

        # make the grid
        features = ee.List(squares).map(lambda g: ee.Feature(ee.Geometry(g)))

        return ee.FeatureCollection(features)

    def clipOnCollection(
        self, fc: ee.FeatureCollection, keepProperties: Union[ee.Number, int] = 1
    ) -> ee.ImageCollection:
        """Clip an image to a FeatureCollection.

        The image will be clipped to every single features of the featureCollection as one independent image.

        Parameters:
            fc: The featureCollection to clip to.
            keepProperties: If True, the properties of the featureCollection will be added to the clipped image.

        Returns:
            The clipped imageCollection.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                src = 'COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM'
                image = ee.Image(src)
                fc = ee.FeatureCollection('FAO/GAUL/2015/level0')
                clipped = image.geetools.clipOnCollection(fc)
                print(clipped.size().getInfo())
        """

        def fcClip(feat):
            image = self._obj.clip(feat.geometry())
            return ee.Algorithms.If(
                ee.Number(keepProperties).toInt(), image.copyProperties(feat), image
            )

        return ee.ImageCollection(fc.map(fcClip))

    def bufferMask(
        self,
        radius: Union[int, ee.Number] = 1.5,
        kernelType: Union[ee.String, str] = "square",
        units: Union[ee.String, str] = "pixels",
    ) -> ee.Image:
        """Make a buffer around every masked pixel of the Image.

        The buffer will be made using the specified radius, kernelType and units and will mask surrounfing pixels.

        Parameters:
            radius: The radius of the buffer.
            kernelType: The kernel type of the buffer. One of: ``square``, ``circle``, ``diamond``, ``octagon``, ``plus``, ``square``.
            units: The units of the radius. One of: ``pixels``, ``meters``.

        Returns:
            The image with the buffer mask applied.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                src = 'COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM'
                image = ee.Image(src)
                image = image.geetools.bufferMask(1.5, 'square', 'pixels')
                print(image.bandNames().getInfo())
        """
        radius, kernelType = ee.Number(radius), ee.String(kernelType)
        units = ee.String(units)
        masked = self._obj.mask().Not()
        buffer = masked.focalMax(radius, kernelType, units)
        return self._obj.updateMask(buffer.Not())

    @classmethod
    def full(
        self,
        values: Union[list, ee.List] = [0],
        names: Union[list, ee.List] = ["constant"],
    ) -> ee.Image:
        """Create an image with the given values and names.

        Parameters:
            values: The values to initialize the image with. If one value is given, it will be used for all bands.
            names: The names of the bands. By default it uses the earthen engine default value, "constant".

        Returns:
            An image with the given values and names.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image.geetools.full([1, 2, 3], ['a', 'b', 'c'])
                print(image.bandNames().getInfo())
        """
        values, names = ee.List(values), ee.List(names)

        # resize value to the same length as names
        values = ee.List(
            ee.Algorithms.If(
                values.size().eq(1),
                ee.List.repeat(ee.Number(values.get(0)), names.size()),
                values,
            )
        )
        return ee.Image.constant(values).rename(names)

    def fullLike(
        self,
        fillValue: Union[int, float, ee.Number],
        copyProperties: Union[ee.Number, int] = 0,
        keepMask: Union[ee.Number, int] = 0,
    ) -> ee.Image:
        """Create an image with the same band names, projection and scale as the original image.

        The projection is computed on the first band, make sure all bands have the same.
        The procduced image can also copy the properties of the original image and keep the mask.

        Parameters:
            fillValue: The value to fill the image with.
            copyProperties: If True, the properties of the original image will be copied to the new one.
            keepMask: If True, the mask of the original image will be copied to the new one.

        Returns:
            An image with the same band names, projection and scale as the original image.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image.geetools.fullLike(0)
                print(image.bandNames().getInfo())
        """
        keepMask, copyProperties = ee.Number(keepMask), ee.Number(copyProperties)
        footprint, bandNames = self._obj.geometry(), self._obj.bandNames()
        fillValue = ee.List.repeat(fillValue, bandNames.size())
        image = (
            self.full(fillValue, bandNames)
            .reproject(self._obj.select(0).projection())
            .clip(footprint)
        )
        withProperties = image.copyProperties(self._obj)
        image = ee.Algorithms.If(copyProperties, withProperties, image)
        withMask = ee.Image(image).updateMask(self._obj.mask())
        image = ee.Algorithms.If(keepMask, withMask, image)
        return ee.Image(image)

    def reduceBands(
        self,
        reducer: Union[str, ee.String],
        bands: Union[list, ee.List] = [],
        name: Union[str, ee.String] = "",
    ) -> ee.Image:
        """Reduce the image using the selected reducer and adding the result as a band using the selected name.

        Args:
            bands: The bands to reduce
            reducer: The reducer to use
            name: The name of the new band

        Returns:
            The image with the new reduced band added

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image.geetools.reduceBands("mean", ['B1', 'B2'])
                print(image.bandNames().getInfo())
        """
        # the reduce method only accept client side string
        if not isinstance(reducer, str):
            raise TypeError("reducer must be a Python string")

        bands, name = ee.List(bands), ee.String(name)
        bands = ee.Algorithms.If(bands.size().eq(0), self._obj.bandNames(), bands)
        name = ee.Algorithms.If(name.equals(ee.String("")), reducer, name)
        reduceImage = self._obj.select(ee.List(bands)).reduce(reducer).rename([name])
        return self._obj.addBands(reduceImage)

    def negativeClip(
        self, geometry: Union[ee.FeatureCollection, ee.Geometry]
    ) -> ee.Image:
        """The opposite of the clip method.

        The inside of the geometry will be masked from the image.

        Args:
            geometry: The geometry to mask from the image.

        Returns:
            The image with the geometry masked.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                src, bands = "COPERNICUS/S2_SR_HARMONIZED", ["B1", "B2", "B3"]
                vatican = ee.Geometry.Point([12.4534, 41.9033]).buffer(1)

                image = ee.ImageCollection(src).filterBounds(vatican).first().select(bands)
                image = image.geetools.negativeClip(vatican)
                print(image.reduceRegion(ee.Reducer.mean(), vatican, 1).getInfo())
        """
        return self._obj.updateMask(self._obj.clip(geometry).mask().Not())

    def format(
        self,
        string: Union[str, ee.String],
        dateFormat: Union[str, ee.String] = "yyyy-MM-dd",
    ) -> ee.String:
        """Create a string from using the given pattern and using the image properties.

        The ``system_date`` property is special cased to fit the dateFormat parameter.

        Args:
            string: The pattern to use for the string
            dateFormat: The date format to use for the system_date property

        Returns:
            The string corresponding to the image

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                string = image.geetools.format('this is the image date: {system_date}')
                print(string.getInfo())
        """
        dateFormat, string = ee.String(dateFormat), ee.String(string)

        patternList = string.match(r"\{([^}]+)\}", "g")

        def replaceProperties(p, s):
            p = ee.String(p)
            prop = self._obj.get(p.slice(1, -1))
            date = self._obj.date().format(dateFormat)
            prop = ee.Algorithms.If(p.equals("{system_date}"), date, prop)
            # return ee.String(s).cat(date)
            return ee.String(s).replace(p, ee.String(prop))

        return patternList.iterate(replaceProperties, string)

    def gauss(self, band: Union[ee.String, str] = "") -> ee.Image:
        """Apply a gaussian filter to the image.

        We apply the following function to the image: "exp(((val-mean)**2)/(-2*(std**2)))"
        where val is the value of the pixel, mean is the mean of the image, std is the standard deviation of the image.

        See the `Gaussian filter <https://en.wikipedia.org/wiki/Gaussian_function>`_ Wikipedia page for more information.

        Args:
            band: The band to apply the gaussian filter to. If empty, the first one is selected.

        Returns:
            The image with the gaussian filter applied.An single band image with the gaussian filter applied.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").first()
                image = image.geetools.gauss()
                print(image.bandNames().getInfo())
        """
        band = ee.String(band) if band else ee.String(self._obj.bandNames().get(0))
        image = self._obj.select(band)

        kwargs = {"geometry": image.geometry(), "bestEffort": True}
        mean = image.reduceRegion(ee.Reducer.mean(), **kwargs).get(band)
        std = image.reduceRegion(ee.Reducer.stdDev(), **kwargs).get(band)

        return image.expression(
            "exp(((val-mean)**2)/(-2*(std**2)))",
            {
                "val": image,
                "mean": ee.Image.constant(mean),
                "std": ee.Image.constant(std),
            },
        ).rename(band.cat("_gauss"))

    def doyToDate(
        self,
        year,
        dateFormat: Union[str, ee.String] = "yyyyMMdd",
        band: Union[ee.String, str] = "",
    ) -> ee.Image:
        """Convert the DOY band to a date band.

        This method only work with date formats that can be converted to numbers as earthengine images don't accept string bands.

        Args:
            year: The year to use for the date
            dateFormat: The date format to use for the date band
            band: The band to use as DOY band. If empty, the first one is selected.

        Returns:
            The original image with the DOY band converted to a date band.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.Image.random().multiply(365).toInt()
                vatican = ee.Geometry.Point([12.4534, 41.9033]).buffer(1)

                image = image.geetools.doyToDate(2023)
                print(image.reduceRegion(ee.Reducer.min(), vatican, 1).getInfo())
        """
        year = ee.Number(year)
        band = ee.String(band) if band else ee.String(self._obj.bandNames().get(0))
        dateFormat = ee.String(dateFormat)

        doyList = ee.List.sequence(0, 365)
        remapList = doyList.map(
            lambda d: ee.Number.parse(
                ee.Date.fromYMD(year, 1, 1).advance(d, "day").format(dateFormat)
            )
        )
        return self._obj.remap(doyList, remapList, bandName=band).rename(band)

    def repeat(self, band, repeats: Union[ee.Number, int]) -> ee.image:
        """Repeat a band of the image.

        Args:
            band: The band to repeat
            repeats: The number of times to repeat the band

        Returns:
            The image with the band repeated

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").first()
                image = image.geetools.repeat('B1', 2)
                print(image.bandNames().getInfo())
        """
        band, repeats = ee.String(band), ee.Number(repeats).toInt()

        sequence = ee.List.sequence(1, repeats)
        image = self._obj.select(band)

        def addBand(n, i):
            name = band.cat("_").cat(ee.Number(n).toInt().format())
            return ee.Image(i).addBands(image.rename(name))

        return ee.Image(sequence.iterate(addBand, self._obj))

    def histogramMatch(self, target):
        """Match the histogram of the image to the target image.

        The target images must use the same band names as the source one.
        See the following article for more details: https://medium.com/google-earth/histogram-matching-c7153c85066d

        Args:
            target: The target image to match the histogram to

        Returns:
            The image with the histogram matched to the target image

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                vatican = ee.Geometry.Point([12.4534, 41.9033]).buffer(1)
                image = (
                    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                    .filterBounds(vatican)
                    .filterDate("2023-06-01", "2023-06-30")
                    .first()
                    .select("B4", "B3", "B2")
                    .rename("R", "G", "B")
                )
                target = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                    .filterBounds(vatican)
                    .filterDate("2023-06-01", "2023-06-30")
                    .first()
                    .select("SR_B4", "SR_B3", "SR_B2")
                    .rename("R", "G", "B")
                )
                image = image.geetools.histogramMatch(target)
                print(image.bandNames().getInfo())
        """
        bands = self._obj.bandNames()

        # get the histogram of the source and target images
        kwargs = {
            "reducer": ee.Reducer.autoHistogram(maxBuckets=256, cumulative=True),
            "geometry": self._obj.geometry(),
            "bestEffort": True,
        }
        sourceHistogram = self._obj.reduceRegion(**kwargs)
        targetHistogram = target.updateMask(self._obj.mask()).reduceRegion(**kwargs)

        # Create a lookup table to make sourceHist match targetHist.
        def lookup(sourceHist, targetHist):
            # Split the histograms by column and normalize the counts.
            sourceValues = sourceHist.slice(1, 0, 1).project([0])
            sourceCounts = sourceHist.slice(1, 1, 2).project([0])
            sourceCounts = sourceCounts.divide(sourceCounts.get([-1]))

            targetValues = targetHist.slice(1, 0, 1).project([0])
            targetCounts = targetHist.slice(1, 1, 2).project([0])
            targetCounts = targetCounts.divide(targetCounts.get([-1]))

            # Find first position in target where targetCount >= srcCount[i], for each i.
            lookup = sourceCounts.toList().map(
                lambda n: targetValues.get(targetCounts.gte(n).argmax())
            )

            return {"x": sourceValues.toList(), "y": lookup}

        matchedList = bands.map(
            lambda b: (
                self._obj.select(ee.String(b)).interpolate(
                    **lookup(sourceHistogram.getArray(b), targetHistogram.getArray(b))
                )
            )
        )

        return ee.ImageCollection(matchedList).toBands().rename(bands)

    def removeZeros(self) -> ee.Image:
        """Return an image array with non-zero values extracted from each band.

        This function processes a multi-band image array, where each band represents different data.
        It removes zero values from each band independently and then combines the non-zero values from all bands into a single image.
        The resulting image may have inconsistent array lengths for each pixel, as the number of zero values removed can vary across bands.

        Returns:
            The image with the zero values removed from each band.

        Example:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                vatican = ee.Geometry.Point([12.4534, 41.9033]).buffer(1)
                image = ee.Image([0, 1, 2]).toArray()
                image = image.geetools.removeZeros()
                values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
                print(values.getInfo())
        """
        bands = self._obj.bandNames()

        def remove(band):
            image = self._obj.select([band])
            isZero = image.divide(image)
            countZeros = isZero.arrayReduce(ee.Reducer.sum(), [0]).multiply(-1)
            nbZeros = countZeros.arrayProject([0]).arrayFlatten([["n"]]).toInt()
            return image.arraySort().arraySlice(0, nbZeros)

        return ee.ImageCollection(bands.map(remove)).toBands().rename(bands)

    def interpolateBands(
        self, src: Union[list, ee.List], to: Union[list, ee.List]
    ) -> ee.Image:
        """Interpolate bands from the "src" value range to the "to" value range.

        The Interpolation is performed linearly using the "extrapolate" option of the "interpolate" method.

        Args:
            src: The source value range
            to: The target value range

        Returns:
            The image with the interpolated bands

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                vatican = ee.Geometry.Point([12.4534, 41.9033]).buffer(1)
                image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(vatican).first()
                image = image.select(["B4", "B3", "B2"]).geetools.interpolateBands([0, 3000], [0, 30])
                values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
                print(values.getInfo())
        """
        bands = self._obj.bandNames()
        src, to = ee.List(src), ee.List(to)

        def interpolate(band):
            original = self._obj.select([band])
            normalized = original.unitScale(src.get(0), src.get(1))
            return normalized.interpolate([0, 1], to)

        return ee.ImageCollection(bands.map(interpolate)).toBands().rename(bands)

    def isletMask(self, offset: Union[ee.Number, float, int]) -> ee.Image:
        """Compute the islet mask from an image.

        An islet is a set of non-masked pixels connected together by their edges of very small surface. The user define the offset of the island size and we compute the max number of pixels to improve computation speed. The inpt Image needs to be a single band binary image.

        Args:
            offset: The limit of the islet size in square metters

        Returns:
            The island mask

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                image = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").first()
                mask = image.select('SCL').eq(4)
                mask = mask.geetools.islandMask(100)
                print(mask.bandNames().getInfo())
        """
        offset = ee.Number(offset)
        scale = self._obj.projection().nominalScale()
        pixelsLimit = offset.multiply(2).sqrt().divide(scale).max(ee.Number(2)).toInt()
        area = ee.Image.pixelArea().rename("area")
        isletArea = (
            self._obj.select(0)
            .mask()
            .toInt()
            .connectedPixelCount(pixelsLimit)
            .multiply(area)
        )
        return isletArea.lt(offset).rename("mask").selfMask()
