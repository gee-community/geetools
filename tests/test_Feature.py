"""Test the ``Feature`` class."""
import ee

import geetools  # noqa: F401


class TestToFeatureCollection:
    """Test the ``toFeatureCollection`` method."""

    def test_to_feature_collection(self, multipoint_feature, ee_feature_collection_regression):
        fc = multipoint_feature.geetools.toFeatureCollection()
        ee_feature_collection_regression.check(fc)


class TestRemoveProperties:
    """Test the ``removeProperties`` method."""

    def test_remove_properties(self, multipoint_feature, ee_feature_collection_regression):
        feature = multipoint_feature.geetools.removeProperties(["foo"])
        ee_feature_collection_regression.check(ee.FeatureCollection(feature))
