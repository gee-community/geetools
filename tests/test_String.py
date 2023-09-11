"""Test the String class methods."""
import ee
import pytest

import geetools


class TestEq:
    """Test the eq method."""

    def test_eq_with_same_string(self, string_instance):
        eq_number = string_instance.geetools.eq("foo")
        assert eq_number.getInfo() == 1

    def test_eq_with_different_string(self, string_instance):
        eq_number = string_instance.geetools.eq("bar")
        assert eq_number.getInfo() == 0

    def test_deprecated_method(self, string_instance):
        with pytest.deprecated_call():
            eq_number = geetools.string.eq(string_instance, "foo")
            assert eq_number.getInfo() == 1

    @pytest.fixture
    def string_instance(self):
        """Return a defined string instance."""
        return ee.String("foo")


class TestFormat:
    """test the format method."""

    def test_format_with_dictionary(self, string_instance):
        formatted_string = string_instance.geetools.format(
            {"greeting": "Hello", "name": "bob"}
        )
        assert formatted_string.getInfo() == "Hello bob !"

    def test_deprecated_method(self, string_instance):
        with pytest.deprecated_call():
            formatted_string = geetools.string.format(
                string_instance, {"greeting": "Hello", "name": "bob"}
            )
            assert formatted_string.getInfo() == "Hello bob !"

    @pytest.fixture
    def string_instance(self):
        """Return a defined string instance."""
        return ee.String("{greeting} {name} !")
