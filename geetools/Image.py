"""Toolbox for the ``ee.Image`` class."""
from __future__ import annotations

from typing import Union

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
                value = date.reduceRegion(ee.Reducer.first()).get("date")
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
                image = image1.geetools.merge(image2, image3)
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
