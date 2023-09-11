"""Test the Array class methods."""
import ee


class TestFull:
    """Test the full method."""

    def test_full_with_integers(self):
        full_array = ee.Array.geetools.full(3, 3, 1)
        assert full_array.getInfo() == [[1, 1, 1], [1, 1, 1], [1, 1, 1]]

    def test_full_with_floats(self):
        full_array = ee.Array.geetools.full(3, 3, 1.0)
        assert full_array.getInfo() == [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
        ]

    def test_full_with_ee_numbers(self):
        full_array = ee.Array.geetools.full(3, 3, ee.Number(1))
        assert full_array.getInfo() == [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
