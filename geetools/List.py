"""Extra methods for the ``ee.List`` class."""
from __future__ import annotations

from typing import Union

import ee

from .accessors import geetools_accessor


@geetools_accessor(ee.List)
class List:
    """Toolbox for the ``ee.List`` class."""

    def __init__(self, obj: ee.List):
        """Initialize the List class."""
        self._obj = obj

    def product(self, other: Union[list, ee.List]) -> ee.List:
        """Compute the cartesian product of 2 list.

        Values will all be considered as string and will be joined with **no spaces**.

        Parameters:
            other: The list to compute the cartesian product with.

        Returns:
            A list of strings corresponding to the cartesian product.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                l1 = ee.List(["1", "2", "3"])
                l2 = ee.List(["a", "b", "c"])

                l1.geetools.product(l2).getInfo()
        """
        l1 = ee.List(self._obj).map(lambda e: ee.String(e))
        l2 = ee.List(other).map(lambda e: ee.String(e))
        product = l1.map(lambda e: l2.map(lambda f: ee.String(e).cat(ee.String(f))))
        return product.flatten()

    def complement(self, other: Union[list, ee.List]) -> ee.List:
        """Compute the complement of the current list and the ``other`` list.

        The mthematical complement is the list of elements that are in the current list but not in the ``other`` list and vice-versa.

        Parameters:
            other: The list to compute the complement with.

        Returns:
            A list of strings corresponding to the complement of the current list and the ``other`` list.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                l1 = ee.List(["1", "2", "3"])
                l2 = ee.List(["2", "3", "4"])

                l1.geetools.complement(l2).getInfo()
        """
        l1, l2 = ee.List(self._obj), ee.List(other)
        return l1.removeAll(l2).cat(l2.removeAll(l1))
