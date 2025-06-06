"""Extra methods for the :py:class:`ee.Date` class."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import ee

from .accessors import register_class_accessor

EE_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


@register_class_accessor(ee.Date, "geetools")
class DateAccessor:
    """Toolbox for the :py:class:`ee.Date` class."""

    def __init__(self, obj: ee.Date):
        """Initialize the Date class."""
        self._obj = obj

    @classmethod
    def fromEpoch(cls, number: int, unit: str = "day") -> ee.Date:
        """Set an the number of units since epoch (1970-01-01).

        Parameters:
            number: The number of units since the epoch.
            unit: The unit to return the number of. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The date as a :py:class:`ee.Date` object.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Date.geetools.fromEpoch(49, 'year')
                d.format("YYYY-MM-DD").getInfo()
        """
        cls.check_unit(unit)
        return ee.Date(EE_EPOCH.isoformat()).advance(number, unit)

    @classmethod
    def fromDOY(cls, doy: int, year: int) -> ee.Date:
        """Create a date from a day of year and a year.

        This method is computing doy from a year agnostic representation, the year parameter being
        only used to compute a complete date. the doy should have been generated from the
        :py:meth:`geetools.DateAccessor.toDOY` method.

        Parameters:
            doy: The day of year.
            year: The year.

        Returns:
            The date as a :py:class:`ee.Date` object.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Date.geetools.fromDOY(1, 2020)
                d.format("YYYY-MM-DD").getInfo()
        """
        d, y = ee.Number(doy).toInt(), ee.Number(year).toInt()

        # create the 2 masks to adjust the day of year
        divisibleBy4 = y.mod(4).eq(0)
        divisibleBy100 = y.mod(100).eq(0)
        divisibleBy400 = y.mod(400).eq(0)
        isNotLeap = divisibleBy400.Or(divisibleBy4.And(divisibleBy100.Not())).Not().toInt()
        isAfterMarch = d.gte(60).toInt()

        d = d.subtract(isNotLeap.multiply(isAfterMarch))

        return ee.Date.fromYMD(y, 1, 1).advance(d.subtract(1), "day")

    @classmethod
    def now(cls) -> ee.Date:
        """Create a date on current date.

        Returns:
            The current date.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Date.geetools.now()
                d.format("YYYY-MM-dd").getInfo()
        """
        return ee.Date(datetime.now().isoformat())

    def to_datetime(self, tz: str | ZoneInfo = ZoneInfo("UTC")) -> datetime:
        """Convert a :py:class:`ee.Date` to a :py:class:`datetime.datetime`.

        Since `ee.Date` object is not timezone aware, there is no way to get
        the timezone from it, thus it must be passed as argument.

        Args:
            tz: time zone, defaulted to "UTC". Other names can be found here: https://www.joda.org/joda-time/timezones.html

        Returns:
            The :py:class:`datetime.datetime` representation of the :py:class:`ee.Date`.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Date('2020-01-01').geetools.to_datetime()
                d.strftime('%Y-%m-%d')

        """
        tz = tz if isinstance(tz, ZoneInfo) else ZoneInfo(tz)
        timestamp = self._obj.millis().getInfo() / 1000
        return datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC")).astimezone(tz)

    def getUnitSinceEpoch(self, unit: str = "day") -> ee.Number:
        """Get the number of units since epoch (1970-01-01).

        Parameters:
            unit: The unit to return the number of. One of: ``second``, ``minute``, ``hour``, ``day``, ``month``, ``year``.

        Returns:
            The number of units since the epoch.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

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
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                isLeap = ee.Date('2020-01-01').geetools.isLeap()
                isLeap.getInfo()
        """
        year = self._obj.get("year")
        divisibleBy4 = year.mod(4).eq(0)
        divisibleBy100 = year.mod(100).eq(0)
        divisibleBy400 = year.mod(400).eq(0)

        # d400 or (d4 and not d100)
        isLeap = divisibleBy400.Or(divisibleBy4.And(divisibleBy100.Not()))

        return isLeap.toInt()

    def toDOY(self) -> ee.Number:
        """Convert a date to a day of year.

        This method is computing a year agnostic day of year. It means that the year will always be described
        as a 366 day interval and the day of year will be between 0 and 365. it means that for non
        leap year all days will be shifted by 1 after the 28th of February. Thus the 1st of march will
        always be the 60th day of year.

        Returns:
            The day of year.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                doy = ee.Date('2020-01-01').geetools.toDOY()
                doy.getInfo()
        """
        # create the 2 masks for day offset
        isNotLeap = self.isLeap().Not()
        isAfterMarch = self._obj.get("month").gte(3).toInt()

        # create the day of year
        doy = self._obj.getRelative("day", "year")

        return doy.add(isNotLeap.multiply(isAfterMarch))

    @staticmethod
    def check_unit(unit: str) -> None:
        """Check if the provided value is a valid time unit.

        Parameters:
            unit: The unit to check.

        Raises:
            ValueError: If the unit is not valid.
        """
        if unit not in (units := ["second", "minute", "hour", "day", "month", "year"]):
            raise ValueError(f"unit must be one of: {','.join(units)}")
