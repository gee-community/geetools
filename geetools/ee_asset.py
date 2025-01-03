"""An Asset management class mimicking the ``pathlib.Path`` class behaviour."""
from __future__ import annotations

import os
import re
from pathlib import PurePosixPath

import ee
import ee.data

from .accessors import _register_extention
from .utils import format_description


@_register_extention(ee)
class Asset(os.PathLike):
    """An Asset management class mimicking the ``pathlib.Path`` class behaviour."""

    def __init__(self, *args):
        """Initialize the Asset class.

        .. note::
            An asset cannot be an absolute path like in a normal filesystem and thus any trailing "/" will be removed.
        """
        if len(args) == 0:
            self._path = f"projects/{ee.data._cloud_api_user_project}/assets/"
        else:
            self._path = args[0]._path if isinstance(args[0], Asset) else PurePosixPath(*args)
            project_assets = PurePosixPath(str(self._path)[1:])
            self._path = project_assets if self._path.is_absolute() else self._path

    def __str__(self):
        """Transform the asset id to a string."""
        return self.as_posix()

    def __repr__(self):
        """Return the asset object representation as a string."""
        return f"ee.{type(self).__name__}('{self.as_posix()}')"

    def __truediv__(self, other: os.PathLike) -> Asset:
        """Override the division operator to join the asset with other paths."""
        return Asset(self._path / str(other))

    def __lt__(self, other: os.PathLike) -> bool:
        """Override the less than operator to compare the asset with other paths."""
        return self._path < PurePosixPath(str(other))

    def __gt__(self, other: os.PathLike) -> bool:
        """Override the greater than operator to compare the asset with other paths."""
        return self._path > PurePosixPath(str(other))

    def __le__(self, other: os.PathLike) -> bool:
        """Override the less than or equal operator to compare the asset with other paths."""
        return self._path <= PurePosixPath(str(other))

    def __ge__(self, other: os.PathLike) -> bool:
        """Override the greater than or equal operator to compare the asset with other paths."""
        return self._path >= PurePosixPath(str(other))

    def __eq__(self, other: object) -> bool:
        """Override the equal operator to compare the asset with other paths."""
        return self._path == PurePosixPath(str(other))

    def __ne__(self, other: object) -> bool:
        """Override the not equal operator to compare the asset with other paths."""
        return self._path != PurePosixPath(str(other))

    def __idiv__(self, other: os.PathLike) -> Asset:
        """Override the in-place division operator to join the asset with other paths."""
        return Asset(self._path / str(other))

    def __fspath__(self):
        """Implement the os.Pathlike interface."""
        return self.as_posix()

    def __hash__(self):
        """make the Asset object hashable."""
        return hash(self.as_posix())

    def __getattr__(self, name):
        """Return the attribute of the path object."""
        return getattr(self, name)

    @classmethod
    def home(cls) -> Asset:
        """Return the root asset folder of the used cloud project.

        Returns:
            The root asset folder.

        Examples:
            .. code-block:: python

                ee.Asset.home()
        """
        return cls(f"projects/{ee.data._cloud_api_user_project}/assets/")

    def as_posix(self) -> str:
        """Return the asset id as a posix path.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.as_posix()

                # equivalent to
                str(asset)
        """
        return self._path.as_posix()

    def as_uri(self) -> str:
        """Return the asset id as an uri.

        The uri can be directly copy/pasted to your browser to see the asset in the GEE code editor.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.as_uri()
        """
        return f"https://code.earthengine.google.com/?asset={self.as_posix()}"

    def is_absolute(self, raised: bool = False) -> bool:
        """Return True if the asset is absolute.

        An absolute asset path starts with "projects" and contains "assets" at the 3rd position.
        We don't check if the project name exist in this method, simply the structure of the path.

        Args:
            raised: If True, raise an exception if the asset is not absolute. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.is_absolute()
        """
        # we decided not to enforce the length of the parts to still be able to use the
        # relative_to method of the Path class. Consequence is tis little trick in case
        # the asset is not absolute at all.
        parts = dict(enumerate(self.parts))
        if parts.get(0) == "projects" and parts.get(2) == "assets":
            return True
        else:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} is not absolute.")
            else:
                return False

    def is_user_project(self, raised: bool = False) -> bool:
        """Check if the current asset is in the same project as the user.

        Args:
            raised: If True, raise an exception if the asset is not in the same project. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.is_user_project()
        """
        if self.is_relative_to(self.home()._path):
            return True
        else:
            if raised is True:
                user_project = ee.data._cloud_api_user_project
                msg = f"Asset {self.as_posix()} is not in the same project as the user ({user_project})"
                raise ValueError(msg)
            else:
                return False

    def expanduser(self) -> Asset:
        """Return a new path with expanded ~ constructs.

        If one don't want to write the path with the complete project name, the method will build it for you.

        Examples:
            .. code-block:: python

                asset = ee.Asset("~/assets/folder/image")
                asset.expanduser()
        """
        return Asset(self.as_posix().replace("~", self.home().as_posix(), 1))

    def exists(self, raised: bool = False) -> bool:
        """Return True if the asset exists and/or the user has access to it.

        Args:
            raised: If True, raise an exception if the asset does not exist. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.exists()
        """
        try:
            ee.data.getAsset(self.as_posix())
            return True
        except ee.EEException:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} does not exist.")
            else:
                return False

    @property
    def parts(self):
        """Return the asset parts of the path.

        We will show all the parts from the root to the asset name.
        Remember that projects/user/assets is not part of the asset name but is part of the path.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.parts
        """
        return self._path.parts

    @property
    def parent(self):
        """Return the direct parent directory.

        It can go further up than the root folder if the asset is not absolute.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.parent
        """
        return Asset(self._path.parent)

    @property
    def parents(self):
        """Return the parent directories from the root folder.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.parents
        """
        # we remove the files that are not assets but are parsed by parents method
        parents = self._path.parents
        patterns = [r"^\.$", "^projects$", r"^projects/[^/]+$", r"^projects/[^/]+/assets$"]
        return [Asset(a) for a in parents if not any(re.match(p, str(a)) for p in patterns)]

    @property
    def name(self):
        """Return the asset name.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.name
        """
        return self._path.name

    @property
    def st_size(self):
        """Return the byte size of the file.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.st_size
        """
        # sanity checks
        self.exists(raised=True)
        if self.is_folder():
            raise ValueError(f"Asset {self.as_posix()} is a folder.")

        return int(ee.data.getAsset(self.as_posix())["sizeBytes"])

    def is_relative_to(self, other: os.PathLike) -> bool:
        """Return True if the asset is relative to another asset.

        Args:
            other: The other asset to compare with.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.is_relative_to("projects/ee-geetools/assets")
        """
        return self._path.is_relative_to(PurePosixPath(str(other)))

    def joinpath(self, *args) -> Asset:
        """Join the asset with other paths.

        Args:
            *args: The other paths to join with the asset.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.joinpath("other", "path")
        """
        return Asset(self._path.joinpath(*args))

    def match(self, *patterns) -> bool:
        """Return True if the asset matches the patterns.

        patterns: The patterns to match with the asset name.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.match("**/image")
        """
        return self._path.match(*patterns)

    def with_name(self, name: str) -> Asset:
        """Return the asset with the given name.

        Args:
            name: The new name for the asset.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.with_name("new_image")
        """
        return Asset(self._path.with_name(name))

    def is_image(self, raised: bool = False) -> bool:
        """Return ``True`` if the asset is an image.

        Args:
            raised: If True, raise an exception if the asset is not an image. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.is_image()
        """
        return self.is_type("IMAGE", raised)

    def is_image_collection(self, raised: bool = False) -> bool:
        """Return ``True`` if the asset is an image collection.

        Args:
            raised: If True, raise an exception if the asset is not an image collection. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image_collection")
                asset.is_image_collection()
        """
        return self.is_type("IMAGE_COLLECTION", raised)

    def is_feature_collection(self, raised: bool = False) -> bool:
        """Return ``True`` if the asset is a feature collection.

        Args:
            raised: If True, raise an exception if the asset is not a feature collection. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/feature_collection")
                asset.is_feature_collection()
        """
        return self.is_type("FEATURE_COLLECTION", raised) or self.is_type("TABLE", raised)

    def is_folder(self, raised: bool = False) -> bool:
        """Return ``True`` if the asset is a folder.

        Args:
            raised: If True, raise an exception if the asset is not a folder. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder")
                asset.is_folder()
        """
        return self.is_type("FOLDER", raised)

    @property
    def type(self) -> str:
        """Return the asset type.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.type
        """
        self.exists(raised=True)
        return ee.data.getAsset(self.as_posix())["type"]

    def is_project(self, raised: bool = False) -> bool:
        """Return ``True`` if the asset is a project.

        As project path are not assets, we cannot check their existence. We only check the path structure.

        Args:
            raised: If True, raise an exception if the asset is not a project. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets")
                asset.is_project()
        """
        if self.is_absolute() and len(self.parts) == 3:
            return True
        else:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} is not a project.")
            else:
                return False

    def is_type(self, asset_type: str, raised=False) -> bool:
        """Return ``True`` if the asset is of the specified type.

        Args:
            asset_type: The asset type to check for.
            raised: If True, raise an exception if the asset is not corresponding to the type. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.is_type("IMAGE")
        """
        self.exists(raised=True)
        if self.type == asset_type:
            return True
        else:
            if raised is True:
                raise ValueError(f"Asset {self.as_posix()} is not a {asset_type}.")
            else:
                return False

    def iterdir(self, recursive: bool = False) -> list:
        """Get the list of children of a container.

        Note:
            A container is an asset containing other assets, it can be a ``Folder`` or an ``ImageCollection``.

        Args:
            recursive: If True, get all the children recursively. Defaults to False.

        See Also:
            - :docstring:`ee.Asset.glob`
            - :docstring:`ee.Asset.rglob`

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder")
                asset.iterdir(recursive=True)
        """
        # sanity check on variables
        if not (self.is_project() or self.is_folder() or self.is_image_collection()):
            raise ValueError(
                f"Asset {self.as_posix()} is not a container and cannot contain other assets."
            )

        # no need for recursion if recursive is false we directly return the result of th API call
        if recursive is False:
            asset_ids = ee.data.listAssets({"parent": self.as_posix()})["assets"]
            return [Asset(asset["id"]) for asset in asset_ids]

        # recursive function to get all the assets
        def _recursive_get(folder, asset_list):
            for asset in ee.data.listAssets({"parent": str(folder)})["assets"]:
                asset_list.append(Asset(asset["id"]))
                if asset["type"] in ["FOLDER", "IMAGE_COLLECTION"] and recursive is True:
                    asset_list = _recursive_get(asset["id"], asset_list)
            return asset_list

        return _recursive_get(self, [])

    def mkdir(self, parents=False, exist_ok=False, image_collection: bool = False) -> Asset:
        """Create a container asset from the Asset path.

        Note:
            A container is an asset containing other assets, it can be a ``Folder`` or an ``ImageCollection``.

        Args:
            parents: If True, create all the parents of the folder. Defaults to False.
            exist_ok: If True, do not raise an error if the folder already exists. Defaults to False.
            image_collection: If True, create an image collection asset. Otherwise, create a folder asset. Defaults to False.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder")
                asset.mkdir(parents=True, exist_ok=True)
        """
        # check if the root is the same as home (only place where we can write to)
        self.is_absolute(raised=True)

        # if the complete one is in the list and exist_ok is True remove it from the list and
        # proceed else raise an error
        if self.exists() and exist_ok is False:
            raise ValueError(f"Asset {self.as_posix()} already exists.")

        # list the non-existing parents of the folder to create
        to_be_created = [p for p in self.parents if not p.exists()]

        # if parents is True, create all the parts that are in the list
        # else raise an error with the 1st parent name
        if len(to_be_created) > 0 and parents is False:
            raise ValueError(f'Parent Asset "{to_be_created[-1]}" does not exist.')

        # 2 option either there is 1 single element in the list or all the parents are included
        # we need to walk it in reversed to make sure the parents are build first.
        for p in reversed(to_be_created):
            ee.data.createFolder(p.as_posix())

        # now that all the parents are there, we can create the requested container
        if not self.exists():
            asset_type = "IMAGE_COLLECTION" if image_collection is True else "FOLDER"
            ee.data.createAsset({"type": asset_type}, self.as_posix())

        return self

    @property
    def owner(self):
        """Return the asset owner (project name).

        This method is only parsing the asset path and is not checking asset existence.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.owner
        """
        self.is_absolute(raised=True)
        return self.parts[1]

    def move(self, new_asset: Asset, overwrite: bool = False) -> Asset:
        """Move the asset to a target destination.

        Move this asset (any type) to the given target, and return a new ``Asset`` instance
        pointing to target. If target exists and overwrite is False the method will raise an
        error. Else it will silently delete the existing file. If the asset is a container the whole
        content will be moved as well. The initial content is removed after the move.

        Args:
            new_asset: The destination asset.
            overwrite: If True, overwrite the destination asset if it exists. Defaults to False.

        Returns:
            The new asset instance.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                new_asset = ee.Asset("projects/ee-geetools/assets/folder/new_image")
                asset.move(new_asset, overwrite=False)
        """
        # copy the assets
        self.copy(new_asset, overwrite=overwrite)

        # delete the original
        self.delete(recursive=True, dry_run=False)

        return new_asset

    def delete(self, recursive: bool = False, dry_run: bool | None = None) -> list:
        """Remove the asset.

        This method will delete an asset (any type) asset and all its potential children. By default, it is not recursive and will raise an error if the container is not empty.
        By setting the recursive argument to True, the method will delete all the children and the container asset (including potential subfolders).
        To avoid deleting important assets by accident the method is set to dry_run by default.

        Note:
            A container is an asset containing other assets, it can be a ``Folder`` or an ``ImageCollection``.

        Args:
            recursive: If True, delete all the children and the container asset. Defaults to False.
            dry_run: If True, do not delete the asset simply pass them to the output list. Defaults to True.

        Returns:
            The list of deleted assets.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder")
                asset.delete(recursive=True)
        """
        # init if it should be a dry-run or not
        # if we run a recursive rmdir the dry_run is set to True to avoid deleting too many things by accident
        # if we run a non-recursive rmdir the dry_run is set to False to delete the folder only
        dry_run = dry_run if dry_run is not None else recursive

        # define a delete function to change the behaviour of the method depending of the mode
        # in dry mode, the function only store the assets to be destroyed as a dictionary.
        # in non dry mode, the function store the asset names in a dictionary AND delete them.
        output = []

        def delete(asset):
            output.append(str(asset))
            dry_run is True or ee.data.deleteAsset(str(asset))

        is_container = self.is_folder() or self.is_image_collection()
        if recursive is True and is_container:

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

    # aliases
    def unlink(self) -> list:
        """``delete`` alias for singular assets."""
        # sanity check on variables
        if self.is_project() or self.is_folder() or self.is_image_collection():
            raise ValueError(f"Asset {self.as_posix()} is a container, use rmdir instead.")
        self.exists(raised=True)
        return self.delete()

    def rmdir(self, recursive: bool = False, dry_run: bool | None = None) -> list:
        """``delete`` alias for containers."""
        if not (self.is_project() or self.is_folder() or self.is_image_collection()):
            raise ValueError(f"Asset {self.as_posix()} is not a container, use unlink instead.")
        self.exists(raised=True)
        return self.delete(recursive, dry_run)

    def copy(self, new_asset: Asset, overwrite: bool = False) -> Asset:
        """Copy the asset to a target destination.

        Copy this asset (any type) to the given target, and return a new ``Asset`` instance
        pointing to target. If target exists and overwrite is False the method will raise an
        error. Else it will silently delete the existing asset. If the asset is a container the whole
        content will be moved as well.

        Args:
            new_asset: The destination asset.
            overwrite: If True, overwrite the destination asset if it exists. Defaults to False.

        Returns:
            The new asset instance.

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                new_asset = ee.Asset("projects/ee-geetools/assets/folder/new_image")
                asset.copy(new_asset, overwrite=False)
        """
        # exit if the destination asset exist and overwrite is False
        if new_asset.exists() and overwrite is False:
            raise ValueError(f"Asset {new_asset.as_posix()} already exists.")

        # make all the parents of the target asset if necessary
        if len(new_asset.parents) != 0:
            new_asset.parent.mkdir(parents=True, exist_ok=True)

        # copy the asset to the new destination. If the asset is a container, we need to move all its
        # content recursively to the new destination we recursively call this method on each
        # children of the asset if it's a folder it will loop again.
        if self.is_folder() or self.is_image_collection():
            new_asset.mkdir(True, True, self.is_image_collection())

            # if the asset is an image collection we need to copy the properties of the collection
            if self.is_image_collection():
                original_dict = ee.data.getAsset(self.as_posix())
                props = original_dict["properties"]
                if "startTime" in original_dict:
                    props["system:time_start"] = original_dict["startTime"]
                if "endTime" in original_dict:
                    props["system:time_end"] = original_dict["endTime"]
                new_asset.setProperties(**props)

            # copy the children objects
            for asset in self.iterdir():
                loc_asset = new_asset / asset._path.relative_to(self._path)
                asset.copy(loc_asset, overwrite=overwrite)
        else:
            ee.data.copyAsset(self.as_posix(), new_asset.as_posix(), allowOverwrite=True)

        return new_asset

    def glob(self, pattern: str) -> list:
        """Return a list of assets matching the pattern.

        Args:
            pattern: The pattern to match with the asset name.

        See Also:
            - :docstring:`ee.Asset.iterdir`
            - :docstring:`ee.Asset.rglob`

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder")
                asset.glob("image_*")
        """
        return [a for a in self.iterdir(recursive=False) if a.match(pattern)]

    def rglob(self, pattern: str) -> list:
        """Return a list of assets matching the pattern recursively.

        Args:
            pattern: The pattern to match with the asset name.

        See Also:
            - :docstring:`ee.Asset.glob`
            - :docstring:`ee.Asset.iterdir`

        Examples:
            .. code-block:: python

                asset = ee.Asset("projects/ee-geetools/assets/folder")
                asset.rglob("image_*")
        """
        return [a for a in self.iterdir(recursive=True) if a.match(pattern)]

    def as_description(self) -> str:
        """Transform the name of the Asset in to a description compatible string for a Task.

        Returns:
            The formatted description.
        """
        return format_description(self.name)

    def setProperties(self, **kwargs) -> ee.Asset:
        """Set properties of the asset.

        Args:
            **kwargs: The properties to set key, value pairs. To name normal properties simply use the name as key. For system properties, prefix it with "system:". Note that only the "time_start" and "time_end" are editable.

        Examples:
            .. code-block:: python

                # dates need to be set in milliseconds
                start = dt.datetime(2021, 1, 1).timestamp() * 1000
                asset = ee.Asset("projects/ee-geetools/assets/folder/image")
                asset.setProperties(**{"description": "new_description", "system:time_start": start})
        """
        # We need to retrieve the system properties.
        # They are named as in the server API and renamed inside this function.
        # The method raise error when we try to set something else that the authorized one.
        legit_keys = {"system:time_start": "start_time", "system:time_end": "end_time"}
        system = {k: v for k, v in kwargs.items() if k.startswith("system:")}
        for key in system.keys():
            if key not in legit_keys:
                raise ValueError(f"Property {key} is not a valid system property.")
        system = {legit_keys[k]: v for k, v in system.items()}

        # Specifying an update mask of 'properties' results in full replacement,
        # which isn't what we want. Instead, we name each property that we'll be
        # updating.
        props = {k: v for k, v in kwargs.items() if not k.startswith("system:")}
        update_mask = [f"properties.{k}" for k in props]

        # we can now update the asset by setting both system and asset properties
        ee.data.updateAsset(
            asset_id=self.as_posix(),
            asset={**system, "properties": props},
            update_mask=list(system.keys()) + update_mask,
        )

        return self
