"""Toolbox for the ``ee.Image`` class."""
from __future__ import annotations

from typing import Optional

import ee
import ee_extra
import ee_extra.Algorithms.core

from geetools.accessors import register_class_accessor
from geetools.types import (
    ee_dict,
    ee_geomlike,
    ee_int,
    ee_list,
    ee_number,
    ee_str,
    number,
)


@register_class_accessor(ee.Image, "geetools")
class ImageAccessor:
    """Toolbox for the ``ee.Image`` class."""

    def __init__(self, obj: ee.Image):
        """Initialize the Image class."""
        self._obj = obj

    # -- band manipulation -----------------------------------------------------
    def addDate(self) -> ee.Image:
        """Add a band with the date of the image in the provided format.

        The date is stored as a Timestamp in millisecond in a band "date".

        Returns:
            The image with the date band added.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image = image.geetools.addDate()
                date = image.select('date')
                buffer = ee.Geometry.Point([12.4534, 41.9033]).buffer(100)
                value = date.reduceRegion(ee.Reducer.first(), buffer, 10).get("date")
                ee.Date(value).format('YYYY-MM-dd').getInfo()
        """
        date = self._obj.date().millis()
        return self._obj.addBands(ee.Image.constant(date).rename("date"))

    def addSuffix(self, suffix: ee_str, bands: ee_list = []) -> ee.Image:
        """Add a suffix to the image selected band.

        Add a suffix to the selected band. If no band is specified, the suffix is added to all bands.

        Parameters:
            suffix: The suffix to add to the band.
            bands: The bands to add the suffix to. If None, all bands are selected.

        Returns:
            The image with the suffix added to the selected bands.

        Examples:
            .. code-block:: python

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

    def addPrefix(self, prefix: ee_str, bands: ee_list = []):
        """Add a prefix to the image selected band.

        Add a prefix to the selected band. If no band is specified, the prefix is added to all bands.

        Parameters:
            prefix: The prefix to add to the band.
            bands: The bands to add the prefix to. If None, all bands are selected.

        Returns:
            The image with the prefix added to the selected bands.

        Examples:
            .. code-block:: python

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

    def rename(self, names: ee_dict) -> ee.Image:
        """Rename the bands of the image based on a dictionary.

        It's the same function as the one from GEE but it takes a dictionary as input.
        Keys are the old names and values are the new names.

        Parameters:
            names: The new names of the bands.

        Returns:
            The image with the new band names.

        Examples:
            .. code-block:: python

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

    def remove(self, bands: ee_list) -> ee.Image:
        """Remove bands from the image.

        Parameters:
            bands: The bands to remove.

        Returns:
            The image without the specified bands.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                src = 'COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM'
                image = ee.Image(src).select(['B1', 'B2', 'B3'])
                image = image.geetools.remove(['B1', 'B2'])
                print(image.bandNames().getInfo())
        """
        bands = self._obj.bandNames().removeAll(ee.List(bands))
        return self._obj.select(bands)

    def doyToDate(
        self,
        year,
        dateFormat: ee_str = "yyyyMMdd",
        band: ee_str = "",
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
            .. code-block:: python

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

    # -- the rest --------------------------------------------------------------

    def getValues(self, point: ee.Geometry.Point, scale: ee_int = 0) -> ee.Dictionary:
        """Get the value of the image at the given point using specified geometry.

        The result is presented as a dictionary where the keys are the bands name and the value the mean value of the band at the given point.

        Parameters:
            point: The geometry to get the value from.

        Returns:
            A dictionary with the band names and the value at the given point.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                point = ee.Geometry.Point([11.0, 45.0])
                value = image.geetools.getValues(point, 10)
                print(value.getInfo())
        """
        scale = self._obj.select(0).projection().nominalScale() if scale == 0 else ee.Number(scale)
        return self._obj.reduceRegion(ee.Reducer.mean(), point, scale)

    def minScale(self) -> ee.Number:
        """Return the minimum scale of the image.

        It will be looking at all bands available so Select specific values before using this method.

        Returns:
            The minimum scale of the image.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM')
                image.geetools.minScale().getInfo()
        """
        bandNames = self._obj.bandNames()
        scales = bandNames.map(lambda b: self._obj.select(ee.String(b)).projection().nominalScale())
        return ee.Number(scales.sort().get(0))

    def merge(self, images: ee_list) -> ee.Image:
        """Merge images into a single image.

        Parameters:
            images: The images to merge.

        Returns:
            The merged image.

        Examples:
            .. code-block:: python

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

    def toGrid(
        self,
        size: ee_int = 1,
        band: ee_str = "",
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
            .. code-block:: python

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
        self, fc: ee.FeatureCollection, keepProperties: ee_int = 1
    ) -> ee.ImageCollection:
        """Clip an image to a FeatureCollection.

        The image will be clipped to every single features of the featureCollection as one independent image.

        Parameters:
            fc: The featureCollection to clip to.
            keepProperties: If True, the properties of the featureCollection will be added to the clipped image.

        Returns:
            The clipped imageCollection.

        Examples:
            .. code-block:: python

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
        radius: ee_int = 1.5,
        kernelType: ee_str = "square",
        units: ee_str = "pixels",
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
            .. code-block:: python

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
        values: ee_list = [0],
        names: ee_list = ["constant"],
    ) -> ee.Image:
        """Create an image with the given values and names.

        Parameters:
            values: The values to initialize the image with. If one value is given, it will be used for all bands.
            names: The names of the bands. By default it uses the earthen engine default value, "constant".

        Returns:
            An image with the given values and names.

        Examples:
            .. code-block:: python

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
        fillValue: ee_number,
        copyProperties: ee_int = 0,
        keepMask: ee_int = 0,
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
            .. code-block:: python

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
        reducer: str,
        bands: ee_list = [],
        name: ee_str = "",
    ) -> ee.Image:
        """Reduce the image using the selected reducer and adding the result as a band using the selected name.

        Args:
            bands: The bands to reduce
            reducer: The reducer to use
            name: The name of the new band

        Returns:
            The image with the new reduced band added

        Examples:
            .. code-block:: python

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

    def negativeClip(self, geometry: ee_geomlike) -> ee.Image:
        """The opposite of the clip method.

        The inside of the geometry will be masked from the image.

        Args:
            geometry: The geometry to mask from the image.

        Returns:
            The image with the geometry masked.

        Examples:
            .. code-block:: python

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
        string: ee_str,
        dateFormat: ee_str = "yyyy-MM-dd",
    ) -> ee.String:
        """Create a string from using the given pattern and using the image properties.

        The ``system_date`` property is special cased to fit the dateFormat parameter.

        Args:
            string: The pattern to use for the string
            dateFormat: The date format to use for the system_date property

        Returns:
            The string corresponding to the image

        Examples:
            .. code-block:: python

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

    def gauss(self, band: ee_str = "") -> ee.Image:
        """Apply a gaussian filter to the image.

        We apply the following function to the image: "exp(((val-mean)**2)/(-2*(std**2)))"
        where val is the value of the pixel, mean is the mean of the image, std is the standard deviation of the image.

        See the `Gaussian filter <https://en.wikipedia.org/wiki/Gaussian_function>`_ Wikipedia page for more information.

        Args:
            band: The band to apply the gaussian filter to. If empty, the first one is selected.

        Returns:
            The image with the gaussian filter applied.An single band image with the gaussian filter applied.

        Examples:
            .. code-block:: python

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

    def repeat(self, band, repeats: ee_int) -> ee.image:
        """Repeat a band of the image.

        Args:
            band: The band to repeat
            repeats: The number of times to repeat the band

        Returns:
            The image with the band repeated

        Examples:
            .. code-block:: python

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

    def removeZeros(self) -> ee.Image:
        """Return an image array with non-zero values extracted from each band.

        This function processes a multi-band image array, where each band represents different data.
        It removes zero values from each band independently and then combines the non-zero values from all bands into a single image.
        The resulting image may have inconsistent array lengths for each pixel, as the number of zero values removed can vary across bands.

        Returns:
            The image with the zero values removed from each band.

        Example:
            .. code-block:: python

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

    def interpolateBands(self, src: ee_list, to: ee_list) -> ee.Image:
        """Interpolate bands from the "src" value range to the "to" value range.

        The Interpolation is performed linearly using the "extrapolate" option of the "interpolate" method.

        Args:
            src: The source value range
            to: The target value range

        Returns:
            The image with the interpolated bands

        Examples:
            .. code-block:: python

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

    def isletMask(self, offset: ee_number) -> ee.Image:
        """Compute the islet mask from an image.

        An islet is a set of non-masked pixels connected together by their edges of very small surface. The user define the offset of the island size and we compute the max number of pixels to improve computation speed. The inpt Image needs to be a single band binary image.

        Args:
            offset: The limit of the islet size in square metters

        Returns:
            The island mask

        Examples:
            .. code-block:: python

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
            self._obj.select(0).mask().toInt().connectedPixelCount(pixelsLimit).multiply(area)
        )
        return isletArea.lt(offset).rename("mask").selfMask()

    # -- ee-extra wrapper ------------------------------------------------------
    def index_list(cls) -> dict:
        """Return the list of indices implemented in this module.

        Returns:
            List of indices implemented in this module

        Examples:
            .. code-block:: python

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
        G: number = 2.5,
        C1: number = 6.0,
        C2: number = 7.5,
        L: number = 1.0,
        cexp: number = 1.16,
        nexp: number = 2.0,
        alpha: number = 0.1,
        slope: number = 1.0,
        intercept: number = 0.0,
        gamma: number = 1.0,
        omega: number = 2.0,
        beta: number = 0.05,
        k: number = 0.0,
        fdelta: number = 0.581,
        kernel: str = "RBF",
        sigma: str = "0.5 * (a + b)",
        p: number = 2.0,
        c: number = 1.0,
        lambdaN: number = 858.5,
        lambdaR: number = 645.0,
        lambdaG: number = 555.0,
        online: number = False,
    ) -> ee.Image:
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
            .. code-block:: python

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

    def getScaleParams(self) -> dict:
        """Gets the scale parameters for each band of the image.

        Returns:
            Dictionary with the scale parameters for each band.


        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('MODIS/006/MOD11A2').first().geetools.getScaleParams()
        """
        return ee_extra.STAC.core.getScaleParams(self._obj)

    def getOffsetParams(self) -> dict:
        """Gets the offset parameters for each band of the image.

        Returns:
            Dictionary with the offset parameters for each band.

        Examples:
            .. code-block:: python

            import ee
            import geetools

            ee.Initialize()

            ee.ImageCollection('MODIS/006/MOD11A2').first().getOffsetParams()
        """
        return ee_extra.STAC.core.getOffsetParams(self._obj)

    def scaleAndOffset(self) -> ee.Image:
        """Scales bands on an image according to their scale and offset parameters.

        Returns:
            Scaled image.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                S2 = ee.ImageCollection('COPERNICUS/S2_SR').first().scaleAndOffset()
        """
        return ee_extra.STAC.core.scaleAndOffset(self._obj)

    def preprocess(self, **kwargs) -> ee.Image:
        """Pre-processes the image: masks clouds and shadows, and scales and offsets the image.

        Parameters:
            **kwargs: Keywords arguments for ``maskClouds`` method.

        Returns:
            Pre-processed image.

        Examples:
            .. code-block:: python

            import ee
            import geetools

            ee.Initialize()
            S2 = ee.ImageCollection('COPERNICUS/S2_SR').first().preprocess()
        """
        return ee_extra.QA.pipelines.preprocess(self._obj, **kwargs)

    def getSTAC(self) -> dict:
        """Gets the STAC of the image.

        Returns:
            STAC of the image.

        Examples:
            .. code-block:: python

            import ee
            import geetools

            ee.Initialize()

            ee.ImageCollection('COPERNICUS/S2_SR').first().getSTAC()
        """
        return ee_extra.STAC.core.getSTAC(self._obj)

    def getDOI(self) -> str:
        """Gets the DOI of the image, if available.

        Returns:
            DOI of the ee.Image dataset.

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').first().getDOI()
        """
        return ee_extra.STAC.core.getDOI(self._obj)

    def getCitation(self) -> str:
        """Gets the citation of the image, if available.

        Returns:
            Citation of the ee.Image dataset.

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').first().getCitation()
        """
        return ee_extra.STAC.core.getCitation(self._obj)

    def panSharpen(self, method: str = "SFIM", qa: str = "", **kwargs) -> ee.Image:
        """Apply panchromatic sharpening to the Image.

        Optionally, run quality assessments between the original and sharpened Image to
        measure spectral distortion and set results as properties of the sharpened Image.

        Parameters:
        method: The sharpening algorithm to apply. Current options are "SFIM" (Smoothing Filter-based Intensity Modulation), "HPFA" (High Pass Filter Addition), "PCS" (Principal Component Substitution), and "SM" (simple mean). Different sharpening methods will produce different quality sharpening results in different scenarios.
        qa: One or more optional quality assessment names to apply after sharpening. Results will be stored as image properties with the pattern `geetools:metric`, e.g. `geetools:RMSE`.
        **kwargs: Keyword arguments passed to ee.Image.reduceRegion() such as "geometry", "maxPixels", "bestEffort", etc. These arguments are only used for PCS sharpening and quality assessments.

        Returns:
            The Image with all sharpenable bands sharpened to the panchromatic resolution and quality assessments run and set as properties.

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                source = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_047027_20160819")
                sharp = source.panSharpen(method="HPFA", qa=["MSE", "RMSE"], maxPixels=1e13)
        """
        return ee_extra.Algorithms.core.panSharpen(
            img=self._obj, method=method, qa=qa, prefix="geetools", **kwargs
        )

    def tasseledCap(self) -> ee.Image:
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
            self: ee.Image to calculate tasseled cap components for. Must belong to a supported platform.

        Returns:
            Image with the tasseled cap components as new bands.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                img = img.tasseledCap()
        """
        return ee_extra.Spectral.core.tasseledCap(self._obj)

    def matchHistogram(
        self,
        target: ee.Image,
        bands: dict,
        geometry: Optional[ee.Geometry] = None,
        maxBuckets: int = 256,
    ) -> ee.Image:
        """Adjust the image's histogram to match a target image.

        Parameters:
        target: Image to match.
        bands: A dictionary of band names to match, with source bands as keys and target bands as values.
        geometry: The region to match histograms in that overlaps both images. If none is provided, the geometry of the source image will be used.
        maxBuckets: The maximum number of buckets to use when building histograms. Will be rounded to the nearest power of 2.

        Returns:
            The adjusted image containing the matched source bands.

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                source = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_047027_20160819")
                target = ee.Image("LANDSAT/LE07/C01/T1_TOA/LE07_046027_20150701")
                bands = {
                    "B4": "B3",
                    "B3": "B2",
                    "B2": "B1"
                }
                matched = source.matchHistogram(target, bands)
        """
        return ee_extra.Spectral.core.matchHistogram(
            source=self._obj,
            target=target,
            bands=bands,
            geometry=geometry,
            maxBuckets=maxBuckets,
        )

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
    ):
        """Masks clouds and shadows in an image (valid just for Surface Reflectance products).

        Parameters:
            self: Image to mask.
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
                    .first()
                    .maskClouds(prob = 75,buffer = 300,cdi = -0.5))
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
