"""Test the ``Feature`` class."""
import ee
import pytest

import geetools


class TestToFeatureCollection:
    """Test the ``toFeatureCollection`` method."""

    def test_to_feature_collection(self, feature_instance, data_regression):
        fc = feature_instance.geetools.toFeatureCollection()
        data_regression.check(fc.getInfo())

    def test_deprecated_to_feature_collection(self, feature_instance, data_regression):
        with pytest.deprecated_call():
            fc = geetools.feature.GeometryCollection_to_FeatureCollection(feature_instance)
            data_regression.check(fc.getInfo())

    @pytest.fixture
    def feature_instance(self):
        """Return a ``Feature`` instance."""
        geoms = ee.Geometry.MultiPoint([[0, 0], [0, 1]])
        return ee.Feature(geoms).set("foo", "bar")
