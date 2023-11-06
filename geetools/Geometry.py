"""Toolbox for the ``ee.Geometry`` class."""
from __future__ import annotations

import ee

from .accessors import geetools_accessor


@geetools_accessor(ee.Geometry)
class Geometry:
    """Toolbox for the ``ee.Geometry`` class."""

    def __init__(self, obj: ee.Geometry):
        """Initialize the Geometry class."""
        self._obj = obj

    def keepType(self, type: str) -> ee.Geometry:
        """Only keep the geometries of the given type from a GeometryCollection.

        Args:
            type: The type of geometries to keep. Can be one of: Point, LineString, LineRing Polygon.

        Returns:
            .. jupyter-execute::

                import ee
                import geetools

                ee.Initialize()

                geom = ee.Geometry.Polygon([[[0,0], [1,0], [1,1], [0,1]]])
                geom = geom.geetools.keepType('LineString')
                print(geom.getInfo())
        """
        # will raise an error if self is not a GeometryCollection
        error_msg = "This method can only be used with GeometryCollections"
        assert self._obj.type().getInfo() == "GeometryCollection", error_msg

        def filterType(geom):
            geom = ee.Geometry(geom)
            return ee.Algorithms.If(geom.type().compareTo(type), None, geom)

        self._obj
        geometries = self._obj.geometries().map(filterType, True)
        return getattr(ee.Geometry, "Multi" + type)(geometries, self._obj.projection())
