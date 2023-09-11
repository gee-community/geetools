"""Pytest session configuration."""

import os
from pathlib import Path

import ee
import httplib2
import pytest


def pytest_configure() -> None:
    """Initialize earth engine according to the environment.

    It will use the creddential file if the EARTHENGINE_TOKEN env variable exist.
    Otherwise it use the simple Initialize command (asking the user to register if necessary).
    """
    # only do the initialization if the credential are missing
    if not ee.data._credentials:

        # if the credentials token is asved in the environment use it
        if "EARTHENGINE_TOKEN" in os.environ:

            # write the token to the appropriate folder
            ee_token = os.environ["EARTHENGINE_TOKEN"]
            credential_folder_path = Path.home() / ".config" / "earthengine"
            credential_folder_path.mkdir(parents=True, exist_ok=True)
            credential_file_path = credential_folder_path / "credentials"
            credential_file_path.write_text(ee_token)

        # if the user is in local development the authentication should
        # already be available
        ee.Initialize(http_transport=httplib2.Http())


@pytest.fixture
def number_instance():
    """Return a defined number instance."""
    return ee.Number(1234.56785678)


@pytest.fixture
def string_instance():
    """Return a defined string instance."""
    return ee.String("foo")
