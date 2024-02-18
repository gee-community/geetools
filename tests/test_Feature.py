"""Test the ``Feature`` class."""
import pytest

import geetools


class TestToFeatureCollection:
    """Test the ``toFeatureCollection`` method."""

    def test_to_feature_collection(self, multipoint_feature, data_regression):
        fc = multipoint_feature.geetools.toFeatureCollection()
        data_regression.check(fc.getInfo())

    def test_deprecated_to_feature_collection(self, multipoint_feature, data_regression):
        with pytest.deprecated_call():
            fc = geetools.feature.GeometryCollection_to_FeatureCollection(multipoint_feature)
            data_regression.check(fc.getInfo())


class TestRemoveProperties:
    """Test the ``removeProperties`` method."""

    def test_remove_properties(self, multipoint_feature, data_regression):
        feature = multipoint_feature.geetools.removeProperties(["foo"])
        data_regression.check(feature.getInfo())
