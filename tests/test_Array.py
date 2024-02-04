"""Test the Array class methods."""
import ee
import pytest

import geetools
from geetools.Array import ArrayAccessor  # noqa: F401


class TestFull:
    """Test the full method."""

    def test_full_with_integers(self):
        full_array = ee.Array.geetools.full(3, 3, 1)
        assert full_array.getInfo() == [[1, 1, 1], [1, 1, 1], [1, 1, 1]]

    def test_full_with_floats(self):
        full_array = ee.Array.geetools.full(3.1, 3.1, 1.0)
        assert full_array.getInfo() == [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
        ]

    def test_full_with_ee_numbers(self):
        full_array = ee.Array.geetools.full(ee.Number(3), ee.Number(3), ee.Number(1))
        assert full_array.getInfo() == [[1, 1, 1], [1, 1, 1], [1, 1, 1]]

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            full_array = geetools.array.constant2DArray(3, 3, 1)
            assert full_array.getInfo() == [[1, 1, 1], [1, 1, 1], [1, 1, 1]]


class TestSet:
    """Test the set method."""

    def test_set_with_integers(self):
        array = ee.Array.geetools.full(3, 3, 1)
        set_array = array.geetools.set(1, 1, 0)
        assert set_array.getInfo() == [[1, 1, 1], [1, 0, 1], [1, 1, 1]]

    def test_set_with_floats(self):
        array = ee.Array.geetools.full(3.1, 3.1, 1.0)
        set_array = array.geetools.set(1, 1, 0.0)
        assert set_array.getInfo() == [
            [1.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
        ]

    def test_set_with_ee_numbers(self):
        array = ee.Array.geetools.full(3, 3, ee.Number(1))
        set_array = array.geetools.set(1, 1, ee.Number(0))
        assert set_array.getInfo() == [[1, 1, 1], [1, 0, 1], [1, 1, 1]]

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            array = ee.Array.geetools.full(3, 3, 1)
            set_array = geetools.array.set2DValue(array, (1, 1), 0)
            assert set_array.getInfo() == [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
