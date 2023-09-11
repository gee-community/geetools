"""Extra methods for the ``ee.Array`` class."""
from __future__ import annotations

from typing import Union

import ee

from .accessors import gee_accessor

# hack to have the generated Array class available
ee._InitializeGeneratedClasses()


@gee_accessor(ee.Array)
class Array:
    """Toolbox for the ``ee.Array`` class."""

    def __init__(self, obj: ee.Array):
        """Initialize the Array class."""
        self._obj = obj

    @classmethod
    def full(
        self,
        width: Union[int, float, ee.Number],
        height: Union[int, float, ee.Number],
        value: Union[int, ee.Number, float],
    ) -> ee.Array:
        """Create an array with the given dimensions, initialized to the given value.

        Parameters:
            width: The width of the array.
            height: The height of the array.
            value: The value to initialize the array with.

        Returns:
            An array with the given dimensions, initialized to the given value.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                arr = ee.Array.geetools.full(3, 3, 1)
                arr.getInfo()
        """
        return ee.Array(ee.List.repeat(ee.List.repeat(value, width), height))
