"""Toolbox for the :py:class:`ee.Image` class."""
from __future__ import annotations

from typing import Any, Optional

import ee
import ee_extra
import ee_extra.Algorithms.core
import geopandas as gpd
import numpy as np
import requests
import xarray
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from pyproj import CRS, Transformer
from xee.ext import REQUEST_BYTE_LIMIT

from .accessors import register_class_accessor
from .utils import plot_data


@register_class_accessor(ee.Image, "geetools")
class ImageAccessor:
    """Toolbox for the :py:class:`ee.Image` class."""

    def __init__(self, obj: ee.Image):
        """Initialize the Image class."""
        self._obj = obj

    # -- band manipulation -----------------------------------------------------
    def addDate(self, format: str | ee.String = "") -> ee.Image:
        """Add a band with the date of the image in the provided format.

        If no format is provided, the date is stored as a Timestamp in millisecond in a band "date". If format band is provided, the date is store in an int8 band with the date in the provided format. This format needs to be a string that can be converted to a number.
        If not an error will be thrown.

        Args:
            format: A date pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html

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
        # parse the inputs
        isMillis = ee.String(format).equals(ee.String(""))
        format = ee.String(format) if format else ee.String("YYYYMMdd")

        # extract the date from the object and create a image band from it
        date = self._obj.date()
        date = ee.Algorithms.If(isMillis, date.millis(), ee.Number.parse(date.format(format)))
        dateBand = ee.Image.constant(ee.Number(date)).rename("date")

        return self._obj.addBands(dateBand)

    def addSuffix(self, suffix: str | ee.String, bands: list | ee.List = []) -> ee.Image:
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

    def addPrefix(self, prefix: str | ee.String, bands: list | ee.List = []) -> ee.Image:
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

    def rename(self, names: dict | ee.Dictionary) -> ee.Image:
        """Rename the bands of the image based on a dictionary.

        It's the same function as the one from GEE, but it takes a dictionary as input.
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

    def remove(self, bands: list | ee.List) -> ee.Image:
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
        year: int | float | ee.Number,
        dateFormat: str | ee.String = "yyyyMMdd",
        band: str | ee.String = "",
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

    def getValues(self, point: ee.Geometry, scale: int | ee.Number = 0) -> ee.Dictionary:
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

    def merge(self, images: list | ee.List) -> ee.Image:
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
        size: int | ee.Number = 1,
        band: str | ee.String = "",
        geometry: ee.Geometry | None = None,
    ) -> ee.FeatureCollection:
        """Convert an image to a grid of polygons.

        Based on the size given by the user, the tool will build a grid of size*pixelSize x size * pixelSize cells.
        Each cell will be a polygon. Note that for images that have multiple scale depending on the band,
        we will use the first one or the one stated in the parameters.

        Parameters:
            size: The size of the grid. It will be size * pixelSize x size * pixelSize cells.
            band: The band to burn into the grid.
            geometry: The geometry to use as reference for the grid. If None, the image footprint will be used.

        Returns:
            The grid as a :py:class:`FeatureCollection`.

        Note:
            The method has a known bug when the projection of the image is different from 3857. As we use a buffer, the grid cells can slightly overlap. Feel free to open an Issue and contribute if you feel it needs improvements.

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
        self, fc: ee.FeatureCollection, keepProperties: int | ee.Number = 1
    ) -> ee.ImageCollection:
        """Clip an image to a :py:class:`ee.FeatureCollection`.

        The image will be clipped to every single features of the ``featureCollection`` as one independent image.

        Parameters:
            fc: The :py:class:`ee.FeatureCollection` to clip to.
            keepProperties: If True, the properties of the :py:class:`ee.FeatureCollection` will be added to the clipped image.

        Returns:
            The clipped :py:class:`ee.ImageCollection`.

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
        radius: int | ee.Number = 1.5,
        kernelType: str | ee.String = "square",
        units: str | ee.String = "pixels",
    ) -> ee.Image:
        """Make a buffer around every masked pixel of the Image.

        The buffer will be made using the specified radius, kernelType and units and will mask surrounding pixels.

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
        values: list | ee.List = [0],
        names: list | ee.List = ["constant"],
    ) -> ee.Image:
        """Create an image with the given values and names.

        Parameters:
            values: The values to initialize the image width. If one value is given, it will be used for all bands.
            names: The names of the bands. By default, it uses the earthen engine default value, ``constant``.

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
        fillValue: float | int | ee.Number,
        copyProperties: int | ee.Number = 0,
        keepMask: int | ee.Number = 0,
        keepFootprint: int | ee.Number = 1,
    ) -> ee.Image:
        """Create an image with the same band names, projection and scale as the original image.

        The projection is computed on the first band, make sure all bands have the same.
        The produced image can also copy the properties of the original image and keep the mask.

        Parameters:
            fillValue: The value to fill the image width.
            copyProperties: If True, the properties of the original image will be copied to the new one.
            keepMask: If True, the mask of the original image will be copied to the new one.
            keepFootprint: If True, the footprint of the original image will be used to clip the new image.

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
        # function params as GEE objects
        keepMask, copyProperties = ee.Number(keepMask), ee.Number(copyProperties)
        keepFootprint = ee.Number(keepFootprint)
        # get geometry, band names and property names
        footprint, bandNames = self._obj.geometry(), self._obj.bandNames()
        properties = self._obj.propertyNames().remove(
            "system:footprint"
        )  # remove footprint as a "normal" property
        # list of values to fill the image
        fillValue = ee.List.repeat(fillValue, bandNames.size())
        # filled image
        image = self.full(fillValue, bandNames)
        # handler projection
        projected_list = bandNames.map(
            lambda b: image.select([b]).reproject(self._obj.select([b]).projection())
        )
        image = ee.ImageCollection.fromImages(projected_list).toBands().rename(bandNames)
        # handle footprint
        image_footprint = image.clip(footprint)  # sets system:footprint property
        image = ee.Image(ee.Algorithms.If(keepFootprint, image_footprint, image))
        # handle properties
        withProperties = image.copyProperties(self._obj, properties)
        image = ee.Algorithms.If(copyProperties, withProperties, image)
        # handle mask
        withMask = ee.Image(image).updateMask(self._obj.mask())
        image = ee.Image(ee.Algorithms.If(keepMask, withMask, image))
        # handle band types
        return ee.Image(image.cast(self._obj.bandTypes()))

    def reduceBands(
        self,
        reducer: str | ee.Reducer,
        bands: list | ee.List = [],
        name: str | ee.String = "",
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
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer
        reduceImage = self._obj.select(ee.List(bands)).reduce(red).rename([name])
        return self._obj.addBands(reduceImage)

    def negativeClip(self, geometry: ee.Geometry | ee.Feature | ee.FeatureCollection) -> ee.Image:
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
        string: str | ee.String,
        dateFormat: str | ee.String = "yyyy-MM-dd",
    ) -> ee.String:
        """Create a string from using the given pattern and using the image properties.

        The ``system_date`` property is special cased to fit the ``dateFormat`` parameter.

        Args:
            string: The pattern to use for the string
            dateFormat: The date format to use for the ``system_date`` property

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

    def gauss(self, band: str | ee.String = "") -> ee.Image:
        r"""Apply a gaussian filter to the image.

        We apply the following function to the image:

        .. math::
            \exp\left(\frac{(\text{val}-\text{mean})^2}{-2 \cdot (\text{std}^2)}\right)

        where :math:`\text{val}` is the value of the pixel, :math:`\text{mean}` is the mean of the image, :math:`\text{std}` is the standard deviation of the image.

        See the `Gaussian filter <https://en.wikipedia.org/wiki/Gaussian_function>`_ Wikipedia page for more information.

        Args:
            band: The band to apply the gaussian filter to. If empty, the first one is selected.

        Returns:
            The image with the gaussian filter applied. A single band image with the gaussian filter applied.

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

    def repeat(self, band, repeats: int | ee.Number) -> ee.Image:
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

    def interpolateBands(self, src: list | ee.List, to: list | ee.List) -> ee.Image:
        """Interpolate bands from the ``src`` value range to the ``to`` value range.

        The Interpolation is performed linearly using the ``extrapolate`` option of the :py:meth:`ee.Image.interpolate` method.

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

    def isletMask(self, offset: float | int | ee.Number) -> ee.Image:
        """Compute the islet mask from an image.

        An islet is a set of non-masked pixels connected together by their edges of very small surface. The user define the offset of the islet size, and we compute the max number of pixels to improve computation speed. The input Image needs to be a single band binary image.

        Args:
            offset: The limit of the islet size in square meters.

        Returns:
            The islet mask.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").first()
                mask = image.select('SCL').eq(4)
                mask = mask.geetools.isletMask(100)
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
    def index_list(cls) -> dict[str, dict]:
        """Return the list of indices implemented in this module.

        Returns:
            List of indices implemented in this module

        Examples:
            .. code-block:: python

                import ee, geetools

                ind = ee.Image.geetools.index_list()["BAIS2"]
                print(ind["long_name"])
                print(ind["formula"])
                print(ind["reference"])
        """
        url = "https://raw.githubusercontent.com/awesome-spectral-indices/awesome-spectral-indices/main/output/spectral-indices-dict.json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["SpectralIndices"]

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
        online: float | int = False,
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
            Image with the computed spectral index, or indices, as new bands.

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
            - :docstring:`ee.Image.geetools.getOffsetParams`
            - :docstring:`ee.Image.geetools.scaleAndOffset`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('MODIS/006/MOD11A2').first().geetools.getScaleParams()
        """
        return ee_extra.STAC.core.getScaleParams(self._obj)

    def getOffsetParams(self) -> dict[str, float]:
        """Gets the offset parameters for each band of the image.

        Returns:
            Dictionary with the offset parameters for each band.

        See Also:
            - :docstring:`ee.Image.geetools.getScaleParams`
            - :docstring:`ee.Image.geetools.scaleAndOffset`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                ee.ImageCollection('MODIS/006/MOD11A2').first().geetools.getOffsetParams()
        """
        return ee_extra.STAC.core.getOffsetParams(self._obj)

    def scaleAndOffset(self) -> ee.Image:
        """Scales bands on an image according to their scale and offset parameters.

        Returns:
            Scaled image.

        See Also:
            - :docstring:`ee.Image.geetools.getScaleParams`
            - :docstring:`ee.Image.geetools.getOffsetParams`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                S2 = ee.ImageCollection('COPERNICUS/S2_SR').first().geetools.scaleAndOffset()
        """
        return ee_extra.STAC.core.scaleAndOffset(self._obj)

    def preprocess(self, **kwargs) -> ee.Image:
        """Pre-processes the image: masks clouds and shadows, and scales and offsets the image.

        Parameters:
            **kwargs: Keywords arguments for :py:meth:`ee.Image.geetools.maskClouds <geetools.ee_image.ImageAccessor.maskClouds>` method.

        Returns:
            Pre-processed image.

        See Also:
            - :docstring:`ee.Image.geetools.getScaleParams`
            - :docstring:`ee.Image.geetools.getOffsetParams`
            - :docstring:`ee.Image.geetools.scaleAndOffset`
            - :docstring:`ee.Image.geetools.maskClouds`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()
                S2 = (
                    ee.ImageCollection('COPERNICUS/S2_SR').first()
                    .geetools.preprocess()
                )
        """
        return ee_extra.QA.pipelines.preprocess(self._obj, **kwargs)

    def getSTAC(self) -> dict[str, Any]:
        """Gets the STAC of the image.

        Returns:
            STAC of the image.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                ee.ImageCollection('COPERNICUS/S2_SR').first().geetools.getSTAC()
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
        collection = "_".join(assetId.split("/")[:-1])
        links = requests.get(project_catalog).json()["links"]
        collection_stac = next((i["href"] for i in links if i.get("title") == collection), None)
        if collection_stac is None:
            raise ValueError(f"Collection {collection} not found in the {project} catalog")

        return requests.get(collection_stac).json()

    def getDOI(self) -> str:
        """Gets the DOI of the image, if available.

        Returns:
            DOI of the :py:class:`ee.Image` dataset.

        See Also:
            - :docstring:`ee.Image.geetools.getCitation`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').first().geetools.getDOI()
        """
        stac = self.getSTAC()
        error_msg = "DOI not found in the STAC"
        return stac["sci:doi"] if "sci:doi" in stac else error_msg

    def getCitation(self) -> str:
        """Gets the citation of the image, if available.

        Returns:
            Citation of the :py:class:`ee.Image` dataset.

        See Also:
            - :docstring:`ee.Image.geetools.getDOI`

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                ee.ImageCollection('NASA/GPM_L3/IMERG_V06').first().geetools.getCitation()
        """
        stac = self.getSTAC()
        error_msg = "Citation not found in the STAC"
        return stac["sci:citation"] if "sci:citation" in stac else error_msg

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
                sharp = source.geetools.panSharpen(method="HPFA", qa=["MSE", "RMSE"], maxPixels=1e13)
        """
        return ee_extra.Algorithms.core.panSharpen(
            img=self._obj, method=method, qa=qa, prefix="geetools", **kwargs
        )

    def tasseledCap(self) -> ee.Image:
        """Calculates tasseled cap brightness, wetness, and greenness components.

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
            self: :py:class:`ee.Image` to calculate tasseled cap components for. Must belong to a supported platform.

        Returns:
            Image with the tasseled cap components as new bands.

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

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                img = img.geetools.tasseledCap()
        """
        return ee_extra.Spectral.core.tasseledCap(self._obj)

    def matchHistogram(
        self,
        target: ee.Image,
        bands: dict,
        geometry: ee.Geometry | None = None,
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
                matched = source.geetools.matchHistogram(target, bands)
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
        cdi: int | None = None,
    ) -> ee.Image:
        """Masks clouds and shadows in an image (valid just for Surface Reflectance products).

        Parameters:
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
                    .geetools.maskClouds(prob = 75,buffer = 300,cdi = -0.5)
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

    def removeProperties(self, properties: list | ee.List) -> ee.Image:
        """Remove a list of properties from an image.

        Args:
            properties: List of properties to remove from the image.

        Returns:
            Image with the specified properties removed.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                image = image.geetools.removeProperties(["system:time_start"])
        """
        properties = ee.List(properties)
        proxy = self._obj.multiply(1)  # drop properties
        return ee.Image(proxy.copyProperties(self._obj, exclude=properties))

    def distanceToMask(
        self,
        mask: ee.Image,
        kernel: str = "euclidean",
        radius: int = 1000,
        band_name: str | ee.String = "distance_to_mask",
    ) -> ee.Image:
        """Compute the distance from each pixel to the nearest non-masked pixel.

        Parameters:
            mask: The mask to compute the distance to.
            kernel: The kernel type to use for the distance computation default to ``"euclidean"``.
            radius: The radius of the kernel.
            band_name: The name of the band to store the distance values.

        Returns:
            The original images with the distance band added.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                centerBuffer = image.geometry().centroid().buffer(100)
                BufferMask = ee.Image.constant(1).clip(centerBuffer)
                mask = ee.Image.constant(0).where(BufferMask, 1).clip(image.geometry())
                image = image.geetools.distanceToMask(mask)
        """
        # gather the parameters
        kernel = getattr(ee.Kernel, kernel)(radius, "meters")
        bandName = ee.String(band_name)

        # compute the distance
        distance = self._obj.select(0).mask().Not().distance(kernel).rename(bandName)
        distMask = distance.mask().Not().remap([0, 1], [0, radius])
        final = distance.unmask().add(distMask)

        return self._obj.addBands(final)

    def distance(self, other: ee.Image) -> ee.Image:
        """Compute the sum of all spectral distance between two images.

        Parameters:
            other: The image to compute the distance to.

        Returns:
            and Image with the Euclidean distance between the two images for each band.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                other = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                image = image.geetools.distance(other)
        """
        # compute the distance
        distance = self._obj.subtract(other).pow(2).reduce("sum").sqrt().rename("sum_distance")

        return ee.Image(distance)

    def maskCoverRegion(
        self,
        region: ee.Geometry,
        scale: Optional[int | ee.Number] = None,
        band: Optional[str | ee.String] = None,
        proxyValue: int | ee.Number = -999,
        **kwargs,
    ) -> ee.Number:
        """Compute the coverage of masked pixels inside a Geometry.

        Parameters:
            region: The region to compute the mask coverage.
            scale: The scale of the computation. In case you need a rough estimation use a higher scale than the original from the image.
            band: The band to use. Defaults to the first band.
            proxyValue: the value to use for counting the mask and avoid confusing 0s to masked values. In most cases the user should not change this value, but in case of conflicts, choose a value that is out of the range of the image values.
            **kwargs:
                - ``maxPixels``: The maximum number of pixels to reduce.
                - ``tileScale``: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            The percentage of masked pixels within the region.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                aoi = ee.Geometry.Point([11.880190936531116, 42.0159494554553]).buffer(2000)
                image = image.geetools.maskCoverRegion(aoi)
        """
        # compute the mask cover
        image = self._obj.select(band or 0)
        scale = scale or image.projection().nominalScale()
        unmasked = image.unmask(proxyValue)
        mask = unmasked.eq(proxyValue)
        cover = mask.reduceRegion(
            ee.Reducer.frequencyHistogram(), region, scale=scale, bestEffort=True, **kwargs
        )
        # The cover result is a dictionary with each band as key (in our case the first one).
        # For each band key the number of 0 and 1 is stored in a dictionary.
        # We need to extract the number of 1 and 0 to compute the ratio which implys lots of casting.
        values = ee.Dictionary(cover.values().get(0))
        zeros, ones = ee.Number(values.get("0", 0)), ee.Number(values.get("1", 0))
        ratio = ones.divide(zeros.add(ones)).multiply(100)

        # we want to display this result as a 1 digit float
        return ratio

    def maskCoverRegions(
        self,
        collection: ee.FeatureCollection,
        scale: Optional[int | ee.Number] = None,
        band: Optional[str | ee.String] = None,
        proxyValue: int | ee.Number = -999,
        columnName: str | ee.String = "mask_cover",
        **kwargs,
    ) -> ee.FeatureCollection:
        """Compute the coverage of masked pixels inside a Geometry.

        Parameters:
            collection: The collection to compute the mask coverage (in each Feature).
            scale: The scale of the computation. In case you need a rough estimation use a higher scale than the original from the image.
            band: The band to use. Defaults to the first band.
            proxyValue: the value to use for counting the mask and avoid confusing 0s to masked values. In most cases the user should not change this value, but in case of conflicts, choose a value that is out of the range of the image values.
            columnName: name of the column that will hold the value.
            **kwargs:
                - ``tileScale``: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            The passed table with the new column containing the percentage of masked pixels within the region.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                reg = ee.Geometry.Point([11.880190936531116, 42.0159494554553]).buffer(2000)
                aoi = ee.FeatureCollection([ee.Feature(reg)])
                image = image.geetools.maskCoverRegions(aoi)
        """
        # compute the mask cover
        properties = collection.propertyNames()  # original properties
        image = self._obj.select(band or 0)
        scale = scale or image.projection().nominalScale()
        unmasked = image.unmask(proxyValue)
        mask = unmasked.eq(proxyValue)
        column = "_geetools_histo_"
        cover = mask.reduceRegions(
            collection=collection,
            reducer=ee.Reducer.frequencyHistogram().setOutputs([column]),
            scale=scale,
            **kwargs,
        )

        def compute_percentage(feat: ee.Feature) -> ee.Feature:
            histo = ee.Dictionary(feat.get(column))
            zeros, ones = ee.Number(histo.get("0", 0)), ee.Number(histo.get("1", 0))
            ratio = ones.divide(zeros.add(ones)).multiply(100)
            return feat.select(properties).set(columnName, ratio)

        return cover.map(compute_percentage)

    def maskCover(
        self,
        scale: Optional[int] = None,
        proxyValue: int = -999,
        propertyName: str = "mask_cover",
        **kwargs,
    ) -> ee.Image:
        """Compute the percentage of masked pixels inside the image.

        It will use the geometry and the first band of the image.

        Parameters:
            scale: The scale of the computation. In case you need a rough estimation use a higher scale than the original from the image.
            proxyValue: the value to use for counting the mask and avoid confusing 0s to masked values. Choose a value that is out of the range of the image values.
            propertyName: the name of the property where the value will be saved
            **kwargs:
                - ``maxPixels``: The maximum number of pixels to reduce.
                - ``tileScale``: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            The same image with the percentage of masked pixels as a property.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                aoi = ee.Geometry.Point([11.880190936531116, 42.0159494554553]).buffer(2000)
                image = image.geetools.maskCoverRegion(aoi)
        """
        region = self._obj.geometry()
        value = self.maskCoverRegion(region, scale, None, proxyValue, **kwargs)
        return self._obj.set(propertyName, value)

    def plot(
        self,
        bands: list,
        region: ee.Geometry,
        ax: Axes | None = None,
        fc: ee.FeatureCollection = None,
        cmap: str = "viridis",
        crs: str = "EPSG:4326",
        scale: float = 0.0001,  # 0.0001 is the default scale for Sentinel-2
        color="k",
    ) -> Axes:
        """Plot the image on a matplotlib axis.

        Parameters:
            bands: The bands to plot.
            region: The geometry borders to plot the image on.
            ax: The matplotlib axis to plot the image on.
            fc: a FeatureCollection object to overlay on top of the image. Default is None, it can be a different object from the region.
            cmap: The colormap to use for the image. Default is ``viridis``. can only ber used for single band images.
            crs: The coordinate reference system of the image. By default, we will use ``"EPSG:4326"``
            scale: The scale of the image.
            color: The color of the overlaid feature collection. Default is ``k`` (black).

        Examples:
            .. code-block:: python

                import ee, geetools
                import matplotlib.pyplot as plt

                ee.Initialize()

                image = ee.Image('COPERNICUS/S2_SR/20190828T151811_20190828T151809_T18GYT')
                fig, ax = plt.subplots()
                image.geetools.plot(["B4", "B3", "B2"], image.geometry(), ax)
        """
        if ax is None:
            fig, ax = plt.subplots()

        # extract the image as a xarray dataset
        ds = xarray.open_dataset(
            ee.ImageCollection([self._obj]),
            engine="ee",
            crs=crs,
            scale=scale,
            geometry=region.bounds(),
            request_byte_limit=REQUEST_BYTE_LIMIT,
        )

        # extract all the bands as dataarrays objects
        # x and y coordinates need to be transposed to match imshow requirements
        bands_da = [ds[b][0, :, :].transpose() for b in bands]

        # compute the extend of the image so the unit displayed for x and y are matching the required crs
        proj = Transformer.from_crs(CRS("EPSG:4326"), CRS(crs), always_xy=True)
        region_bounds = region.bounds().coordinates().get(0).getInfo()
        min_x, min_y = proj.transform(*region_bounds[0])
        max_x, max_y = proj.transform(*region_bounds[2])

        # set the parameters that will be use for single and multi-band display
        params = dict(extent=[min_x, max_x, min_y, max_y], origin="lower")

        # For single band image, we use the data array directly as source image
        # for multi band image, we need to stack the dataarrays to create a RGB image
        # and normalized them
        if len(bands) == 1:
            ax.imshow(bands_da[0], cmap=cmap, **params)
        else:
            da = np.dstack(bands_da)
            rgb_image = (da - np.min(da)) / (np.max(da) - np.min(da))
            ax.imshow(rgb_image, **params)

        # add the feature collection if provided
        # we need to extract the geometries and plot them
        if fc is not None:
            gdf = gpd.GeoDataFrame.from_features(fc.getInfo()["features"])
            gdf = gdf.set_crs("EPSG:4326").to_crs(crs)
            gdf.boundary.plot(ax=ax, color=color)

        # The default aspect for map plots is 'auto'; if however data are not projected (coordinates are long/lat),
        #  the aspect is by default set to 1/cos(s_y * pi/180) with s_y the y coordinate of the middle of the
        # region (the mean of the y range of bounding box) so that a long/lat square appears square in the
        # middle of the plot. This implies an Equirectangular projection.
        if CRS(crs).is_geographic:
            y_coord = np.mean([min_y, max_y])
            ax.set_aspect(1 / np.cos(y_coord * np.pi / 180))
        else:
            ax.set_aspect("auto")

        # make sure the canvas is only rendered once.
        ax.figure.canvas.draw_idle()

        return ax

    @classmethod
    def fromList(cls, images: ee.List | list) -> ee.Image:
        """Create a single image by passing a list of images.

        Warning: The bands cannot have repeated names, if so, it will throw an error (see examples).

        Parameters:
            images: a list of ee.Image

        Returns:
            A single :py:class:`ee.Image` with one band per image in the passed list

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                sequence = ee.List([1, 2, 3])
                images = sequence.map(lambda i: ee.Image(ee.Number(i)).rename(ee.Number(i).int().format()))
                image = ee.Image.geetools.fromList(images)
                print(image.bandNames().getInfo())

            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                sequence = ee.List([1, 2, 2, 3])
                images = sequence.map(lambda i: ee.Image(ee.Number(i)).rename(ee.Number(i).int().format()))
                image = ee.Image.geetools.fromList(images)
                print(image.bandNames().getInfo())
        """
        bandNames = ee.List(images).map(lambda i: ee.Image(i).bandNames()).flatten()
        ic = ee.ImageCollection.fromImages(images)
        return ic.toBands().rename(bandNames)

    def byBands(
        self,
        regions: ee.FeatureCollection,
        reducer: str | ee.Reducer = "mean",
        bands: list = [],
        regionId: str = "system:index",
        labels: list = [],
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Compute a reducer for each band of the image in each region.

        This method is returning a dictionary with all the bands as keys and their reduced value in each region as values.

        .. code-block::

            {
                "band1": {"feature1": value1, "feature2": value2, ...},
                "band2": {"feature1": value1, "feature2": value2, ...},
                ...
            }

        Parameters:
            regions: The regions to compute the reducer in.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            regionId: The property used to label region. Defaults to ``"system:index"``.
            labels: The labels to use for the output dictionary. Default to the band names.
            bands: The bands to compute the reducer on. Default to all bands.
            scale: The scale to use for the computation. Default is 10000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            A dictionary with all the bands as keys and their values in each region as a list.

        See Also:
            - :docstring:`ee.Image.geetools.byRegions`
            - :docstring:`ee.Image.geetools.plot_by_bands`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ecoregions = ee.FeatureCollection("projects/google/charts_feature_example").select(["label", "value","warm"])
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()
                d = normClim.geetools.byBands(ecoregions, ee.Reducer.mean(), scale=10000)
                print(d.getInfo())
        """
        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = regions.aggregate_array(regionId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))

        # get the bands to be used in the reducer
        eeBands = ee.List(bands) if len(bands) else self._obj.bandNames()

        # retrieve the label to use for each bands if provided
        eeLabels = ee.List(labels) if len(labels) else eeBands

        # by default for 1 band image, the reducers are renaming the output band. To ensure it keeps
        #  the original band name we add setOutputs that is ignored for multi band images.
        # This is currently hidden because of https://issuetracker.google.com/issues/374285504
        # It will have no impact on most of the cases as plt_hist should be used for single band images
        # reducer = reducer.setOutputs(labels)
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer

        # retrieve the reduce bands for each feature
        image = self._obj.select(eeBands).rename(eeLabels)
        fc = image.reduceRegions(
            collection=regions,
            reducer=red,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        )

        # extract the data as a list of dictionaries (one for each label) aggregating
        # the values for each feature
        values = eeLabels.map(lambda b: ee.Dictionary.fromLists(features, fc.aggregate_array(b)))

        return ee.Dictionary.fromLists(eeLabels, values)

    def byRegions(
        self,
        regions: ee.FeatureCollection,
        reducer: str | ee.Reducer = "mean",
        bands: list = [],
        regionId: str = "system:index",
        labels: list = [],
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> ee.Dictionary:
        """Compute a reducer in each region of the image for eah band.

        This method is returning a dictionary with all the features as keys and their reduced value for each band as values.

        .. code-block::

            {
                "feature1": {"band1": value1, "band2": value2, ...},
                "feature2": {"bands1": value1, "band2": value2, ...},
                ...
            }

        Parameters:
            regions: The regions to compute the reducer in.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            regionId: The property used to label region. Defaults to ``"system:index"``.
            labels: The labels to use for the output dictionary. Default to the band names.
            bands: The bands to compute the reducer on. Default to all bands.
            scale: The scale to use for the computation. Default is 10000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.


        Returns:
            A dictionary with all the bands as keys and their values in each region as a list.

        See Also:
            - :docstring:`ee.Image.geetools.byBands`
            - :docstring:`ee.Image.geetools.plot_by_regions`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ecoregions = ee.FeatureCollection("projects/google/charts_feature_example").select(["label", "value","warm"])
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()
                d = normClim.geetools.byRegions(ecoregions, ee.Reducer.mean(), scale=10000)
                print(d.getInfo())
        """
        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = regions.aggregate_array(regionId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))

        # get the bands to be used in the reducer
        bands = ee.List(bands) if len(bands) else self._obj.bandNames()

        # retrieve the label to use for each bands if provided
        labels = ee.List(labels) if len(labels) else bands

        # by default for 1 band image, the reducers are renaming the output band. To ensure it keeps
        #  the original band name we add setOutputs that is ignored for multi band images.
        # This is currently hidden because of https://issuetracker.google.com/issues/374285504
        # It will have no impact on most of the cases as plt_hist should be used for single band images
        # reducer = reducer.setOutputs(labels)
        red = getattr(ee.Reducer, reducer)() if isinstance(reducer, str) else reducer

        # retrieve the reduce bands for each feature
        image = self._obj.select(bands).rename(labels)
        fc = image.reduceRegions(
            collection=regions,
            reducer=red,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        )

        # extract the data as a list of dictionaries (one for each label) aggregating
        # we are force to turn the fc into a list because GEE don't accept to map a featureCollection
        # into something else (in our a case a dict)
        fcList = fc.toList(fc.size())
        values = fcList.map(lambda f: ee.Feature(f).select(labels).toDictionary())

        return ee.Dictionary.fromLists(features, values)

    def plot_by_regions(
        self,
        type: str,
        regions: ee.FeatureCollection,
        reducer: str | ee.Reducer = "mean",
        bands: list = [],
        regionId: str = "system:index",
        labels: list = [],
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced values for each region.

        Each region will be plotted using the ``regionId`` as x-axis label defaulting to "system:index" if not provided.
        If no ``bands`` are provided, all bands will be plotted.
        If no ``labels`` are provided, the band names will be used.

        Warning:
            This method is client-side.

        Parameters:
            type: The type of plot to use. Defaults to ``"bar"``. can be any type of plot from the python lib ``matplotlib.pyplot``. If the one you need is missing open an issue!
            regions: The regions to compute the reducer in.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            bands: The bands to compute the reducer on. Default to all bands.
            regionId: The property used to label region. Defaults to ``"system:index"``.
            labels: The labels to use for the output dictionary. Default to the band names.
            colors: The colors to use for the plot. Default to the default matplotlib colors.
            ax: The matplotlib axis to plot the data on. If None, a new figure is created.
            scale: The scale to use for the computation. Default is 10000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.


        Returns:
            The matplotlib axis with the plot.

        See Also:
            - :docstring:`ee.Image.geetools.byRegions`
            - :docstring:`ee.Image.geetools.byBands`
            - :docstring:`ee.Image.geetools.plot_by_bands`
            - :docstring:`ee.Image.geetools.plot_hist`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ecoregions = ee.FeatureCollection("projects/google/charts_feature_example").select(["label", "value","warm"])
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()

                normClim.geetools.plot_by_regions(ecoregions, ee.Reducer.mean(), scale=10000)
        """
        # get the data from the server
        data = self.byBands(
            regions=regions,
            reducer=reducer,
            bands=bands,
            regionId=regionId,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = regions.aggregate_array(regionId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))
        features = features.getInfo()

        # extract the labels from the parameters
        eeBands = ee.List(bands) if len(bands) else self._obj.bandNames()
        labels = labels if len(labels) else eeBands.getInfo()

        # reorder the data according to the labels id set by the user
        data = {b: {f: data[b][f] for f in features} for b in labels}

        ax = plot_data(type=type, data=data, label_name=regionId, colors=colors, ax=ax)

        return ax

    def plot_by_bands(
        self,
        type: str,
        regions: ee.FeatureCollection,
        reducer: str | ee.Reducer = "mean",
        bands: list = [],
        regionId: str = "system:index",
        labels: list = [],
        colors: list = [],
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        tileScale: float = 1,
    ) -> Axes:
        """Plot the reduced values for each band.

        Each band will be plotted using the ``labels`` as x-axis label defaulting to band names if not provided.
        If no ``bands`` are provided, all bands will be plotted.
        If no ``regionId`` are provided, the ``"system:index"`` property will be used.


        Warning:
            This method is client-side.

        Parameters:
            type: The type of plot to use. Defaults to ``"bar"``. can be any type of plot from the python lib ``matplotlib.pyplot``. If the one you need is missing open an issue!
            regions: The regions to compute the reducer in.
            reducer: The name of the reducer or a reducer object to use. Default is ``"mean"``.
            bands: The bands to compute the reducer on. Default to all bands.
            regionId: The property used to label region. Defaults to ``"system:index"``.
            labels: The labels to use for the output dictionary. Default to the band names.
            colors: The colors to use for the plot. Default to the default matplotlib colors.
            ax: The matplotlib axis to plot the data on. If None, a new figure is created.
            scale: The scale to use for the computation. Default is 10000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.

        Returns:
            The matplotlib axis with the plot.

        See Also:
            - :docstring:`ee.Image.geetools.byRegions`
            - :docstring:`ee.Image.geetools.byBands`
            - :docstring:`ee.Image.geetools.plot_by_regions`
            - :docstring:`ee.Image.geetools.plot_hist`

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                ecoregions = ee.FeatureCollection("projects/google/charts_feature_example").select(["label", "value","warm"])
                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()

                normClim.geetools.plot_by_bands(ecoregions, ee.Reducer.mean(), scale=10000)
        """
        # get the data from the server
        data = self.byRegions(
            regions=regions,
            reducer=reducer,
            bands=bands,
            regionId=regionId,
            labels=labels,
            scale=scale,
            crs=crs,
            crsTransform=crsTransform,
            tileScale=tileScale,
        ).getInfo()

        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = regions.aggregate_array(regionId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))
        features = features.getInfo()

        # extract the labels from the parameters
        eeBands = ee.List(bands) if len(bands) else self._obj.bandNames()
        labels = labels if len(labels) else eeBands.getInfo()

        # reorder the data according to the labels id set by the user
        data = {f: {b: data[f][b] for b in labels} for f in features}

        ax = plot_data(type=type, data=data, label_name=regionId, colors=colors, ax=ax)

        return ax

    def plot_hist(
        self,
        bins: int = 30,
        region: ee.Geometry | None = None,
        bands: list = [],
        labels: list = [],
        colors: list = [],
        precision: int = 2,
        ax: Axes | None = None,
        scale: int = 10000,
        crs: str | None = None,
        crsTransform: list | None = None,
        bestEffort: bool = False,
        maxPixels: int = 10**7,
        tileScale: float = 1,
        **kwargs,
    ) -> Axes:
        """Plot the histogram of the image bands.

        Parameters:
            bins: The number of bins to use for the histogram. Default is 30.
            region: The region to compute the histogram in. Default is the image geometry.
            bands: The bands to plot the histogram for. Default to all bands.
            labels: The labels to use for the output dictionary. Default to the band names.
            colors: The colors to use for the plot. Default to the default matplotlib colors.
            precision: The number of decimal to keep for the histogram bins values. Default is 2.
            ax: The matplotlib axis to plot the data on. If None, a new figure is created.
            scale: The scale to use for the computation. Default is 10,000m.
            crs: The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.
            crsTransform: The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
            bestEffort: If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
            maxPixels: The maximum number of pixels to reduce. default to 10**7.
            tileScale: A scaling factor between 0.1 and 16 used to adjust aggregation tile size; setting a larger tileScale (e.g., 2 or 4) uses smaller tiles and may enable computations that run out of memory with the default.
            **kwargs: Keyword arguments passed to the `matplotlib.fill_between() <https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.fill_between.html>`_ function.

        Returns:
            The matplotlib axis with the plot.

        See Also:
            - :docstring:`ee.Image.geetools.byRegions`
            - :docstring:`ee.Image.geetools.byBands`
            - :docstring:`ee.Image.geetools.plot_by_bands`
            - :docstring:`ee.Image.geetools.plot_by_regions`


        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm91m').toBands()
                normClim.geetools.plot_hist()
        """
        # extract the bands from the image
        eeBands = ee.List(bands) if len(bands) == 0 else self._obj.bandNames()
        eeLabels = ee.List(labels).flatten() if len(labels) == 0 else eeBands
        labels = eeLabels.getInfo()

        # retrieve the region from the parameters
        region = region if region else self._obj.geometry()

        # extract the data from the server
        image = self._obj.select(eeBands).rename(eeLabels).clip(region)

        # set the common parameters of the 3 reducers
        params = {
            "geometry": region,
            "scale": scale,
            "crs": crs,
            "crsTransform": crsTransform,
            "bestEffort": bestEffort,
            "maxPixels": maxPixels,
            "tileScale": tileScale,
        }

        # compute the min and max values of the bands so w can scale the bins of the histogram
        min = image.reduceRegion(**{"reducer": ee.Reducer.min(), **params})
        min = min.values().reduce(ee.Reducer.min())

        max = image.reduceRegion(**{"reducer": ee.Reducer.max(), **params})
        max = max.values().reduce(ee.Reducer.max())

        # compute the histogram. The result is a dictionary with each band as key and the histogram
        # as values. The histograp is a list of [start of bin, value] pairs
        reducer = ee.Reducer.fixedHistogram(min, max, bins)
        raw_data = image.reduceRegion(**{"reducer": reducer, **params}).getInfo()

        # massage raw data to reshape them as usable source for an Axes plot
        # first extract the x coordinates of the plot as a list of bins borders
        # every value is duplicated but the first one to create a scale like display.
        # the values are treated the same way we simply drop the last duplication to get the same size.
        p = 10**precision  # multiplier use to truncate the float values
        x = [int(d[0] * p) / p for d in raw_data[labels[0]] for _ in range(2)][1:]
        data = {l: [int(d[1]) for d in raw_data[l] for _ in range(2)][:-1] for l in labels}

        # create the graph objcet if not provided
        if ax is None:
            fig, ax = plt.subplots()

        # display the histogram as a fill_between plot to respect GEE lib design
        for i, label in enumerate(labels):
            kwargs["facecolor"] = to_rgba(colors[i], 0.2)
            kwargs["edgecolor"] = to_rgba(colors[i], 1)
            ax.fill_between(x, data[label], label=label, **kwargs)

        # customize the layout of the axis
        ax.set_ylabel("Count")
        ax.grid(axis="x" if type in ["barh"] else "y")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

        return ax
