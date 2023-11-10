"""Extra method for the ``ee.Filter`` class."""
from __future__ import annotations

from typing import Any

import ee

from geetools.accessors import geetools_accessor


@geetools_accessor(ee.Filter)
class Filter:
    """Toolbox for the ``ee.Filter`` class."""

    def __init__(self, obj: ee.Filter):
        """Initialize the Filter class."""
        self._obj = obj

    # -- date filters ----------------------------------------------------------
    def dateRange(self, range: ee.DateRange) -> Any:
        """Filter by daterange.

        Parameters:
            range: The date range to filter by.

        Returns:
            The filter to apply to a collection.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                col = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
                range = ee.DateRange("2018-01-01", "2019-01-01")
                filteredCol = col.filter(ee.Filter.geetools.dateRange(range))

                filteredCol.size().getInfo()
        """
        return ee.Filter.date(range.start(), range.end())
