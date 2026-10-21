"""Extra methods for the :py:class:`ee.Join` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Join, "geetools")
class JoinAccessor:
    """Toolbox for the :py:class:`ee.Join` class."""

    def __init__(self, obj: ee.Join):
        """Initialize the Join class."""
        self._obj = obj

    @staticmethod
    def byProperty(
        primary: ee.FeatureCollection,
        secondary: ee.FeatureCollection,
        field: str | ee.String,
        outer: bool = False,
    ) -> ee.FeatureCollection:
        """Join 2 collections by a given property field.

        It assumes ids are unique so uses :py:meth:`ee.Join.saveFirst`.

        Args:
            primary: The first collection.
            secondary: The second collection.
            field: The field to join by.
            outer: Whether to keep non-matching features.

        Returns:
            The joined collection.


        Example:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                # build fake featureCollections on the same point
                point = ee.Geometry.Point([0,0])
                prop1 = {'id': 1, 'prop_from_fc1': 'I am from fc1'}
                prop2 = {'id': 1, 'prop_from_fc2': 'I am from fc2'}
                fc1 = ee.FeatureCollection([ee.Feature(point, prop1)])
                fc2 = ee.FeatureCollection([ee.Feature(point, prop2)])

                # join them together in the same featureCollection
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
