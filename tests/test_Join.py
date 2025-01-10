"""Test the ``Join`` class."""
import ee
import pytest

import geetools  # noqa: F401


class TestByProperty:
    """Test the ``byProperty`` method."""

    def test_by_property(self, fc1, fc2, ee_feature_collection_regression):
        joined = ee.Join.geetools.byProperty(fc1, fc2, "id")
        ee_feature_collection_regression.check(joined, prescision=4)

    def test_by_property_outer(self, fc1, fc2, ee_feature_collection_regression):
        joined = ee.Join.geetools.byProperty(fc1, fc2, "id", outer=True)
        ee_feature_collection_regression.check(joined, prescision=4)

    @pytest.fixture
    def fc1(self):
        point = ee.Geometry.Point([0, 0])
        prop1 = {"id": 1, "prop_from_fc1": "I am from fc1"}
        return ee.FeatureCollection([ee.Feature(point, prop1)])

    @pytest.fixture
    def fc2(self):
        point = ee.Geometry.Point([0, 0])
        prop2 = {"id": 1, "prop_from_fc2": "I am from fc2"}
        return ee.FeatureCollection([ee.Feature(point, prop2)])
