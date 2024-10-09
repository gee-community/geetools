"""Pytest session configuration."""

import string

import ee
import pytest
import pytest_gee
import requests

S2_BAND_COMBO = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "SCL"]
"""Sentinel-2 band combination."""

L8_BAND_COMBO = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11"]
"""Landsat-8 band combination."""


def pytest_configure() -> None:
    """Initialize earth engine according to the environment."""
    pytest_gee.init_ee_from_service_account()


@pytest.fixture(scope="session")
def gee_folder_structure():
    """Override the default test folder structure."""
    point = ee.Geometry.Point([0, 0])
    return {
        "folder::Folder": {
            "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            "subfolder::Folder": {
                "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            },
        },
        "rmdir_folder::Folder": {
            "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            "subfolder::Folder": {
                "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            },
        },
        "move_folder::Folder": {
            "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            "subfolder::Folder": {
                "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            },
        },
        "copy_folder::Folder": {
            "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            "subfolder::Folder": {
                "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
            },
        },
        "unlink_folder::Folder": {
            "image": ee.Image(1).clipToBoundsAndScale(point.buffer(100), scale=30),
        },
    }


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
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .select(S2_BAND_COMBO)
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture
def vatican():
    """Return the vatican city."""
    level0 = ee.FeatureCollection("FAO/GAUL/2015/level0")
    return level0.filter(ee.Filter.eq("ADM0_NAME", "Holy See"))


@pytest.fixture
def vatican_buffer():
    """A 100 buffer around vatican city."""
    return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)


@pytest.fixture
def s2_sr_vatican_2020():
    """A single image from 2020 on top of vatican city from S2 SR collection."""
    src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
    return ee.Image(src).select(S2_BAND_COMBO)


@pytest.fixture
def l8_sr_vatican_2020():
    """A single image from 2020 on top of vatican city from L8 SR collection."""
    src = "LANDSAT/LC08/C02/T1/LC08_191031_20130711"
    return ee.Image(src).select(L8_BAND_COMBO)


@pytest.fixture
def l8_toa(amazonas) -> ee.ImageCollection:
    """Return a landsat based collection.

    the 100 first images of the landast 8 TOA ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_RT_TOA")
        .select(L8_BAND_COMBO)
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture
def l8_sr(amazonas):
    """Return a landsat based collection.

    the 100 first images of the landast 8 SR ImageCollection centered on the amazonas state of colombia and from 2021-01-01 to 2021-12-01.
    """
    return (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(amazonas)
        .filterDate("2021-01-01", "2021-12-01")
    )


@pytest.fixture
def l8_sr_raw():
    """Return a defined image collection."""
    return ee.ImageCollection("LANDSAT/LC08/C02/T1").select(L8_BAND_COMBO)


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


@pytest.fixture
def multipoint_feature():
    """Return a ``Feature`` instance."""
    geoms = ee.Geometry.MultiPoint([[0, 0], [0, 1]])
    return ee.Feature(geoms).set({"foo": "bar", "bar": "foo"})


@pytest.fixture
def ecoregions():
    """Return the ecoregion collection."""
    return ee.FeatureCollection("projects/google/charts_feature_example")


@pytest.fixture
def climSamp():
    """Return the climate sample collection."""
    normClim = ee.ImageCollection("OREGONSTATE/PRISM/Norm81m").toBands()
    region = ee.Geometry.Rectangle(-123.41, 40.43, -116.38, 45.14)
    return normClim.sample(region, 5000)


@pytest.fixture(scope="session")
def stac_schema():
    """Return the STAC collection schema."""
    url = "https://raw.githubusercontent.com/radiantearth/stac-spec/v1.0.0/collection-spec/json-schema/collection.json"
    return requests.get(url).json()


@pytest.fixture(scope="session")
def jaxa_rainfall():
    """Return the JAXA rain collection."""
    return ee.ImageCollection("JAXA/GPM_L3/GSMaP/v6/operational")
