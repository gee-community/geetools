"""Test the Date class methods."""
import ee
import pytest

import geetools  # noqa: F401


class TestToDatetime:
    """Test the toDatetime method."""

    def test_to_datetime(self, date_instance):
        datetime = date_instance.geetools.to_datetime()
        assert datetime.year == 2020
        assert datetime.month == 1
        assert datetime.day == 1

    def test_to_datetime_timezone(self, date_instance):
        dt = date_instance.geetools.to_datetime("America/Buenos_Aires")
        # Buenos Aires time is -3
        assert dt.year == 2019
        assert dt.month == 12
        assert dt.day == 31
        assert dt.hour == 21


class TestGetUnitSinceEpoch:
    """Test the getUnitSinceEpoch method."""

    def test_unit_since_epoch(self, date_instance):
        unit = date_instance.geetools.getUnitSinceEpoch("year")
        assert unit.getInfo() >= 49  # 2020 - 1970

    def test_wrong_unit(self, date_instance):
        with pytest.raises(ValueError):
            date_instance.geetools.getUnitSinceEpoch("foo")


class TestFromEpoch:
    """Test the fromEpoch method."""

    def test_from_epoch(self):
        date = ee.Date.geetools.fromEpoch(49, "year")
        assert date.format("YYYY-MM-DD").getInfo() == "2019-01-01"

    def test_wrong_unit(self):
        with pytest.raises(ValueError):
            ee.Date.geetools.fromEpoch(49, "foo")


class TestFromDOY:
    """Test the fromDOY method."""

    def test_from_doy(self):
        date = ee.Date.geetools.fromDOY(1, 2020)
        assert date.format("YYYY-MM-DD").getInfo() == "2020-01-01"

    def test_wrong_year(self):
        # check GEE can use year < EPOCH
        date = ee.Date.geetools.fromDOY(1, 3)
        assert date.format("YYYY-MM-DD").getInfo() == "0003-01-01"

    def test_wrong_doy(self):
        # check that GEE can use > 365 doy
        date = ee.Date.geetools.fromDOY(367, 2020)
        assert date.format("YYYY-MM-DD").getInfo() == "2021-01-01"


class TestIsLeap:
    """Test the isLeap method."""

    def test_is_leap_1992(self):
        leap = ee.Date("1992-01-01").geetools.isLeap()
        assert leap.getInfo() == 1

    def test_is_leap_2000(self):
        leap = ee.Date("2000-01-01").geetools.isLeap()
        assert leap.getInfo() == 1

    def test_is_leap_1900(self):
        leap = ee.Date("1900-01-01").geetools.isLeap()
        assert leap.getInfo() == 0


class TestNow:
    """Test the now method."""

    def test_now(self):
        date = ee.Date.geetools.now()
        assert date.getInfo() is not None
