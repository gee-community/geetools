"""Test the ``Geometry`` class."""


class TestKeepType:
    """Test the ``keepType`` method."""

    def test_keep_type(self, geom_instance, data_regression):
        geom = geom_instance.geetools.keepType("LineString")
        geojson = geom.getInfo()
        assert geojson["type"] == "MultiLineString"
        assert geom.coordinates().getInfo() == [[[0, 1], [0, 0]]]
