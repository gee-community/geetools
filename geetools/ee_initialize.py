"""Tools for the :py:func:`ee.Initialize` function."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import ee
import httplib2
from google.oauth2.credentials import Credentials

from .accessors import register_function_accessor

_project_id: str | None = None
"The project Id used by the current user."


@register_function_accessor(ee.Initialize, "geetools")
class InitializeAccessor:
    """Toolbox for the ``ee.Initialize`` function."""

    @staticmethod
    def from_user(name: str = "", credential_pathname: str = "", project: str = "") -> None:
        """Initialize Earthengine API using a specific user.

        Equivalent to the :py:func:`ee.Initialize` function but with a specific credential file stored in
        the machine by the :py:meth:`ee.Authenticate.geetools.new_user <geetools.ee_authenticate.AuthenticateAccessor.new_user>`
        function.

        Args:
            name: The name of the user as saved when created. use default if not set
            credential_pathname: The path to the folder where the credentials are stored. If not set, it uses the default path
            project: The project_id to use. If not set, it uses the default project_id of the saved credentials.

        Example:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize.from_user("<name of the saved user>")
        """
        # gather global variable to be modified
        global _project_id

        # set the user profile information
        name = f"credentials{name}"
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_folder = Path(credential_pathname).parent
        credential_path = credential_folder / name

        # check if the user exists
        if not credential_path.exists():
            msg = "Please register this user first by using geetools.User.create first"
            raise ee.EEException(msg)

        # Set the credential object and Init GEE API
        tokens = json.loads((credential_path / name).read_text())
        credentials = Credentials(
            None,
            refresh_token=tokens["refresh_token"],
            token_uri=ee.oauth.TOKEN_URI,
            client_id=tokens["client_id"],
            client_secret=tokens["client_secret"],
            scopes=ee.oauth.SCOPES,
        )
        ee.Initialize(credentials)

        # save the project_id in a dedicated global variable as it's not saved
        # from GEE side
        _project_id = project or tokens["project_id"]

    @staticmethod
    def from_service_account(private_key: str) -> None:
        """Initialize Earthengine API using a service account.

        Equivalent to the :py:func:`ee.Initialize` function but with a specific service account json key.

        Args:
            private_key: The private key of the service account in json format.

        Example:
            .. code-block:: python

                import ee
                import geetools

                private_key = "your_private_key"

                ee.Initialize.from_service_account(private_key)
        """
        # gather global variable to be modified
        global _project_id

        # connect to GEE using a temp file to avoid writing the key to disk
        with tempfile.TemporaryDirectory() as temp_dir:
            file = Path(temp_dir) / "private_key.json"
            file.write_text(private_key)
            ee_user = json.loads(private_key)["client_email"]
            _project_id = json.loads(private_key)["project_id"]
            credentials = ee.ServiceAccountCredentials(ee_user, str(file))
            ee.Initialize(credentials=credentials, http_transport=httplib2.Http())

    @staticmethod
    def project_id() -> str:
        """Get the project_id of the current account.

        Returns:
            The project_id of the connected profile

        Raises:
            RuntimeError: If the account is not initialized.

        Examples:
            .. code-block::

                import ee, geetools

                ee.Initialize.geetools.project_id()
        """
        if _project_id is None:
            raise RuntimeError("The GEE account is not initialized")
        return _project_id
