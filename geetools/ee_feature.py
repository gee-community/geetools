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

    @classmethod
    def cell(
        cls,
        size: int | ee.Number,
        ix: int | ee.Number = 0,
        iy: int | ee.Number = 0,
        crs: str | ee.String = "EPSG:4326",
    ) -> ee.Feature:
        """Create a feature representing one cell in a regularly spaced grid.

        Args:
            size: The cell side length in the units of the CRS.
            ix: The cell index in the x direction, starting at the CRS area-of-use minimum.
            iy: The cell index in the y direction, starting at the CRS area-of-use minimum.
            crs: The CRS of the grid.

        Returns:
            A feature representing the requested grid cell.
        """
        from pyproj import CRS, Transformer

        size, crs = ee.Number(size), ee.String(crs)
        crs_value = crs.getInfo()
        # Earth Engine cannot currently compute projection bounds server-side; pyproj supplies the area of use.
        # https://gis.stackexchange.com/questions/471100/how-to-get-the-bounds-of-a-projection-in-gee
        # https://issuetracker.google.com/issues/313937471
        geographic_bounds = CRS(crs_value).area_of_use.bounds
        transformer = Transformer.from_crs(4326, crs_value, always_xy=True)
        x_min, y_min, x_max, y_max = transformer.transform_bounds(*geographic_bounds, densify_pts=100)

        x_min, y_min = ee.Number(x_min).toDouble(), ee.Number(y_min).toDouble()
        x_max, y_max = ee.Number(x_max).toDouble(), ee.Number(y_max).toDouble()
        ix, iy = ee.Number(ix).toInt(), ee.Number(iy).toInt()
        x_left = x_min.add(size.multiply(ix))
        x_right = x_left.add(size).min(x_max)
        y_bottom = y_min.add(size.multiply(iy))
        y_top = y_bottom.add(size).min(y_max)

        cell_id = ee.String("{proj}_{size}_E{ix}-S{iy}").geetools.format(
            {
                "proj": ee.Projection(crs).crs(),
                "size": size.format(),
                "ix": ix.format("%02d"),
                "iy": iy.format("%02d"),
            }
        )
        rectangle = ee.Geometry.Rectangle(
            [x_left, y_bottom, x_right, y_top],
            crs,
            geodesic=False,
            evenOdd=True,
        )
        return ee.Feature(rectangle, {"id": cell_id})

    def toFeatureCollection(self) -> ee.FeatureCollection:
        """Convert a :py:class:`ee.Feature` composed of a multiGeometry geometry into a :py:class:`ee.FeatureCollection`.

        Returns:
            The :py:class:`ee.FeatureCollection`.

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

    def removeProperties(self, properties: list[str] | ee.List) -> ee.Feature:
        """Remove properties from a feature.

        Args:
            properties : List of properties to remove.

        Returns:
            The feature without the properties.

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
