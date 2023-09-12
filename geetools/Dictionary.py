"""Extra methods for the ``ee.Dictionary`` class."""
from __future__ import annotations

from typing import Union

import ee

from .accessors import geetools_accessor


@geetools_accessor(ee.Dictionary)
class Dictionary:
    """Toolbox for the ``ee.Dictionary`` class."""

    def __init__(self, obj: ee.Dictionary):
        """Initialize the Dictionary class."""
        self._obj = obj

    @classmethod
    def fromPairs(self, list: Union[list, ee.List]) -> ee.Dictionary:
        """Create a dictionary from a list of [[key, value], ...]] pairs.

        Parameters:
            list: A list of pairs (key, value).

        Returns:
            A dictionary using the pairs.

        Examples:
            .. jupyter-execute::

                import ee, geetools

                ee.Initialize()

                d = ee.Dictionary.geetools.fromPairs([["foo", 1], ["bar", 2]])
                d.getInfo()
        """
        list = ee.List(list)
        keys = list.map(lambda pair: ee.List(pair).get(0))
        values = list.map(lambda pair: ee.List(pair).get(1))
        return ee.Dictionary.fromLists(keys, values)
