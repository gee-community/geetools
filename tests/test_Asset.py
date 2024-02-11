"""Test cases for the Asset class."""

import geetools


class TestStr:
    """Test the to_string method."""

    def test_str(self):
        asset = geetools.Asset("project/bar")
        assert str(asset) == "project/bar"
