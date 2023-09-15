"""Toolbox for the ``ee.Image`` class."""
from __future__ import annotations

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
