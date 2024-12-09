"""Test the utils module."""

from geetools import utils


class TestFormatDescription:
    """Test the utils.format_description function."""

    def test_valid_description(self):
        """Test a valid description."""
        description = "This is a valid description 123.,:;_-"
        result = utils.format_description(description)
        assert result == "This_is_a_valid_description_123.,:;_-"

    def test_replacements(self):
        """Test replacements."""
        description = "Testing / replacements ?!{}()"
        result = utils.format_description(description)
        assert result == "Testing_-_replacements_..::::"

    def test_long_description(self):
        description = "A" * 150
        result = utils.format_description(description)
        assert len(result) == 100

    def test_unicode_characters(self):
        description = "Unicode characters like é, ä, and ñ should be changed"
        result = utils.format_description(description)
        assert result == "Unicode_characters_like_e,_a,_and_n_should_be_changed"


class TestFormatAssetID:
    """Test the utils.format_asset_id function."""

    def test_valid_description(self):
        """Test a valid description."""
        description = "This is a valid description 123.,:;_-"
        result = utils.format_asset_id(description)
        assert result == "This_is_a_valid_description_123_____-"

    def test_replacements(self):
        """Test replacements."""
        description = "Testing / replacements ?!{}()"
        result = utils.format_asset_id(description)
        assert result == "Testing_-_replacements_______"

    def test_long_description(self):
        description = "A" * 150
        result = utils.format_asset_id(description)
        assert len(result) == 150

    def test_unicode_characters(self):
        description = "Unicode characters like é, ä, and ñ should be changed"
        result = utils.format_asset_id(description)
        assert result == "Unicode_characters_like_e__a__and_n_should_be_changed"
