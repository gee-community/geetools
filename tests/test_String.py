"""Test the String class methods."""
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


class TestFormat:
    """test the format method."""

    def test_format_with_dictionary(self, format_string_instance):
        params = {"greeting": "Hello", "name": "bob"}
        formatted_string = format_string_instance.geetools.format(params)
        assert formatted_string.getInfo() == "Hello bob !"

    def test_deprecated_format(self, format_string_instance):
        with pytest.deprecated_call():
            params = {"greeting": "Hello", "name": "bob"}
            formatted_string = geetools.string.format(format_string_instance, params)
            assert formatted_string.getInfo() == "Hello bob !"
