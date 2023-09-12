"""Test the Date class methods."""
import ee
import pytest

import geetools


class TestToDatetime:
    """Test the toDatetime method."""

    def test_to_datetime(self, date_instance):
        datetime = date_instance.geetools.toDatetime()
        assert datetime.year == 2020
        assert datetime.month == 1
        assert datetime.day == 1

    def test_deprecated_method(self, date_instance):
        with pytest.deprecated_call():
            datetime = geetools.tools.date.toDatetime(date_instance)
            assert datetime.year == 2020
            assert datetime.month == 1
            assert datetime.day == 1

    @pytest.fixture
    def date_instance(self):
        """Return a defined date instance."""
        return ee.Date("2020-01-01")
