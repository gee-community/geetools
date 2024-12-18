"""Extra methods for the ``ee.Dictionary`` class."""
from __future__ import annotations

from typing import Any

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Dictionary, "geetools")
class DictionaryAccessor:
    """Toolbox for the ``ee.Dictionary`` class."""

    def __init__(self, obj: ee.Dictionary):
        """Initialize the Dictionary class."""
        self._obj = obj

    # -- alternative constructor -----------------------------------------------
    def fromPairs(self, list: list | ee.List) -> ee.Dictionary:
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

    def getMany(self, list: list | ee.List) -> ee.List:
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

    def toTable(self, valueType: ee.List | ee.Dictionary | Any = Any) -> ee.FeatureCollection:
        """Convert a :py:class:`ee.Dictionary` to a :py:class:`ee.FeatureCollection` with no geometries (table).

        The keys will always be stored in `system:index` column.

        Parameters:
            valueType: this will define how to process the values. In case of
            ee.List the values will be stored in columns named `value_<position>`.
            In case of a ee.Dictionary, column names will be created from the keys.
            For any other type, it will return a table with one feature with
            one column per key.

        Returns:
            a ee.FeatureCollection in which the keys of the ee.Dictionary are
            in the `system:index` and the values are in new columns.
        """

        def features_from_dict(key, value) -> ee.Feature:
            key = ee.String(key)
            feat = ee.Feature(None, {"system:index": key})
            return feat.set(ee.Dictionary(value))

        def features_from_list(key, value) -> ee.Feature:
            key = ee.String(key)
            feat = ee.Feature(None, {"system:index": key})
            value = ee.List(value)
            keys = ee.List.sequence(1, value.size())
            keys = keys.map(lambda k: ee.String("value_").cat(ee.Number(k).toInt()))
            properties = ee.Dictionary.fromLists(keys, value)
            return feat.set(properties)

        if valueType == ee.Dictionary:
            features = self._obj.map(features_from_dict).values()
        elif valueType == ee.List:
            features = self._obj.map(features_from_list).values()
        else:
            return ee.FeatureCollection([ee.Feature(None, self._obj)])
        return ee.FeatureCollection(features)
