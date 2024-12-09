"""Extra tools for the ``ee.DateRange`` class."""

from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.DateRange, "geetools")
class DateRangeAccessor:
    """Toolbox for the ``ee.DateRange`` class."""

    def __init__(self, obj: ee.DateRange):
        """Initialize the DateRange class."""
        self._obj = obj

    # -- date range operations -------------------------------------------------
    def split(self, interval: int | ee.Number, unit: str = "day") -> ee.List:
        """Convert a ``ee.DateRange`` to a list of ``ee.DateRange``.

        The DateRange will be split in multiple DateRanges of the specified interval and Unit.
        For example "1", "day". if the end date is not included the last dateRange length will be adapted.

        Parameters:
            interval: The interval to split the DateRange
            unit: The unit to split the DateRange. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The list of DateRanges

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                dateList = ee.DateRange('2020-01-01', '2020-01-31').geetools.split(1, 'day')
                dateList.getInfo()
        """
        self.check_unit(unit)
        interval = ee.Number(interval).toInt().multiply(self.unitMillis(unit))
        start, end = self._obj.start().millis(), self._obj.end().millis()

        timestampList = ee.List.sequence(start, end, interval)
        timestampList = timestampList.add(ee.Number(end).toFloat()).distinct()
        indexList = ee.List.sequence(0, timestampList.size().subtract(2))

        return indexList.map(
            lambda i: ee.DateRange(timestampList.get(i), timestampList.get(ee.Number(i).add(1)))
        )

    # -- utils -----------------------------------------------------------------
    @staticmethod
    def check_unit(unit: str) -> None:
        """Check if the unit is valid."""
        if unit not in (units := ["second", "minute", "hour", "day", "month", "year"]):
            raise ValueError(f"unit must be one of: {','.join(units)}")

    @staticmethod
    def unitMillis(unit: str) -> ee.Number:
        """Get the milliseconds of a unit.

        Parameters:
            unit: The unit to get the milliseconds. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The number of milliseconds in the unit
        """
        millis = {
            "second": 1000,
            "minute": 1000 * 60,
            "hour": 1000 * 60 * 60,
            "day": 1000 * 60 * 60 * 24,
            "month": 1000 * 60 * 60 * 24 * 30,
            "year": 1000 * 60 * 60 * 24 * 365,
        }
        return ee.Number(millis[unit])
