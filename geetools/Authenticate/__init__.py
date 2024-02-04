"""Toolbox for the ``ee.Authenticate`` function."""
from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from shutil import move
from tempfile import TemporaryDirectory
from typing import Callable

import ee

from geetools.accessors import register_function_accessor


@register_function_accessor(ee.Authenticate, "geetools")
class AuthenticateAccessor:
    """Create an accessor for the ``ee.Authenticate`` function."""

    def __init__(self, obj: Callable):
        """Initialize the class."""
        self._obj = obj

    @staticmethod
    def new_user(name: str = "", credential_pathname: str = "") -> None:
        """Authenticate the user and save the credentials in a specific folder.

        Equivalent to ee.Authenticate but where the registered user will not be the default one (the one you get when running ee.initialize())

        Args:
            name: The name of the user. If not set, it will reauthenticate default.
            credential_pathname: The path to the folder where the credentials are stored. If not set, it uses the default path

        Example:
            .. code-block:: python

                import ee
                import geetools

                # cannot be displayed in the documentation as the creation
                # of a new user requires user interaction

                # geetools.User.create("secondary")
                # geetools.User.set("secondary")
                # ee.Number(1).getInfo()
        """
        name = f"credentials{name}"
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_path = Path(credential_pathname).parent

        # the authenticate method will write the credentials in the default
        # folder and with the default name. We have to save the existing one in tmp,
        # and then exchange places between the newly created and the existing one
        default = Path(ee.oauth.get_credentials_path())

        with TemporaryDirectory() as dir:
            with suppress(FileNotFoundError):
                move(default, Path(dir) / default.name)
            ee.Authenticate()
            move(default, credential_path / name)
            with suppress(FileNotFoundError):
                move(Path(dir) / default.name, default)

    @staticmethod
    def delete_user(name: str = "", credential_pathname: str = "") -> None:
        """Delete a user credential file.

        Args:
            name: The name of the user. If not set, it will delete the default user
            credential_pathname: The path to the folder where the credentials are stored. If not set, it uses the default path

        Example:
            .. code-block:: python

                import ee
                import geetools

                # cannot be displayed in the documentation as the creation
                # of a new user requires user interaction

                # geetools.User.create("secondary")
                # geetools.User.delete("secondary")
                # geetools.User.set("secondary")
                # will raise an error as the user does not exist anymore
        """
        name = f"credentials{name}"
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_path = Path(credential_pathname).parent
        with suppress(FileNotFoundError):
            (credential_path / name).unlink()

    @staticmethod
    def list_user(credential_pathname: str = "") -> list:
        """return all the available users in the set folder.

        To reach "default" simply omit the ``name`` parameter in the User methods

        Args:
            credential_pathname: The path to the folder where the credentials are stored. If not set, it uses the default path

        Returns:
            A list of strings with the names of the users

        Example:
            .. code-block:: python

                import ee
                import geetools

                geetools.User.list(
        """
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_path = Path(credential_pathname).parent
        files = [f for f in credential_path.glob("credentials*") if f.is_file()]
        return [f.name.replace("credentials", "") or "default" for f in files]

    @staticmethod
    def rename_user(new: str, old: str = "", credential_pathname: str = "") -> None:
        """Rename a user without changing the credentials.

        Args:
            new: The new name of the user
            old: The name of the user to rename
            credential_pathname: The path to the folder where the credentials are stored. If not set, it uses the default path

        Example:
            .. code-block:: python

                import ee
                import geetools

                geetools.user.create("secondary")
                geetools.User.rename("secondary", "new_default")
                geetools.User.list()
        """
        old = f"credentials{old}"
        new = f"credentials{new}"
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_path = Path(credential_pathname).parent
        with suppress(FileNotFoundError):
            (credential_path / old).rename(credential_path / new)
