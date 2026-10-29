"""Test the ``Feature`` class."""
import ee

import geetools  # noqa: F401


class TestCell:
    """Test the ``cell`` method."""

    def test_cell(self):
        cell = ee.Feature.geetools.cell(20)
        assert cell.get("id").getInfo() == "EPSG:4326_20_E00-S00"
        assert cell.geometry().coordinates().getInfo() == [
            [[-180, -90], [-160, -90], [-160, -70], [-180, -70], [-180, -90]]
        ]

    def test_cell_with_indexes(self):
        cell = ee.Feature.geetools.cell(20, ix=5, iy=5)
        assert cell.get("id").getInfo() == "EPSG:4326_20_E05-S05"

    def test_cell_with_size_10_and_indexes(self):
        cell = ee.Feature.geetools.cell(10, ix=10, iy=10)
        assert cell.get("id").getInfo() == "EPSG:4326_10_E10-S10"

    def test_cell_clamps_to_projection_bounds(self):
        cell = ee.Feature.geetools.cell(100, ix=3, iy=1)
        assert cell.geometry().coordinates().getInfo() == [
            [[120, 10], [180, 10], [180, 90], [120, 90], [120, 10]]
        ]

    def test_cell_with_projected_crs(self):
        cell = ee.Feature.geetools.cell(1000, crs="EPSG:3857")
        assert cell.get("id").getInfo() == "EPSG:3857_1000_E00-S00"

    def test_cell_with_polar_crs(self):
        cell = ee.Feature.geetools.cell(2_000_000, crs="EPSG:3031")
        assert cell.get("id").getInfo() == "EPSG:3031_2000000_E00-S00"
        assert cell.geometry().coordinates().getInfo()


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
