"""Tools for the :py:func:`ee.Initialize` function."""
from __future__ import annotations

import json
import os
from pathlib import Path

import ee
from deprecated.sphinx import deprecated
from ee._state import get_state
from google.oauth2.credentials import Credentials

from .accessors import register_function_accessor


@register_function_accessor(ee.Initialize, "geetools")
class InitializeAccessor:
    """Toolbox for the ``ee.Initialize`` function."""

    @staticmethod
    def from_user(name: str = "", credential_pathname: str | os.PathLike = "", project: str = ""):
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
        # set the user profile information
        name = f"credentials{name}"
        credential_pathname = credential_pathname or ee.oauth.get_credentials_path()
        credential_folder = Path(credential_pathname).parent
        credential_path = credential_folder / name

        # check if the user exists
        if not credential_path.exists():
            msg = "Please register this user first by using geetools.User.create first"
            raise ee.EEException(msg)

        # Set the credential object
        tokens = json.loads(credential_path.read_text())

        # init the credential object and identify if the saved json is a service account or a user account
        if "gserviceaccount" in tokens.get("client_email", ""):
            ee_user = tokens["client_email"]
            credentials = ee.ServiceAccountCredentials(ee_user, key_data=json.dumps(tokens))
            project = credentials.project_id
        else:
            credentials = Credentials(
                None,
                refresh_token=tokens["refresh_token"],
                token_uri=ee.oauth.TOKEN_URI,
                client_id=tokens["client_id"],
                client_secret=tokens["client_secret"],
                scopes=ee.oauth.SCOPES,
            )

        ee.Initialize(credentials, project=project)

    @staticmethod
    def from_service_account(private_key: str):
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
        # connect to GEE using a ServiceAccountCredential object
        ee_user = json.loads(private_key)["client_email"]
        credentials = ee.ServiceAccountCredentials(ee_user, key_data=private_key)
        ee.Initialize(credentials=credentials, project=credentials.project_id)

    @staticmethod
    @deprecated(version="1.18.0", reason="Use the state object from vanilla earth engine instead.")
    def project_id() -> str:
        """Get the project_id of the current account.

        Returns:
            The project_id of the connected profile.

        Examples:
            .. code-block::

                import ee, geetools

                ee.Initialize.geetools.project_id()
        """
        return get_state().cloud_api_user_project
