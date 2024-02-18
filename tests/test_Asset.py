"""Test cases for the Asset class."""
import os
from unittest.mock import patch

import ee
import pytest

EARTHENGINE_PROJECT = os.environ.get("EARTHENGINE_PROJECT")


class TestConstructors:
    """Test the constructors of the Asset class."""

    @patch("ee.data._cloud_api_user_project", EARTHENGINE_PROJECT)
    def test_home(self):
        asset = ee.Asset.home()
        assert asset == f"projects/{EARTHENGINE_PROJECT}/assets"


class TestStr:
    """Test the to_string method."""

    def test_str(self):
        asset = ee.Asset("projects/bar")
        assert str(asset) == "projects/bar"

    def test_repr(self):
        asset = ee.Asset("projects/bar")
        assert repr(asset) == "ee.Asset('projects/bar')"

    def test_as_posix(self):
        asset = ee.Asset("projects/bar")
        assert asset.as_posix() == "projects/bar"

    def test_as_uri(self):
        asset = ee.Asset("projects/bar")
        assert asset.as_uri() == "https://code.earthengine.google.com/?asset=projects/bar"


class TestOperations:
    """Test the operations that can be run on the asset."""

    def test_truediv(self):
        asset = ee.Asset("projects/bar")
        assert asset / "foo" == "projects/bar/foo"

    def test_lt(self):
        asset = ee.Asset("projects/bar/foo")
        assert (asset < "projects/bar/foo/bar") is True
        assert (asset < "projects/bar/foo") is False
        assert (asset < "projects/bar") is False

    def test_gt(self):
        asset = ee.Asset("projects/bar/foo")
        assert (asset > "projects/bar/foo/bar") is False
        assert (asset > "projects/bar/foo") is False
        assert (asset > "projects/bar") is True

    def test_le(self):
        asset = ee.Asset("projects/bar/foo")
        assert (asset <= "projects/bar/foo/bar") is True
        assert (asset <= "projects/bar/foo") is True
        assert (asset <= "projects/bar") is False

    def test_ge(self):
        asset = ee.Asset("projects/bar/foo")
        assert (asset >= "projects/bar/foo/bar") is False
        assert (asset >= "projects/bar/foo") is True
        assert (asset >= "projects/bar") is True

    def test_eq(self):
        asset = ee.Asset("projects/bar")
        assert (asset == "projects/bar") is True
        assert (asset == "projects/bar/foo") is False

    def test_ne(self):
        asset = ee.Asset("projects/bar")
        assert (asset != "projects/bar") is False
        assert (asset != "projects/bar/foo") is True

    def test_idiv(self):
        asset = ee.Asset("projects/bar")
        asset /= "foo"
        assert asset == "projects/bar/foo"

    def test_is_absolute(self):
        assert ee.Asset("projects/bar/assets/foo").is_absolute() is True
        assert ee.Asset("projects/bar/foo").is_absolute() is False
        assert ee.Asset("projects/assets/foo").is_absolute() is False
        assert ee.Asset("bar/assets/foo").is_absolute() is False
        with pytest.raises(ValueError):
            ee.Asset("projects/bar").is_absolute(raised=True)

    @patch("ee.data._cloud_api_user_project", EARTHENGINE_PROJECT)
    def test_is_user_project(self):
        assert ee.Asset(f"projects/{EARTHENGINE_PROJECT}/assets/foo").is_user_project() is True
        assert ee.Asset("projects/foo").is_user_project() is False
        with pytest.raises(ValueError):
            ee.Asset("projects/foo").is_user_project(raised=True)

    @patch("ee.data._cloud_api_user_project", EARTHENGINE_PROJECT)
    def test_expanduser(self):
        asset = ee.Asset("~/foo").expanduser()
        assert asset == f"projects/{EARTHENGINE_PROJECT}/assets/foo"


class TestProperties:
    """Test the properties of the Asset class."""

    pass


class TestServerMethods:
    """Test methods that are run on the server."""

    def test_exists(self):
        asset = ee.Asset("projects/bar")
        with patch("ee.data.getInfo", return_value={"type": "Folder"}):
            assert asset.exists() is True
        with patch("ee.data.getInfo", return_value=None):
            assert asset.exists() is False
