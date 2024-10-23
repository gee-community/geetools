"""Extra methods for the ``ee.Array`` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Array, "geetools")
class ArrayAccessor:
    """Toolbox for the ``ee.Array`` class."""

    def __init__(self, obj: ee.Array):
        """Initialize the Array class."""
        self._obj = obj

    # -- alternative constructor -----------------------------------------------
    def full(
        self,
        width: float | int | ee.Number,
        height: float | int | ee.Number,
        value: float | int | ee.Number,
    ) -> ee.Array:
        """Create an array with the given dimensions, initialized to the given value.

        Parameters:
            width: The width of the array.
            height: The height of the array.
            value: The value to initialize the array with.

        Returns:
            An array with the given dimensions, initialized to the given value.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                arr = ee.Array.geetools.full(3, 3, 1)
                arr.getInfo()
        """
        width, height = ee.Number(width).toInt(), ee.Number(height).toInt()
        return ee.Array(ee.List.repeat(ee.List.repeat(value, width), height))

    # -- data maniputlation ----------------------------------------------------
    def set(
        self,
        x: int | ee.Number,
        y: int | ee.Number,
        value: float | int | ee.Number,
    ) -> ee.Array:
        """Set the value of a cell in an array.

        Parameters:
            x: The x coordinate of the cell.
            y: The y coordinate of the cell.
            value: The value to set the cell to.

        Returns:
            The array with the cell set to the given value.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                arr = ee.Array.geetools.full(3, 3, 1)
                arr.geetools.set(1, 1, 0).getInfo()
        """
        xPos, yPos = ee.Number(x).toInt(), ee.Number(y).toInt()
        row = ee.List(self._obj.toList().get(yPos)).set(xPos, ee.Number(value))
        return ee.Array(self._obj.toList().set(yPos, row))
