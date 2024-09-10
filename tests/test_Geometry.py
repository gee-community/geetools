"""Test the ``Geometry`` class."""
import pytest

import geetools


class TestKeepType:
    """Test the ``keepType`` method."""

    def test_keep_type(self, geom_instance, data_regression):
        geom = geom_instance.geetools.keepType("LineString")
        geojson = geom.getInfo()
        assert geojson["type"] == "MultiLineString"
        assert geom.coordinates().getInfo() == [[[0, 1], [0, 0]]]

    def test_deprecated_point(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiPoint(geom_instance)
            geojson = geom.getInfo()
            assert geojson["type"] == "MultiPoint"
            assert geom.coordinates().getInfo() == [[0, 0]]

    def test_deprecated_line(self, geom_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiLineString(geom_instance)
            geojson = geom.getInfo()
            assert geojson["type"] == "MultiLineString"
            assert geom.coordinates().getInfo() == [[[0, 1], [0, 0]]]

    def test_deprecated_polygon(self, geom_instance, ndarrays_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.geometry.GeometryCollection_to_MultiPolygon(geom_instance)
            geom.getInfo()
            assert geom.getInfo()["type"] == "MultiPolygon"
            ndarrays_regression.check({"coordinates": geom.bounds().getInfo()["coordinates"]})
