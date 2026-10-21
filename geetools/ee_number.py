"""Extra methods for the :py:class:`ee.Number` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Number, "geetools")
class NumberAccessor:
    """toolbox for the :py:class:`ee.Number` class."""

    def __init__(self, obj: ee.Number):
        """Initialize the Number class."""
        self._obj = obj

    def truncate(self, nbDecimals: int | ee.Number = 2) -> ee.Number:
        """Truncate a number to a given number of decimals.

        Parameters:
            nbDecimals: The number of decimals to truncate to.

        Returns:
            The truncated number.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                n = ee.Number(1.23456).geetools.truncate(3)
                n.getInfo()
        """
        nbDecimals = ee.Number(nbDecimals).toInt()
        factor = ee.Number(10).pow(nbDecimals)
        return self._obj.multiply(factor).toInt().divide(factor)

    def isClose(self, other: int | float | ee.Number, tol: int | float | ee.Number = 1e-9) -> ee.Number:
        """Check if a number is close to another number.

        Args:
            other: The number to compare.
            tol: The tolerance to consider the numbers close.

        Returns:
            A number with value 1 if the numbers are close, 0 otherwise.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                n = ee.Number(1.23456).geetools.isClose(1.23456, 1e-5)
                n.getInfo()
        """
        return self._obj.subtract(other).abs().lte(tol)
