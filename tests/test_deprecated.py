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
            date = geetools.date.millisToDatetime(1527811200000)
            assert date == datetime.strptime("2018-06-01", "%Y-%m-%d")


class TestCollection:
    """Test methods from the deprecated_collection module."""

    def test_enumerate(self):
        with pytest.raises(NotImplementedError):
            geetools.collection.enumerate(None)


class TestElement:
    """Test the methods from the deprecated_element module."""

    def test_fillNull(self):
        with pytest.raises(NotImplementedError):
            geetools.element.fillNull(None, None)


class TestDecisionTree:
    """Test the methods from the deprecated_decision_tree module."""

    def test_deprecated_binary(self):
        with pytest.raises(NotImplementedError):
            geetools.decision_tree.binary(None, None)
