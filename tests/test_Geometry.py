"""Test the ``Geometry`` class."""
import pytest

import geetools


class TestKeepType:
    """Test the ``keepType`` method."""

    def test_keep_type(self, geom_instance, data_regression):
        geom = geom_instance.geetools.keepType("LineString")
        data_regression.check(geom.getInfo())

    def test_deprecated_point(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiPoint(geom_instance)
            data_regression.check(geom.getInfo())

    def test_deprecated_line(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiLineString(geom_instance)
            data_regression.check(geom.getInfo())

    def test_deprecated_polygon(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiPolygon(geom_instance)
            data_regression.check(geom.getInfo())
