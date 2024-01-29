"""Test the Filter class methods."""
import ee
import pytest

import geetools


class TestDateRange:
    """Test the dateRange method."""

    def test_dateRange_with_daterange(self, l8_sr_raw):
        filter = ee.Filter.geetools.dateRange(ee.DateRange("2018-01-01", "2019-01-01"))
        filtered_col = l8_sr_raw.filter(filter)
        assert filtered_col.size().getInfo() == 143188

    def test_deprecated_method(self, l8_sr_raw):
        with pytest.deprecated_call():
            dateRange = ee.DateRange("2018-01-01", "2019-01-01")
            filter = geetools.filters.dateRange(dateRange)
            filtered_col = l8_sr_raw.filter(filter)
            assert filtered_col.size().getInfo() == 143188
