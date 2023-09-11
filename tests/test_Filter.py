"""Test the Filter class methods."""
import ee
import pytest

import geetools


class TestDateRange:
    """Test the dateRange method."""

    def test_dateRange_with_daterange(self, image_collection):
        filter = ee.Filter.geetools.dateRange(ee.DateRange("2018-01-01", "2019-01-01"))
        filtered_col = image_collection.filter(filter)
        assert filtered_col.size().getInfo() == 143188

    def test_deprecated_method(self, image_collection):
        with pytest.deprecated_call():
            dateRange = ee.DateRange("2018-01-01", "2019-01-01")
            filter = geetools.filters.dateRange(dateRange)
            filtered_col = image_collection.filter(filter)
            assert filtered_col.size().getInfo() == 143188

    @pytest.fixture
    def image_collection(self):
        """Return a defined image collection."""
        return ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
