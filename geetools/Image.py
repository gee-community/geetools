"""Toolbox for the ``ee.Image`` class."""
from __future__ import annotations

from typing import Optional, Union

import ee

from .accessors import geetools_accessor


@geetools_accessor(ee.Image)
class Image:
    """Toolbox for the ``ee.Image`` class."""

    def __init__(self, obj: ee.Image):
        """Initialize the Image class."""
        self._obj = obj

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
                clipped = image.geetools.clipToCollection(fc)
                print(clipped.size().getInfo())
        """

        def fcClip(feat):
            image = self._obj.clip(feat.geometry())
            return ee.Algorithms.If(
                ee.Number(keepProperties).toInt(), image.copyProperties(feat), image
            )

        return ee.ImageCollection(fc.map(fcClip))
