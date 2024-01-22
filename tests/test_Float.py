"""Test the Float placeholder object."""
import ee
import pytest


class TestFloat:
    """Test the Float placeholder class."""

    def test_init(self):
        with pytest.raises(NotImplementedError):
            ee.Float()

    def test_name(self):
        ee.Float.__name__ == "Float"
