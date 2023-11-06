"""Test the ``Geometry`` class."""
import ee
import pytest

import geetools


class TestKeepType:
    """Test the ``keepType`` method."""

    def test_keep_type(self, geom_instance, data_regression):
        geom = geom_instance.geetools.keepType("LineString")
        data_regression.check(geom.getInfo())

    def test_deprecated_point(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiPoint(
                geom_instance
            )
            data_regression.check(geom.getInfo())

    def test_deprecated_line(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiLineString(
                geom_instance
            )
            data_regression.check(geom.getInfo())

    def test_deprecated_polygon(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiPolygon(
                geom_instance
            )
            data_regression.check(geom.getInfo())

    @pytest.fixture
    def geom_instance(self):
        """et a geometryCollection instance."""
        point0 = ee.Geometry.Point([0, 0], proj="EPSG:4326")
        point1 = ee.Geometry.Point([0, 1], proj="EPSG:4326")
        poly0 = point0.buffer(1, proj="EPSG:4326")
        poly1 = point1.buffer(1, proj="EPSG:4326").bounds(proj="EPSG:4326")
        line = ee.Geometry.LineString([point1, point0], proj="EPSG:4326")
        multiPoly = ee.Geometry.MultiPolygon([poly0, poly1], proj="EPSG:4326")
        return ee.Algorithms.GeometryConstructors.MultiGeometry(
            [multiPoly, poly0, poly1, point0, line],
            crs="EPSG:4326",
            geodesic=True,
            maxError=1,
        )
