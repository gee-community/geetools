"""Test all the deprecated methods that have not been kept in the new implementation."""

from datetime import datetime

import pytest

import geetools


class TestVizualisation:
    """Test methods from the deprecated_visualization module."""

    def test_stretch_std(self):
        with pytest.raises(NotImplementedError):
            geetools.visualization.stretch_std(None, None)

    def test_stretch_percentile(self):
        with pytest.raises(NotImplementedError):
            geetools.visualization.stretch_percentile(None, None)


class TestDate:
    """Test methods from the deprecated_date module."""

    def test_millis_to_datetime(self):
        with pytest.deprecated_call():
            date = geetools.date.millisToDatetime(1527804000000)
            assert date == datetime.strptime("2018-06-01", "%Y-%m-%d")
