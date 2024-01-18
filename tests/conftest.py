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


# -- fixtures that will be used throughout the tests ---------------------------
@pytest.fixture(scope="session")
def amazonas() -> ee.FeatureCollection:
    """Return the Amazonas state from colombia."""
    level2 = ee.FeatureCollection("FAO/GAUL/2015/level2")
    colombia = level2.filter(ee.Filter.eq("ADM0_NAME", "Colombia"))
    return colombia.filter(ee.Filter.eq("ADM1_NAME", "Amazonas"))


@pytest.fixture(scope="session")
def s2_sr(amazonas) -> ee.ImageCollection:
    """Return a copernicus based collection.

    the 100 first images of the Sentinel-2 Surface Reflectance ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("COPERNICUS/S2_SR")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture(scope="session")
def s2(amazonas) -> ee.ImageCollection:
    """Return a copernicus based collection.

    the 100 first images of the Sentinel-2 Surface Reflectance ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("COPERNICUS/S2")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture(scope="session")
def l8_toa(amazonas) -> ee.ImageCollection:
    """Return a landsat based collection.

    the 100 first images of the landast 8 TOA ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )
