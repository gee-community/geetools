"""Test the ``Geometry`` class."""
import geetools as geetools


class TestKeepType:
    """Test the ``keepType`` method."""

    def test_keep_type(self, geom_instance, data_regression):
        geom = geom_instance.geetools.keepType("LineString")
        geojson = geom.getInfo()
        assert geojson["type"] == "MultiLineString"
        assert geom.coordinates().getInfo() == [[[0, 1], [0, 0]]]

    def test_keep_multiple_types(self, geom_instance):
        geom = geom_instance.geetools.keepType(("Point", "LineString"))
        geojson = geom.getInfo()

        assert geojson["type"] == "GeometryCollection"
        assert {geometry["type"] for geometry in geojson["geometries"]} == {"Point", "LineString"}

    def test_exclude_types(self, geom_instance):
        geom = geom_instance.geetools.keepType(("Point", "LineString"), exclude=True)
        geojson = geom.getInfo()

        # verify that he kpt all the polygons and multipolygons
        # and reconstructed the multipolygons correctly as a polygon (side effect)
        assert geojson["type"] == "GeometryCollection"
        assert len(geojson["geometries"]) == 4
        assert {geometry["type"] for geometry in geojson["geometries"]} == {"Polygon"}
