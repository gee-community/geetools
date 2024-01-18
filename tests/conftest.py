"""Pytest session configuration."""

import json
import os
import tempfile
from pathlib import Path

import ee
import httplib2
import pytest


def pytest_configure() -> None:
    """Initialize earth engine according to the environment.

    It will use the creddential file if the EARTHENGINE_TOKEN env variable exist.
    Otherwise it use the simple Initialize command (asking the user to register if necessary).
    """
    # if the credentials token is asved in the environment use it
    if "EARTHENGINE_TOKEN" in os.environ:
        # extract data from the key
        ee_token = json.loads(os.environ["EARTHENGINE_TOKEN"])
        username, key = ee_token["username"], ee_token["key"]

        # Use them to init EE
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "token.json"
            file.write_text(json.dumps(key))
            credentials = ee.ServiceAccountCredentials(username, str(file))
            ee.Initialize(credentials)

    # if the user is in local development the authentication should
    # already be available
    else:
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
