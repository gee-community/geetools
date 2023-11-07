"""Extra methods for the ``ee.Number`` class."""
from __future__ import annotations

from typing import Union

import ee

from geetools.accessors import geetools_accessor


@geetools_accessor(ee.Number)
class Number:
    """toolbox for the ``ee.Number`` class."""

    def __init__(self, obj: ee.Number):
        """Initialize the Number class."""
        self._obj = obj

    def truncate(self, nbDecimals: Union[ee.Number, int] = 2) -> ee.Number:
        """Truncate a number to a given number of decimals.

        Parameters:
            nbDecimals: The number of decimals to truncate to.

        Returns:
            The truncated number.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                n = ee.Number(1.23456).geetools.truncate(3)
                n.getInfo()
        """
        nbDecimals = ee.Number(nbDecimals).toInt()
        factor = ee.Number(10).pow(nbDecimals)
        return self._obj.multiply(factor).toInt().divide(factor)
