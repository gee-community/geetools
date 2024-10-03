"""Test the ``DateRange`` class."""
import ee
import pytest


class TestSplit:
    """Test the ``split`` method."""

    def test_split(self, daterange_instance):
        list = daterange_instance.geetools.split(1, "day")
        first = ee.DateRange(list.get(0)).start()
        last = ee.DateRange(list.get(-1)).end()
        assert list.size().getInfo() == 30
        assert first.format("YYYY-MM-dd").getInfo() == "2020-01-01"
        assert last.format("YYYY-MM-dd").getInfo() == "2020-01-31"

    def split_with_end_outside(self, daterange_instance):
        list = daterange_instance.geetools.split(2, "month")
        first = ee.DateRange(list.get(0)).start()
        last = ee.DateRange(list.get(-1)).end()
        assert list.size().getInfo() == 1
        assert first.format("YYYY-MM-dd").getInfo() == "2020-01-01"
        assert last.format("YYYY-MM-dd").getInfo() == "2020-01-31"


class TestCheckUnit:
    """Test the ``check_unit`` method exception."""

    def test_check_unit(self):
        with pytest.raises(ValueError):
            ee.DateRange.geetools.check_unit("toto")
