"""Extra methods for the ee.Number class"""
from typing import Union

import ee

from .accessors import gee_accessor

@gee_accessor(ee.numbers.Number)
class Number:
    """toolbox for the number class"""

    def __init__(self, obj: ee.numbers.Number):
        self._obj = obj

    def truncate(self, nbDecimals: Union[ee.Number, int] = 2) -> ee.numbers.Number:
        """Truncate a number to a given number of decimals

        Parameters:
            nbDecimals : The number of decimals to truncate to.

        Returns:
            The truncated number.
        """
        nbDecimals = ee.Number(nbDecimals).toInt()
        factor = ee.Number(10).pow(nbDecimals)
        return self._obj.multiply(factor).toInt().divide(factor)
