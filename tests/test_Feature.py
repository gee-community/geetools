"""Test the ``Feature`` class."""


class TestToFeatureCollection:
    """Test the ``toFeatureCollection`` method."""

    def test_to_feature_collection(self, multipoint_feature, data_regression):
        fc = multipoint_feature.geetools.toFeatureCollection()
        data_regression.check(fc.getInfo())


class TestRemoveProperties:
    """Test the ``removeProperties`` method."""

    def test_remove_properties(self, multipoint_feature, data_regression):
        feature = multipoint_feature.geetools.removeProperties(["foo"])
        data_regression.check(feature.getInfo())
