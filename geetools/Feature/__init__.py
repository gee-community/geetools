"""Toolbox for the ``ee.Feature`` class."""
from __future__ import annotations

import ee

from geetools.accessors import register_class_accessor


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
