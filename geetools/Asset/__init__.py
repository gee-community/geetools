"""An Asset management class mimicking the ``pathlib.Path`` class behaviour."""
from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import Optional, Union

import ee

from geetools.accessors import _register_extention

pathlike = Union[str, os.PathLike]


@_register_extention(ee)
class Asset:
    """An Asset management class mimicking the ``pathlib.Path`` class behaviour."""

    def __init__(self, *args):
        """Initialize the Asset class."""
        self._path = PurePosixPath(*args)

    def __str__(self):
        """Transform the asset id to a string."""
        return self.as_posix()

    def __repr__(self):
        """Return the asset object representation as a string."""
        return f"{type(self).__name__}({self.as_posix()})"

    def __truediv__(self, other: pathlike) -> Asset:
        """Override the division operator to join the asset with other paths."""
        return Asset(self._path / other)

    def __lt__(self, other: pathlike) -> bool:
        """Override the less than operator to compare the asset with other paths."""
        return self._path < PurePosixPath(other)

    def __gt__(self, other: pathlike) -> bool:
        """Override the greater than operator to compare the asset with other paths."""
        return self._path > PurePosixPath(other)

    def __le__(self, other: pathlike) -> bool:
        """Override the less than or equal operator to compare the asset with other paths."""
        return self._path <= PurePosixPath(other)

    def __ge__(self, other: pathlike) -> bool:
        """Override the greater than or equal operator to compare the asset with other paths."""
        return self._path >= PurePosixPath(other)

    def __eq__(self, other: pathlike) -> bool:
        """Override the equal operator to compare the asset with other paths."""
        return self._path == PurePosixPath(other)

    def __ne__(self, other: pathlike) -> bool:
        """Override the not equal operator to compare the asset with other paths."""
        return self._path != PurePosixPath(other)

    def __idiv__(self, other: pathlike) -> Asset:
        """Override the in-place division operator to join the asset with other paths."""
        return Asset(self._path / other)

    def as_posix(self) -> str:
        """Return the asset id as a posix path."""
        return self._path.as_posix()

    def as_uri(self) -> str:
        """Return the asset id as a uri."""
        return f"https://code.earthengine.google.com/?asset={self.as_posix()}"

    def is_absolute(self, raised: bool = False) -> bool:
        """Return True if the asset is absolute."""
        if self.parts[0] == "projects" and self.parts[2] != "assets":
            return True
        else:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} is not absolute.")
            else:
                return False

    def is_same_project(self, raised: False) -> bool:
        """Check if the current asset is in the same project as the user.

        Args:
            raised: If True, raise an exception if the asset is not in the same project. Defaults to False.
        """
        if self.is_relative_to(self.home()):
            return True
        else:
            if raised is True:
                user_project = ee.data._cloud_api_user_project
                msg = f"Asset {self.as_posix()} is not in the same project as the user ({user_project})"
                raise ValueError(msg)
            else:
                return False

    @classmethod
    def home(cls) -> Asset:
        """Return the current project name."""
        return cls.__init__(f"projects/{ee.data._cloud_api_user_project}/assets/")

    def exists(self, raised: bool = False) -> bool:
        """Return True if the asset exists and/or has access to it.

        Args:
            raised: If True, raise an exception if the asset does not exist. Defaults to False.
        """
        try:
            ee.data.getAsset(self.as_posix())
            return True
        except ee.EEException:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} does not exist.")
            else:
                return False

    def expanduser(self):
        """Return a new path with expanded ~ constructs."""
        return Asset(self.as_posix().replace("~", self.home().as_posix(), 1))

    def parts(self):
        """Return the asset id parts."""
        return self._path.parts

    @property
    def parent(self):
        """Return the parent directory."""
        return Asset(self._path.parent)

    @property
    def parents(self):
        """Return the parent directories."""
        return [Asset(p) for p in self._path.parents]

    @property
    def name(self):
        """Return the asset name."""
        return self._path.name

    @property
    def st_size(self):
        """Return the byte size of the file."""
        self.exists(raised=True)
        return ee.data.getAsset(self.as_posix())["sizeBytes"]

    def is_relative_to(self, other: pathlike) -> bool:
        """Return True if the asset is relative to another asset."""
        return self._path.is_relative_to(PurePosixPath(other))

    def joinpath(self, *args) -> Asset:
        """Join the asset with other paths."""
        return Asset(self._path.joinpath(*args))

    def match(self, *patterns) -> bool:
        """Return True if the asset matches the patterns."""
        return self._path.match(*patterns, case_sensitive=True)

    def with_name(self, name: str) -> Asset:
        """Return the asset with the given name."""
        return Asset(self._path.with_name(name))

    def is_image(self) -> bool:
        """Return ``True`` if the asset is an image."""
        return self.is_type("IMAGE")

    def is_image_collection(self) -> bool:
        """Return ``True`` if the asset is an image collection."""
        return self.is_type("IMAGE_COLLECTION")

    def is_feature_collection(self) -> bool:
        """Return ``True`` if the asset is a feature collection."""
        return self.is_type("FEATURE_COLLECTION") or self.is_type("TABLE")

    def is_folder(self) -> bool:
        """Return ``True`` if the asset is a folder."""
        return self.is_type("FOLDER")

    def is_type(self, asset_type: str, raised=False) -> bool:
        """Return ``True`` if the asset is of the specified type.

        Args:
            asset_type: The asset type to check for.
            raised: If True, raise an exception if the asset is not corresponding to the type. Defaults to False.
        """
        self.exists(raised=True)
        if ee.data.getAsset(self.as_posix())["type"] == asset_type:
            return True
        else:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} is not a {asset_type}.")
            else:
                return False

    def iterdir(self, recursive: bool = False) -> list:
        """Get the list of children of a folder."""
        self.is_type("FOLDER", raised=True)

        # recursive function to get all the assets
        def _recursive_get(folder, asset_list):
            for asset in ee.data.listAssets({"parent": str(folder)})["assets"]:
                asset_list.append(Asset(asset["id"]))
                if asset["type"] == "FOLDER" and recursive is True:
                    asset_list = _recursive_get(asset["id"], asset_list)
                return asset_list

        return _recursive_get(self, [])

    def mkdir(self, parents=False, exist_ok=False):
        """Create a folder asset."""
        # check if the root is the same as home (only place where we can write to)
        self.is_same_project(raised=True)
        self.is_absolute(raised=True)

        # list all the parts of the path that needs to be created
        parent_to_ignore = [
            Asset("."),  # will appear in the parent list if the path is not absolute
            Asset("projects"),  # not an asset
            Asset(f"projects/{ee.data._cloud_api_user_project}"),  # not an asset
            self.home(),  # not an asset
        ]
        to_be_created = [p for p in self.parents if p not in parent_to_ignore and not p.exists()]

        # if the complete one is in the least and exist_ok is True remove it from the list and proceed
        # else raise an error
        if self in to_be_created:
            if exist_ok is True:
                to_be_created.remove(self)
            else:
                raise ValueError(f"Asset {self.as_posix()} already exists.")

        # if parents is True, create all the parts that are in the list
        # else raise an error with the 1st parent name
        if len(to_be_created) > 0:
            if parents is True:
                for p in reversed(to_be_created):
                    ee.data.createAsset({"type": "FOLDER"}, p.as_posix())
            else:
                raise ValueError(f'Parent Asset "{to_be_created[-1]}" does not exist.')

        # finally build self folder asset
        ee.data.createAsset({"type": "FOLDER"}, self.as_posix())

        return self

    @property
    def owner(self):
        """Return the asset owner (project name).

        Note:
            This method is only parsing the asset path and is not checking asset existence.
        """
        self.is_absolute(raised=True)
        return self.parts[1]

    def rename(self, new_name: str) -> Asset:
        """Rename the asset."""
        NotImplementedError()

    def replace(self, new_asset: Asset) -> Asset:
        """Replace the asset."""
        NotImplementedError()

    def rmdir(self, recursive: bool = False, dry_run: Optional[bool] = None) -> list:
        """Remove the asset folder.

        This method will delete a folder asset and all its childrend. by default it is not recursive and will raise an error if the folder is not empty.
        By setting the recursive argument to True, the method will delete all the children and the folder asset.
        To avoid deleting important assets by accident the method is set to dry_run by default.

        Args:
            recursive: If True, delete all the children and the folder asset. Defaults to False.
            dry_run: If True, do not delete the asset simply pass them to the output list. Defaults to True.

        Returns:
            The list of deleted assets.
        """
        # raise an error if the asset is not a folder
        self.is_type("FOLDER", raised=True)

        # init if it should be a dry-run or not
        # if we run a recursive rmdir the dry_run is set to True to avoid deleting too many things by accident
        # if we run a non-recursive rmdir the dry_run is set to False to delete the folder only
        dry_run = dry_run if dry_run is not None else recursive

        # define a delete function to change the behaviour of the method depending of the mode
        # in dry mode, the function only store the assets to be destroyed as a dictionary.
        # in non dry mode, the function store the asset names in a dictionary AND delete them.
        output = []

        def delete(asset):
            output.append(str(id))
            dry_run is True or ee.data.deleteAsset(str(id))

        if recursive is True:

            # get all the assets
            asset_list = self.iterdir(recursive=True)

            # split the files by nesting levels
            # we will need to delete the more nested files first
            assets_ordered: dict = {}
            for asset in asset_list:
                lvl = len(asset.parts)
                assets_ordered.setdefault(lvl, [])
                assets_ordered[lvl].append(asset)

            # delete all items starting from the more nested ones
            assets_ordered = dict(sorted(assets_ordered.items(), reverse=True))
            for lvl in assets_ordered:
                [delete(asset) for asset in assets_ordered[lvl]]

        # delete the initial folder/asset
        delete(self)

        return output

    def unlink(self):
        """Remove the asset."""
        self.exists(raised=True)
        ee.data.deleteAsset(self.as_posix())

    def delete(self):
        """Alias for unlink."""
        return self.unlink()
