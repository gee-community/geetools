"""Extra methods for the ``ee.String`` class."""
from __future__ import annotations

from typing import Union

import ee

from .accessors import gee_accessor


@gee_accessor(ee.String)
class String:
    """Toolbox for the ``ee.String`` class."""

    def __init__(self, obj: ee.String):
        """Initialize the String class."""
        self._obj = obj

    def eq(self, other: Union[str, ee.String]) -> ee.Number:
        """Compare two strings and return a ``ee.Number``.

        Parameters:
            other: The string to compare with.

        Returns:
            ``1`` if the strings are equal, ``0`` otherwise.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                s = ee.String("foo").eq("foo")
                s.getInfo()
        """
        return self._obj.compareTo(ee.String(other)).Not()
