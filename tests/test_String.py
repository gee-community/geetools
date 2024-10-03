"""Test the String class methods."""
import ee


class TestEq:
    """Test the eq method."""

    def test_eq_with_same_string(self, string_instance):
        eq_number = string_instance.geetools.eq("foo")
        assert eq_number.getInfo() == 1

    def test_eq_with_different_string(self, string_instance):
        eq_number = string_instance.geetools.eq("bar")
        assert eq_number.getInfo() == 0


class TestFormat:
    """test the format method."""

    def test_format_with_dictionary(self, format_string_instance):
        params = {"greeting": "Hello", "name": "bob"}
        formatted_string = format_string_instance.geetools.format(params)
        assert formatted_string.getInfo() == "Hello bob !"

    def test_with_number(self, format_string_instance):
        params = {"greeting": "Hello", "name": ee.Number(1)}
        formatted_string = format_string_instance.geetools.format(params)
        assert formatted_string.getInfo() == "Hello 1 !"
