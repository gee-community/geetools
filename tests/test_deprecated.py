"""Test all the deprecated methods that have not been kept in the new implementation."""


import pytest

import geetools


class TestDecisionTree:
    """Test the methods from the deprecated_decision_tree module."""

    def test_deprecated_binary(self):
        with pytest.raises(NotImplementedError):
            geetools.decision_tree.binary(None, None)


class TestImageCollection:
    """Test the deprecated_imagecollection module."""

    def test_get_id(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.getId(None)

    def test_wrapper(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.wrapper(None)

    def test_merge_geometry(self, s2_sr, data_regression):
        with pytest.deprecated_call():
            geom = geetools.imagecollection.mergeGeometries(s2_sr.limit(10))
            data_regression.check(geom.getInfo())

    def test_data2pandas(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.data2pandas(None)

    def test_tobands(self, s2_sr, data_regression):
        with pytest.deprecated_call():
            image = geetools.imagecollection.toBands(s2_sr.limit(3))
            data_regression.check(image.bandNames().getInfo())

    def test_enumerate_property(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.enumerateProperty(None, None)

    def test_enumerate_simple(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.enumerateSimple(None)

    def test_get_values(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.getValues(None, None)

    def test_parametrize_property(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.parametrizeProperty(None, None, None, None)

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
