"""Extra method for the :py:class:`ee.Filter` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Filter, "geetools")
class FilterAccessor:
    """Toolbox for the :py:class:`ee.Filter` class."""

    def __init__(self, obj: ee.Filter):
        """Initialize the Filter class."""
        self._obj = obj

    def dateRange(self, range: ee.DateRange) -> ee.Filter:
        """Filter by daterange.

        Parameters:
            range: The date range to filter by.

        Returns:
            The filter to apply to a collection.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                # Create a collection and filter it by a date range
                collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

                # filter by date range
                range = ee.DateRange("2018-01-01", "2019-01-01")
                filteredCollection = collection.filter(ee.Filter.geetools.dateRange(range))

                # print the total size of the collections
                print(f"landsat full collection: {collection.size().getInfo()}")
                print(f"landsat filtered collection: {filteredCollection.size().getInfo()}")
        """
        return ee.Filter.date(range.start(), range.end())
