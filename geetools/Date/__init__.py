"""Extra methods for the ``ee.Date`` class."""
from __future__ import annotations

from datetime import datetime

import ee

from geetools.accessors import register_class_accessor

EE_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


@register_class_accessor(ee.Date, "geetools")
class DateAccessor:
    """Toolbox for the ``ee.Date`` class."""

    def __init__(self, obj: ee.Date):
        """Initialize the Date class."""
        self._obj = obj

    # -- alternative constructor -----------------------------------------------
    @classmethod
    def fromEpoch(cls, number: int, unit: str = "day") -> ee.Date:
        """Set an the number of units since epoch (1970-01-01).

        Parameters:
            number: The number of units since the epoch.
            unit: The unit to return the number of. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The date as a ``ee.Date`` object.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Date.geetools.fromEpoch(49, 'year')
                d.getInfo()
        """
        cls.check_unit(unit)
        return ee.Date(EE_EPOCH.isoformat()).advance(number, unit)

    @classmethod
    def fromDOY(cls, doy: int, year: int) -> ee.Date:
        """Create a date from a day of year and a year.

        Parameters:
            doy: The day of year.
            year: The year.

        Returns:
            The date as a ``ee.Date`` object.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Date.geetools.fromDOY(1, 2020)
                d.getInfo()
        """
        d, y = ee.Number(doy).toInt(), ee.Number(year).toInt()
        return ee.Date.fromYMD(y, 1, 1).advance(d.subtract(1), "day")

    # -- export date -----------------------------------------------------------
    def to_datetime(self) -> datetime:
        """Convert a ``ee.Date`` to a ``datetime.datetime``.

        Returns:
            The ``datetime.datetime`` representation of the ``ee.Date``.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Date('2020-01-01').geetools.toDatetime()
                d.strftime('%Y-%m-%d')

        """
        return datetime.fromtimestamp(self._obj.millis().getInfo() / 1000.0)

    # -- date operations -------------------------------------------------------
    def getUnitSinceEpoch(self, unit: str = "day") -> ee.Number:
        """Get the number of units since epoch (1970-01-01).

        Parameters:
            unit: The unit to return the number of. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The number of units since the epoch.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Date('2020-01-01').geetools.getUnitSinceEpoch('year')
                d.getInfo()
        """
        self.check_unit(unit)
        return self._obj.difference(EE_EPOCH, unit).toInt()

    def isLeap(self) -> ee.Number:
        """Check if the year of the date is a leap year.

        Returns:
            ``1`` if the year is a leap year, ``0`` otherwise.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Date('2020-01-01').geetools.isLeap()
                d.getInfo()
        """
        year = self._obj.get("year")
        divisibleBy4 = year.mod(4).eq(0)
        divisibleBy100 = year.mod(100).eq(0)
        divisibleBy400 = year.mod(400).eq(0)

        # d400 or (d4 and not d100)
        isLeap = divisibleBy400.Or(divisibleBy4.And(divisibleBy100.Not()))

        return isLeap.toInt()

    # -- helper methods --------------------------------------------------------
    @staticmethod
    def check_unit(unit: str) -> None:
        """Check if the provided value is a valid time unit."""
        if unit not in (units := ["second", "minute", "hour", "day", "month", "year"]):
            raise ValueError(f"unit must be one of: {','.join(units)}")
