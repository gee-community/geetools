"""Extra methods for the ``ee.Join`` class."""
from __future__ import annotations

import ee

from geetools.accessors import register_class_accessor
from geetools.types import ee_str


@register_class_accessor(ee.Join, "geetools")
class JoinAccessor:
    """Toolbox for the ``ee.Join`` class."""

    def __init__(self, obj: ee.join):
        """Initialize the Join class."""
        self._obj = obj

    @staticmethod
    def byProperty(
        primary: ee.Collection,
        secondary: ee.Collection,
        field: ee_str,
        outer: bool = False,
    ) -> ee.Collection:
        """Join 2 collections by a given property field.

        It assumes ids are unique so uses ee.Join.saveFirst.

        Args:
            primary: the first collection
            secondary: the second collection
            field: the field to join by
            outer: whether to keep non matching features

        Returns:
            the joined collection


        Example:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                point = ee.Geometry.Point([0,0])
                prop1 = {'id': 1, 'prop_from_fc1': 'I am from fc1'}
                prop2 = {'id': 1, 'prop_from_fc2': 'I am from fc2'}
                fc1 = ee.FeatureCollection([ee.Feature(point, prop1)])
                fc2 = ee.FeatureCollection([ee.Feature(point, prop2)])
                joined = ee.Join.geetools.byProperty(fc1, fc2, 'id')
                joined.getInfo()

        """
        field = ee.String(field)
        primary, secondary = ee.FeatureCollection(primary), ee.FeatureCollection(secondary)
        Filter = ee.Filter.equals(leftField=field, rightField=field)
        join = ee.Join.saveFirst(matchKey="match", outer=outer)
        joined = join.apply(primary, secondary, Filter)

        def cleanJoin(feat):
            primaryProp = feat.propertyNames().remove("match")
            secondaryProp = ee.Feature(feat.get("match")).toDictionary()
            return feat.select(primaryProp).setMulti(secondaryProp)

        return ee.FeatureCollection(joined.map(cleanJoin))
