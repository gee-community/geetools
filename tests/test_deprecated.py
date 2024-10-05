"""Test all the deprecated methods that have not been kept in the new implementation."""


import pytest

import geetools


class TestImageCollection:
    """Test the deprecated_imagecollection module."""

    def test_linear_function_band(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.linearFunctionBand(None, None, None, None)

    def test_linear_function_property(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.linearFunctionProperty(None, None, None, None)

    def linear_interpolation_property(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.linearInterpolationProperty(None, None, None, None)

    def test_gauss_function_band(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.gaussFunctionBand(None, None, None, None, None)

    def test_gauss_function_property(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.gaussFunctionProperty(None, None, None, None, None)

    def testnormal_distribution_property(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.normalDistributionProperty(None, None, None, None, None)

    def test_normal_distribution_band(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.normalDistributionBand(None, None, None, None, None)

    def test_moving_average(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.moving_average(None)


class TestAlgorithm:
    """Test the deprecated_algorithms module."""

    def test_pansharpenkernel(self):
        with pytest.raises(NotImplementedError):
            geetools.algorithms.pansharpenKernel(None, None)

    def test_pansharpenihsFusion(self):
        with pytest.raises(NotImplementedError):
            geetools.algorithms.pansharpenIhsFusion(None)


class TestComposite:
    """Test the deprecated_composite module."""

    def test_max(self, s2_sr):
        with pytest.deprecated_call():
            geetools.composite.max(s2_sr)

    def test_medoidScore(self, s2_sr):
        with pytest.raises(NotImplementedError):
            geetools.composite.medoidScore(s2_sr)
