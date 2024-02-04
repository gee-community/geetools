"""Extra methods for the ``ee.Number`` class."""
from __future__ import annotations

import ee

from geetools.accessors import register_class_accessor
from geetools.types import ee_int


@register_class_accessor(ee.Number, "geetools")
class NumberAccessor:
    """toolbox for the ``ee.Number`` class."""

    def __init__(self, obj: ee.Number):
        """Initialize the Number class."""
        self._obj = obj

    def truncate(self, nbDecimals: ee_int = 2) -> ee.Number:
        """Truncate a number to a given number of decimals.

        Parameters:
            nbDecimals: The number of decimals to truncate to.

        Returns:
            The truncated number.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                n = ee.Number(1.23456).geetools.truncate(3)
                n.getInfo()
        """
        nbDecimals = ee.Number(nbDecimals).toInt()
        factor = ee.Number(10).pow(nbDecimals)
        return self._obj.multiply(factor).toInt().divide(factor)
