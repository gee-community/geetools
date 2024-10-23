"""Toolbox for the ``ee.Feature`` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Feature, "geetools")
class FeatureAccessor:
    """Toolbox for the ``ee.Feature`` class."""

    def __init__(self, obj: ee.Feature):
        """Initialize the class."""
        self._obj = obj

    def toFeatureCollection(self) -> ee.FeatureCollection:
        """Convert a feature composed of a multiGeometry geometry into a FEatureCollection.

        Returns:
            The FeatureCollection

        Example:
            .. code-block:: python

                    import ee
                    import geetools

                    ee.Initialize()

                    geoms = ee.Geometry.MultiPoint([[0,0], [0,1]])
                    feature = ee.Feature(geoms).set("foo", "bar")
                    fc = feature.geetools.toFeatureCollection()
                    print(fc.size().getInfo())
        """
        geoms = self._obj.geometry().geometries()
        fc = geoms.map(lambda g: self._obj.setGeometry(g))
        return ee.FeatureCollection(fc)

    def removeProperties(self, properties: list | ee.List) -> ee.Feature:
        """Remove properties from a feature.

        Args:
            properties : List of properties to remove

        Returns:
            The feature without the properties

        Example:
            .. code-block:: python

                    import ee
                    import geetools

                    ee.Initialize()

                    feature = ee.Feature(None).set("foo", "bar", "baz", "foo")
                    feature = feature.geetools.removeProperties(["foo"])
                    print(feature.getInfo())
        """
        properties = ee.List(properties)
        proxy = ee.Feature(self._obj.geometry())  # drop properties
        return proxy.copyProperties(self._obj, exclude=properties)
