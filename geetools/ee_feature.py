"""Toolbox for the :py:class:`ee.Feature` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Feature, "geetools")
class FeatureAccessor:
    """Toolbox for the :py:class:`ee.Feature` class."""

    def __init__(self, obj: ee.Feature):
        """Initialize the class."""
        self._obj = obj

    def toFeatureCollection(self) -> ee.FeatureCollection:
        """Convert a :py:class:`ee.Feature` composed of a multiGeometry geometry into a :py:class:`ee.FeatureCollection`.

        Returns:
            The :py:class:`ee.FeatureCollection`

        Example:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                geoms = ee.Geometry.MultiPoint([[0,0], [0,1]])
                feature = ee.Feature(geoms).set("foo", "bar")
                fc = feature.geetools.toFeatureCollection()
                fc.getInfo()
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
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                feature = ee.Feature(None).set("foo", "bar", "baz", "foo")
                feature = feature.geetools.removeProperties(["foo"])
                feature.getInfo()
        """
        properties = ee.List(properties)
        proxy = ee.Feature(self._obj.geometry())  # drop properties
        return proxy.copyProperties(self._obj, exclude=properties)
