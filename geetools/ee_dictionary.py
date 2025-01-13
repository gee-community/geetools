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

        There are 3 different type of values handled by this method:

        1. Any (default): when values are a `ee.String` or `ee.Number`, the
        keys will be saved in the column "system:index" and the values in the
        column "value".

        .. code-block:: python

            import ee, geetools

            ee.Initialize()

            d = ee.Dictionary({"foo": 1, "bar": 2})
            d.geetools.toTable().getInfo()

            >> {
              'type': FeatureCollection,
              'columns': {
                'system:index': String,
                'value': String
              },
              features: [
                {
                  'type': Feature,
                  'geometry': null,
                  'id': 'foo',
                  'properties': {
                    'value': 1,
                  },
                },
                {
                  'type': Feature,
                  'geometry': null,
                  'id': 'bar',
                  'properties': {
                    'value': 2,
                  },
                }
            ]}

        2. ee.Dictionary: when values are a ee.Dictionary, the
        keys will be saved in the column "system:index" and the values will be
        treated as each Feature's properties.

        .. code-block:: python

            import ee, geetools

            ee.Initialize()

            d = ee.Dictionary({
              "Argentina": {"ADM0_CODE": 12, "Shape_Area": 278.289196625},
              "Armenia": {"ADM0_CODE": 13, "Shape_Area": 3.13783139285},
            })
            d.geetools.toTable().getInfo()

            >> {
              'type': FeatureCollection,
              'columns': {
                'system:index': String,
                'ADM0_CODE': Integer,
                'Shape_Area': Float
              },
              features: [
                {
                  'type': Feature,
                  'geometry': null,
                  'id': 'Argentina',
                  'properties': {
                    'ADM0_CODE': 12
                    'Shape_Area': 278.289196625
                  },
                },
                {
                  'type': Feature,
                  'geometry': null,
                  'id': 'Armenia',
                  'properties': {
                    'ADM0_CODE': 13
                    'Shape_Area': 3.13783139285
                  },
                }
            ]}

        3. ee.List: when values are a ee.List of numbers or strings, the
        keys will be saved in the column "system:index" and the values in
        as many columns as items in the list. The column name pattern is
        "value_{i}" where i is the position of the element in the list.

        .. code-block:: python

            import ee, geetools

            ee.Initialize()

            d = ee.Dictionary({
              "Argentina": [12, 278.289196625],
              "Armenia": [13, 3.13783139285],
            })
            d.geetools.toTable().getInfo()

            >> {
              'type': FeatureCollection,
              'columns': {
                'system:index': String,
                'value_0': Integer,
                'value_1': Float
              },
              features: [
                {
                  'type': Feature,
                  'geometry': null,
                  'id': 'Argentina',
                  'properties': {
                    'value_0': 12
                    'value_1': 278.289196625
                  },
                },
                {
                  'type': Feature,
                  'geometry': null,
                  'id': 'Armenia',
                  'properties': {
                    'value_0': 13
                    'value_1': 3.13783139285
                  },
                }
            ]}

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
            index = {"system:index": ee.String(key)}
            props = ee.Dictionary(value).combine(index)
            return ee.Feature(None, props)

        def features_from_list(key, value) -> ee.Feature:
            index = {"system:index": ee.String(key)}
            values = ee.List(value)
            columns = ee.List.sequence(0, values.size().subtract(1))
            columns = columns.map(lambda k: ee.String("value_").cat(ee.Number(k).toInt()))
            props = ee.Dictionary.fromLists(columns, values).combine(index)
            return ee.Feature(None, props)

        def features_from_any(key, value) -> ee.Feature:
            props = {"system:index": ee.String(key), "value": value}
            return ee.Feature(None, props)

        if valueType == ee.Dictionary:
            features = self._obj.map(features_from_dict).values()
        elif valueType == ee.List:
            features = self._obj.map(features_from_list).values()
        else:
            features = self._obj.map(features_from_any).values()
        return ee.FeatureCollection(features)
