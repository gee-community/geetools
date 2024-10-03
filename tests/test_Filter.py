"""Test the Filter class methods."""
import ee


class TestDateRange:
    """Test the dateRange method."""

    def test_dateRange_with_daterange(self, l8_sr_raw):
        filter = ee.Filter.geetools.dateRange(ee.DateRange("2018-01-01", "2019-01-01"))
        filtered_col = l8_sr_raw.filter(filter)
        assert filtered_col.size().getInfo() == 165030
