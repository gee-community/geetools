"""Test all the deprecated methods that have not been kept in the new implementation."""

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


class TestCollection:
    """Test methods from the deprecated_collection module."""

    def test_enumerate(self):
        with pytest.raises(NotImplementedError):
            geetools.collection.enumerate(None)
