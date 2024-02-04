"""Extra methods for the ``ee.Dictionary`` class."""
from __future__ import annotations

import ee

from geetools.accessors import register_class_accessor
from geetools.types import ee_list


@register_class_accessor(ee.Dictionary, "geetools")
class DictionaryAccessor:
    """Toolbox for the ``ee.Dictionary`` class."""

    def __init__(self, obj: ee.Dictionary):
        """Initialize the Dictionary class."""
        self._obj = obj

    # -- alternative constructor -----------------------------------------------
    def fromPairs(self, list: ee_list) -> ee.Dictionary:
        """Create a dictionary from a list of [[key, value], ...]] pairs.

        Parameters:
            list: A list of pairs (key, value).

        Returns:
            A dictionary using the pairs.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Dictionary.geetools.fromPairs([["foo", 1], ["bar", 2]])
                d.getInfo()
        """
        list = ee.List(list)
        keys = list.map(lambda pair: ee.List(pair).get(0))
        values = list.map(lambda pair: ee.List(pair).get(1))
        return ee.Dictionary.fromLists(keys, values)

    # -- dictionary operations -------------------------------------------------
    def sort(self) -> ee.Dictionary:
        """Sort the dictionary by keys in ascending order.

        Returns:
            The sorted dictionary.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Dictionary({"foo": 1, "bar": 2}).geetools.sort()
                d.getInfo()
        """
        orderededKeys = self._obj.keys().sort()
        values = orderededKeys.map(lambda key: self._obj.get(key))
        return ee.Dictionary.fromLists(orderededKeys, values)

    def getMany(self, list: ee_list) -> ee.List:
        """Extract values from a list of keys.

        Parameters:
            list: A list of keys.

        Returns:
            A list of values.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                d = ee.Dictionary({"foo": 1, "bar": 2, "baz": 3})
                d.geetools.getMany(["foo", "bar"]).getInfo()
        """
        return ee.List(list).map(lambda key: self._obj.get(key))
