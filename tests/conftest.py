"""Pytest session configuration."""

import json
import os
import string
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
        print("Using the EARTHENGINE_TOKEN from the environment")
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
@pytest.fixture
def amazonas() -> ee.FeatureCollection:
    """Return the Amazonas state from colombia."""
    level2 = ee.FeatureCollection("FAO/GAUL/2015/level2")
    colombia = level2.filter(ee.Filter.eq("ADM0_NAME", "Colombia"))
    return colombia.filter(ee.Filter.eq("ADM1_NAME", "Amazonas"))


@pytest.fixture
def s2_sr(amazonas) -> ee.ImageCollection:
    """Return a copernicus based collection.

    the 100 first images of the Sentinel-2 Surface Reflectance ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("COPERNICUS/S2_SR")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture
def vatican_buffer():
    """A 100 buffer around vatican city."""
    return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)


@pytest.fixture
def s2_sr_vatican_2020():
    """A single image from 2020 on top of vatican city from S2 SR collection."""
    src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
    return ee.Image(src)


@pytest.fixture
def s2(amazonas) -> ee.ImageCollection:
    """Return a copernicus based collection.

    the 100 first images of the Sentinel-2 Surface Reflectance ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("COPERNICUS/S2")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture
def l8_toa(amazonas) -> ee.ImageCollection:
    """Return a landsat based collection.

    the 100 first images of the landast 8 TOA ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture
def l8_sr_raw():
    """Return a defined image collection."""
    return ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")


@pytest.fixture
def date_instance():
    """Return a defined date instance."""
    return ee.Date("2020-01-01")


@pytest.fixture
def daterange_instance():
    """Return a DateRange instance."""
    return ee.DateRange("2020-01-01", "2020-01-31")


@pytest.fixture
def letter_list():
    """Return a defined list instance."""
    return ee.List([*string.ascii_lowercase[:3]])


@pytest.fixture
def int_list():
    """Return a defined list instance."""
    return ee.List([*range(1, 3)])


@pytest.fixture
def mix_list():
    """Return a defined list instance."""
    return ee.List(["a", 1, ee.Image(1)])


@pytest.fixture
def number_instance():
    """Return a defined number instance."""
    return ee.Number(1234.56785678)


@pytest.fixture
def string_instance():
    """Return a defined string instance."""
    return ee.String("foo")


@pytest.fixture
def format_string_instance():
    """Return a defined string instance."""
    return ee.String("{greeting} {name} !")


@pytest.fixture
def geom_instance():
    """Set a geometryCollection instance."""
    point0 = ee.Geometry.Point([0, 0], proj="EPSG:4326")
    point1 = ee.Geometry.Point([0, 1], proj="EPSG:4326")
    poly0 = point0.buffer(1, proj="EPSG:4326")
    poly1 = point1.buffer(1, proj="EPSG:4326").bounds(proj="EPSG:4326")
    line = ee.Geometry.LineString([point1, point0], proj="EPSG:4326")
    multiPoly = ee.Geometry.MultiPolygon([poly0, poly1], proj="EPSG:4326")
    return ee.Algorithms.GeometryConstructors.MultiGeometry(
        [multiPoly, poly0, poly1, point0, line],
        crs="EPSG:4326",
        geodesic=True,
        maxError=1,
    )


@pytest.fixture
def fc_instance():
    """Return a fc collection containing 1 single geometryCollection."""
    point0 = ee.Geometry.Point([0, 0], proj="EPSG:4326")
    point1 = ee.Geometry.Point([0, 1], proj="EPSG:4326")
    poly0 = point0.buffer(1, proj="EPSG:4326")
    poly1 = point1.buffer(1, proj="EPSG:4326").bounds(proj="EPSG:4326")
    line = ee.Geometry.LineString([point1, point0], proj="EPSG:4326")
    multiPoly = ee.Geometry.MultiPolygon([poly0, poly1], proj="EPSG:4326")
    geometryCollection = ee.Algorithms.GeometryConstructors.MultiGeometry(
        [multiPoly, poly0, poly1, point0, line],
        crs="EPSG:4326",
        geodesic=True,
        maxError=1,
    )
    return ee.FeatureCollection([geometryCollection])


@pytest.fixture
def gaul_3_countries():
    """Return Italy switzerland and France."""
    fc = ee.FeatureCollection("FAO/GAUL/2015/level0")
    return fc.filter(ee.Filter.inList("ADM0_CODE", [122, 237, 85]))


@pytest.fixture
def doy_image():
    """Return an Image instance with 2 random doy bands."""
    doy = ee.Image.random(seed=0).multiply(365).toInt().rename("doy1")
    return doy.rename("doy1").addBands(doy.rename("doy2"))
