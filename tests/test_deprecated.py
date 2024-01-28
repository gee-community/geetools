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


class TestElement:
    """Test the methods from the deprecated_element module."""

    def test_fillNull(self):
        with pytest.raises(NotImplementedError):
            geetools.element.fillNull(None, None)
