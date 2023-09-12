"""Extra methods for the ``ee.Date`` class."""
from __future__ import annotations

from datetime import datetime

import ee

from .accessors import gee_accessor

EE_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


@gee_accessor(ee.Date)
class Date:
    """Toolbox for the ``ee.Date`` class."""

    def __init__(self, obj: ee.Date):
        """Initialize the Date class."""
        self._obj = obj

    def toDatetime(self) -> datetime:
        """Convert a ``ee.Date`` to a ``datetime.datetime``.

        Returns:
            The ``datetime.datetime`` representation of the ``ee.Date``.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                d = ee.Date('2020-01-01').geetools.toDateTime()
                d.strftime('%Y-%m-%d')

        """
        return datetime.fromtimestamp(self._obj.millis().getInfo() / 1000.0)

    def getUnitSinceEpoch(self, unit: str = "day") -> ee.Number:
        """Get the number of units since epoch (1970-01-01).

        Parameters:
            unit: The unit to return the number of. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The number of units since the epoch.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                d = ee.Date('2020-01-01').geetools.unitSinceEpoch('year')
                d.getInfo()
        """
        self._check_unit(unit)
        return self._obj.difference(EE_EPOCH, unit).toInt()

    @classmethod
    def fromEpoch(self, number: int, unit: str = "day") -> ee.Date:
        """Set an the number of units since epoch (1970-01-01).

        Parameters:
            number: The number of units since the epoch.
            unit: The unit to return the number of. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The date as a ``ee.Date`` object.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                d = ee.Date.geetools.fromEpoch(49, 'year')
                d.getInfo()
        """
        self._check_unit(unit)
        return ee.Date(EE_EPOCH.isoformat()).advance(number, unit)

    @classmethod
    def _check_unit(cls, unit: str) -> None:
        """Check if the unit is valid."""
        if unit not in (units := ["second", "minute", "hour", "day", "month", "year"]):
            raise ValueError(f"unit must be one of: {','.join(units)}")
