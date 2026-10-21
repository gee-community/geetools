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

    def test_format_formatter(self):
        string = ee.String(
            "{greeting} developer, pi={number%.2f} start={start%tyyyy-MM-dd} end={end%tdd MMM yyyy}"
        )
        params = {
            "greeting": "Hello",
            "number": 3.1415,
            "start": 1577836800000,
            "end": "2021-01-01",
        }
        formatted_string = string.geetools.format(params)
        assert formatted_string.getInfo() == "Hello developer, pi=3.14 start=2020-01-01 end=01 Jan 2021"

    def test_format_missing(self):
        string = ee.String("{greeting} {missing}")
        params = {"greeting": "Hello", "number": 3.1415, "date": 1577836800000}
        formatted_string = string.geetools.format(params)
        assert formatted_string.getInfo() == "Hello "
