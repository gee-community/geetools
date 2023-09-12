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
