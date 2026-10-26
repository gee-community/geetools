"""Toolbox for the :py:class:`ee.Geometry` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.Geometry, "geetools")
class GeometryAccessor:
    """Toolbox for the :py:class:`ee.Geometry` class."""

    def __init__(self, obj: ee.Geometry):
        """Initialize the Geometry class."""
        self._obj = obj

    def keepType(self, type: str | tuple[str, ...], exclude: bool = False) -> ee.Geometry:
        """Only keep the geometries of the given type from a GeometryCollection.

        Args:
            type: The type or types of geometries to keep. Can be one or more of: Point, LineString,
                Polygon.
            exclude: If True, remove the given geometry types instead of keeping them.

        Returns:
            The geometries matching the selected types.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                # generate multiple geometries of different types
                point0 = ee.Geometry.Point([0,0], proj="EPSG:4326")
                point1 = ee.Geometry.Point([0,1], proj="EPSG:4326")
                poly0 = point0.buffer(1, proj="EPSG:4326")
                poly1 = point1.buffer(1, proj="EPSG:4326").bounds(proj="EPSG:4326")
                line = ee.Geometry.LineString([point1, point0], proj="EPSG:4326")
                multiPoly = ee.Geometry.MultiPolygon([poly0, poly1], proj="EPSG:4326")

                # create a geometry collection from them
                geometryCollection = ee.Algorithms.GeometryConstructors.MultiGeometry(
                    [multiPoly, poly0, poly1, point0, line],
                    crs="EPSG:4326",
                    geodesic=True,
                    maxError=1
                )

                # extract only the LineString geometries from the collection
                geom = geometryCollection.geetools.keepType('LineString')
                geom.getInfo()

                # extract the Point and LineString geometries from the collection
                geom = geometryCollection.geetools.keepType(('Point', 'LineString'))
                geom.getInfo()
        """
        # will raise an error if self is not a GeometryCollection
        error_msg = "This method can only be used with GeometryCollections"
        assert self._obj.type().getInfo() == "GeometryCollection", error_msg

        geometry_types = (type,) if isinstance(type, str) else type
        types = ee.List(list(geometry_types))

        def filterType(geom):
            geom = ee.Geometry(geom)
            matches = types.contains(geom.type())
            if exclude:
                return ee.Algorithms.If(matches, None, geom)
            return ee.Algorithms.If(matches, geom, None)

        geometries = self._obj.geometries().map(filterType, True)
        if not exclude and len(geometry_types) == 1:
            return getattr(ee.Geometry, "Multi" + geometry_types[0])(geometries, self._obj.projection())
        return ee.Algorithms.GeometryConstructors.MultiGeometry(geometries, crs=self._obj.projection())
