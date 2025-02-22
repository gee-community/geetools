"""Extra methods for the :py:class:`ee.Dictionary` class."""
from __future__ import annotations

from typing import Literal

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Dictionary, "geetools")
class DictionaryAccessor:
    """Toolbox for the :py:class:`ee.Dictionary` class."""

    def __init__(self, obj: ee.Dictionary):
        """Initialize the Dictionary class."""
        self._obj = obj

    # -- alternative constructor -----------------------------------------------
    def fromPairs(self, list: list | ee.List) -> ee.Dictionary:
        """Create a dictionary from a list of ``[[key, value], ...]]`` pairs.

        Parameters:
            list: A list of pairs ``(key, value)``.

        Returns:
            A dictionary using the pairs.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

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
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

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
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Dictionary({"foo": 1, "bar": 2, "baz": 3})
                d = d.geetools.getMany(["foo", "bar"])
                d.getInfo()
        """
        return ee.List(list).map(lambda key: self._obj.get(key))

    def toTable(
        self, valueType: Literal["dict", "list", "value"] = "value"
    ) -> ee.FeatureCollection:
        """Convert a :py:class:`ee.Dictionary` to a :py:class:`ee.FeatureCollection` with no geometries (table).

        There are 3 different type of values handled by this method:

        1. value (default): when values are a :py:class:`ee.String` or
           :py:class:`ee.Number`, the keys will be saved in the column
           ``system:index`` and the values in the column "value".

        2. dict: when values are a :py:class:`ee.Dictionary`, the keys will be
           saved in the column ``system:index`` and the values will be treated
           as each Feature's properties.

        3. list: when values are a :py:class:`ee.List` of numbers or strings,
           the keys will be saved in the column ``system:index`` and the values
           in as many columns as items in the list. The column name pattern is
           "value_{i}" where i is the position of the element in the list.

        These are the only supported patterns. Other patterns should be converted
        to one of these. For example, the values of a reduction using the
        reducer :py:meth:`ee.Reducer.frequencyHistogram` are of type
        :py:class:`ee.Array` and the array contains lists.

        Parameters:
            valueType: this will define how to process the values.

        Returns:
            a collection in which the keys of the :py:class:`ee.Dictionary` are
            in the ``system:index`` and the values are in new columns.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Dictionary({"foo": 1, "bar": 2})
                d.geetools.toTable().getInfo()

            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Dictionary({
                  "Argentina": {"ADM0_CODE": 12, "Shape_Area": 278.289196625},
                  "Armenia": {"ADM0_CODE": 13, "Shape_Area": 3.13783139285},
                })
                d.geetools.toTable('dict').getInfo()

            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                d = ee.Dictionary({
                  "Argentina": [12, 278.289196625],
                  "Armenia": [13, 3.13783139285],
                })
                d.geetools.toTable().getInfo()

            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                # reduction
                ran = ee.Image.random().multiply(10).reduceRegion(
                    reducer=ee.Reducer.fixedHistogram(0, 1.1, 11),
                    geometry=ee.Geometry.Point([0,0]).buffer(1000),
                    scale=100
                )

                # process to get desired format
                res = ee.Array(ee.Dictionary(ran).get('random'))
                reslist = res.toList()
                keys = reslist.map(lambda i: ee.Number(ee.List(i).get(0)).multiply(100).toInt().format())
                values = reslist.map(lambda i: ee.Number(ee.List(i).get(1)).toInt())
                final = ee.Dictionary.fromLists(keys, values)

                # fetch
                final.geetools.toTable().getInfo()
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

        make_features = {
            "list": features_from_list,
            "dict": features_from_dict,
            "value": features_from_any,
        }
        features = self._obj.map(make_features[valueType]).values()
        return ee.FeatureCollection(features)
