"""Test the Integer placeholder object."""
import ee
import pytest


class TestInteger:
    """Test the Integer placeholder class."""

    def test_init(self):
        with pytest.raises(NotImplementedError):
            ee.Integer()

    def test_name(self):
        assert ee.Integer.__name__ == "Integer"
