"""Tools for the ``ee.Initialize`` function."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import ee
from google.oauth2.credentials import Credentials

from geetools.accessors import register_function_accessor


@register_function_accessor(ee.Initialize, "geetools")
class InitializeAccessor:
    """Toolbox for the ``ee.Initialize`` function."""

    def __init__(self, obj: Callable):
        """Initialize the class."""
        self._obj = obj

    @staticmethod
    def from_user(name: str = "", credential_pathname: str = "") -> None:
        """Initialize Earthengine API using a specific user.

        Equivalent to the ``ee.initialize`` function but with a specific credential file stored in the machine by the ``ee.Authenticate.to_user`` function.

        Args:
            name: The name of the user as saved when created. use default if not set
            credential_pathname: The path to the folder where the credentials are stored. If not set, it uses the default path

        Example:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize.from_user("test")

                # check that GEE is connected
                ee.Number(1).getInfo()
        """
        name = f"credentials{name}"
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_path = Path(credential_pathname).parent

        try:
            tokens = json.loads((credential_path / name).read_text())
            refresh_token = tokens["refresh_token"]
            client_id = tokens["client_id"]
            client_secret = tokens["client_secret"]
            credentials = Credentials(
                None,
                refresh_token=refresh_token,
                token_uri=ee.oauth.TOKEN_URI,
                client_id=client_id,
                client_secret=client_secret,
                scopes=ee.oauth.SCOPES,
            )
        except Exception:
            msg = "Please register this user first by using geetools.User.create first"
            raise ee.EEException(msg)

        ee.Initialize(credentials)
