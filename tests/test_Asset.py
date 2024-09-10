"""Test cases for the Asset class."""
import os
from unittest.mock import patch

import ee
import pytest

import geetools  # noqa F401

EARTHENGINE_PROJECT = os.environ.get("EARTHENGINE_PROJECT")


class TestConstructors:
    """Test the constructors of the Asset class."""

    @patch("ee.data._cloud_api_user_project", EARTHENGINE_PROJECT)
    def test_home(self):
        asset = ee.Asset.home()
        assert asset == f"projects/{EARTHENGINE_PROJECT}/assets"

    def test_not_absolute(self):
        asset = ee.Asset("/projects/foo/bar")
        assert asset == "projects/foo/bar"


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

    def test_as_description(self):
        asset = ee.Asset(f"projects/{EARTHENGINE_PROJECT}/assets/a weird name")
        assert asset.as_description() == "a_weird_name"


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

    def test_is_relative_to(self):
        asset1 = ee.Asset("projects/bar")
        asset2 = ee.Asset("projects/bar/foo")
        assert asset2.is_relative_to(asset1) is True
        assert asset1.is_relative_to(asset2) is False

    def test_joinpath(self):
        asset = ee.Asset("projects/bar")
        assert asset.joinpath("foo") == "projects/bar/foo"

    def test_match(self):
        asset = ee.Asset("projects/bar/foo")
        assert asset.match("projects/bar/*") is True
        assert asset.match("projects/bar") is False
        assert asset.match("**/foo") is True

    def test_with_name(self):
        asset = ee.Asset("projects/bar")
        assert asset.with_name("foo") == "projects/foo"


class TestProperties:
    """Test the properties of the Asset class."""

    def test_parts(self):
        asset = ee.Asset("projects/bar/foo")
        assert asset.parts == ("projects", "bar", "foo")

    def test_parent(self):
        asset = ee.Asset("projects/test/assets/foo/bar/baz")
        assert asset.parent == "projects/test/assets/foo/bar"

    def test_parents(self, data_regression):
        asset = ee.Asset("projects/test/assets/foo/bar/baz")
        parents = [str(p) for p in asset.parents]
        data_regression.check(parents)

    def test_name(self):
        asset = ee.Asset("projects/bar/foo")
        assert asset.name == "foo"

    def test_st_size(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        assert (gee_test_folder / "folder/image").st_size == 31
        with pytest.raises(ValueError):
            gee_test_folder.st_size

    def test_owner(self):
        assert ee.Asset("projects/bar/assets/foo").owner == "bar"
        with pytest.raises(ValueError):
            ee.Asset("projects/foo").owner


class TestServerMethods:
    """Test methods that are run on the server."""

    def test_exists(self, gee_test_folder):
        # cast to asset as it's just a regular path in pytest-gee
        gee_test_folder = ee.Asset(gee_test_folder)

        assert gee_test_folder.exists() is True
        assert (gee_test_folder / "folder").exists() is True
        assert (gee_test_folder / "folder" / "image").exists() is True
        assert (gee_test_folder / "folder" / "fake").exists() is False

    def test_is_project(self):
        assert ee.Asset(f"projects/{EARTHENGINE_PROJECT}/assets").is_project() is True
        assert ee.Asset("projects/bar").is_project() is False
        with pytest.raises(ValueError):
            ee.Asset("projects/bar").is_project(raised=True)

    def test_is_folder(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        assert (gee_test_folder / "folder").is_folder() is True
        assert (gee_test_folder / "folder" / "image").is_folder() is False

    def test_is_image(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        assert (gee_test_folder / "folder" / "image").is_image() is True
        assert (gee_test_folder / "folder").is_feature_collection() is False

    def test_is_type(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        assert gee_test_folder.is_type("FOLDER") is True
        with pytest.raises(ValueError):
            gee_test_folder.is_type("IMAGE", raised=True)

    def test_iterdir(self, gee_hash, gee_test_folder, data_regression):
        folder = ee.Asset(gee_test_folder) / "folder"
        assets = [
            str(a).replace(EARTHENGINE_PROJECT, "ee-project").replace(gee_hash, "hash")
            for a in folder.iterdir()
        ]
        data_regression.check(assets)

    def test_iterdir_recursive(self, gee_hash, gee_test_folder, data_regression):
        folder = ee.Asset(gee_test_folder) / "folder"
        assets = [
            str(a).replace(EARTHENGINE_PROJECT, "ee-project").replace(gee_hash, "hash")
            for a in folder.iterdir(recursive=True)
        ]
        data_regression.check(assets)

    def test_iterdir_nodir(self, gee_test_folder):
        with pytest.raises(ValueError):
            (ee.Asset(gee_test_folder) / "folder" / "image").iterdir()

    def test_glob(self, gee_test_folder, gee_hash, data_regression):
        folder = ee.Asset(gee_test_folder) / "folder"
        assets = [
            str(a).replace(EARTHENGINE_PROJECT, "ee-project").replace(gee_hash, "hash")
            for a in folder.glob("*/image")
        ]
        data_regression.check(assets)

    def test_rglob(self, gee_test_folder, gee_hash, data_regression):
        folder = ee.Asset(gee_test_folder) / "folder"
        assets = [
            str(a).replace(EARTHENGINE_PROJECT, "ee-project").replace(gee_hash, "hash")
            for a in folder.rglob("*/image")
        ]
        data_regression.check(assets)

    def test_mkdir(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = (gee_test_folder / "new_mkdir_folder").mkdir()
        assert asset.is_folder() is True
        ee.data.deleteAsset(str(asset))

    def test_mkdir_exists(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        with pytest.raises(ValueError):
            (gee_test_folder / "folder").mkdir()
        asset = (gee_test_folder / "folder").mkdir(exist_ok=True)
        assert asset.is_folder() is True

    def test_mkdir_parents(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        with pytest.raises(ValueError):
            (gee_test_folder / "new_mkdir_parent" / "subfolder").mkdir()
        asset = (gee_test_folder / "new_mkdir_parent" / "subfolder").mkdir(parents=True)
        assert asset.parent.is_folder() is True
        assert asset.is_folder() is True
        ee.data.deleteAsset(str(asset))
        ee.data.deleteAsset(str(asset.parent))

    def test_unlink(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "unlink_folder" / "image"
        assert asset.is_image() is True
        asset.unlink()
        assert asset.exists() is False

    def test_unlink_not_exists(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        with pytest.raises(ValueError):
            (gee_test_folder / "new_unlink_folder").unlink()

    def test_delete(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = (gee_test_folder / "new_delete_folder").mkdir()
        assert asset.is_folder() is True
        asset.delete()
        assert asset.exists() is False

    def test_rmdir_dry_run(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = (gee_test_folder / "test_rmdir_folder").mkdir()
        assert asset.is_folder() is True
        assets = asset.rmdir(dry_run=True)
        assert assets == [str(asset)]
        assert asset.exists() is True
        ee.data.deleteAsset(str(asset))

    def test_rmdir(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = (gee_test_folder / "test_rmdir_folder").mkdir()
        assert asset.is_folder() is True
        asset.rmdir()
        assert asset.exists() is False

    def test_rmdir_not_folder(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        with pytest.raises(ValueError):
            (gee_test_folder / "folder" / "image").rmdir()

    def test_rmdir_recursive_dry_run(self, gee_hash, gee_test_folder, data_regression):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "rmdir_folder"
        assets = [
            str(a).replace(EARTHENGINE_PROJECT, "ee-project").replace(gee_hash, "hash")
            for a in asset.rmdir(recursive=True)
        ]
        data_regression.check(assets)

    def test_rmdir_recursive(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "rmdir_folder"
        asset.rmdir(recursive=True, dry_run=False)
        assert asset.exists() is False

    def test_copy(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "copy_folder" / "image"
        new_asset = gee_test_folder / "copy_folder" / "new_image"
        asset.copy(new_asset)
        assert asset.exists() is True
        assert new_asset.exists() is True

    def test_copy_folder(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "copy_folder"
        new_asset = gee_test_folder / "new_copy_folder"
        asset.copy(new_asset)
        assert asset.exists() is True
        assert new_asset.exists() is True

    def test_move(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "move_folder" / "image"
        new_asset = gee_test_folder / "move_folder" / "new_image"
        asset.move(new_asset)
        assert asset.exists() is False
        assert new_asset.exists() is True

    def test_move_folder(self, gee_test_folder):
        gee_test_folder = ee.Asset(gee_test_folder)
        asset = gee_test_folder / "move_folder"
        new_asset = gee_test_folder / "new_move_folder"
        asset.move(new_asset)
        assert asset.exists() is False
        assert new_asset.exists() is True


class TestSetProperties:
    """Test the ``set_properties`` method."""

    def test_set_properties(self, gee_test_folder):
        asset = ee.Asset(gee_test_folder) / "folder" / "image"
        asset.setProperties(foo="bar")
        assert ee.Image(asset.as_posix()).get("foo").getInfo() == "bar"
