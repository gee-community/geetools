"""Test the ``Image`` class."""
import io
import zipfile
from io import BytesIO
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

import ee
import numpy as np
import pytest
from jsonschema import validate
from matplotlib import pyplot as plt

import geetools


class TestAddDate:
    """Test the ``addDate`` method."""

    def test_add_date(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.addDate()
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})

    def test_add_date_format(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.addDate("yyyyMMdd")
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})


class TestAddSuffix:
    """Test the ``addSuffix`` method."""

    def test_add_suffix_to_all(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addSuffix("_suffix")
        data_regression.check(image.bandNames().getInfo())

    def test_add_suffix_to_selected(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addSuffix("_suffix", bands=["B1", "B2"])
        data_regression.check(image.bandNames().getInfo())


class TestAddPrefix:
    """Test the ``addPrefix`` method."""

    def test_add_prefix_to_all(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addPrefix("prefix_")
        data_regression.check(image.bandNames().getInfo())

    def test_add_prefix_to_selected(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addPrefix("prefix_", bands=["B1", "B2"])
        data_regression.check(image.bandNames().getInfo())


class TestGetValues:
    """Test the ``getValues`` method."""

    def test_get_values(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        values = s2_sr_vatican_2020.geetools.getValues(vatican_buffer.centroid())
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})

    def test_get_values_with_scale(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        values = s2_sr_vatican_2020.geetools.getValues(vatican_buffer.centroid(), scale=100)
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})


class TestMinScale:
    """Test the ``minScale`` method."""

    def test_min_scale(self, s2_sr_vatican_2020):
        scale = s2_sr_vatican_2020.geetools.minScale()
        assert scale.getInfo() == 10


class TestMerge:
    """Test the ``merge`` method."""

    def test_merge(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.merge([s2_sr_vatican_2020, s2_sr_vatican_2020])
        data_regression.check(image.bandNames().getInfo())


class TestRename:
    """Test the ``rename`` method."""

    def test_rename(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.rename({"B1": "newB1", "B2": "newB2"})
        data_regression.check(image.bandNames().getInfo())


class TestRemove:
    """Test the ``remove`` method."""

    def test_remove(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.remove(["B1", "B2"])
        data_regression.check(image.bandNames().getInfo())


class TestToGrid:
    """Test the ``toGrid`` method."""

    def test_to_grid(self, s2_sr_vatican_2020, vatican_buffer, ndarrays_regression):
        grid = s2_sr_vatican_2020.geetools.toGrid(1, "B2", vatican_buffer)
        grid = [f["geometry"]["coordinates"] for f in grid.getInfo()["features"]]
        grid = {f"geometry_{i}": np.array(c) for i, c in enumerate(grid)}
        ndarrays_regression.check(grid)


class TestClipOnCollection:
    """Test the ``clipOnCollection`` method."""

    def test_clip_on_collection(self, s2_sr_vatican_2020, fc_instance, data_regression):
        clipped = s2_sr_vatican_2020.geetools.clipOnCollection(fc_instance)
        name = "test_clip_on_collection"
        data_regression.check(clipped.first().bandNames().getInfo(), f"{name}_bands")
        data_regression.check(clipped.first().propertyNames().getInfo(), f"{name}_property")

    def test_clip_on_collection_without_properties(
        self, s2_sr_vatican_2020, fc_instance, data_regression
    ):
        clipped = s2_sr_vatican_2020.geetools.clipOnCollection(fc_instance, 0)
        name = "test_clip_on_collection_without_properties"
        data_regression.check(clipped.first().bandNames().getInfo(), f"{name}_bands")
        data_regression.check(clipped.first().propertyNames().getInfo(), f"{name}_property")

    @pytest.fixture
    def fc_instance(self):
        """Return 2 little buffers in vaticanc city as a featurecollection."""
        return ee.FeatureCollection(
            [
                ee.Feature(ee.Geometry.Point([12.4534, 41.9029]).buffer(50), {"Id": 1}),
                ee.Feature(ee.Geometry.Point([12.4534, 41.9029]).buffer(100), {"Id": 2}),
            ]
        )


class TestBufferMask:
    """Test the ``bufferMask`` method."""

    @pytest.mark.xfail
    def test_buffer_mask(self):
        """I don't know what to test here."""
        assert False


class TestFull:
    """Test the ``full`` method."""

    def test_full(self, vatican_buffer, num_regression):
        image = ee.Image.geetools.full()
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_full_with_value(self, vatican_buffer, num_regression):
        image = ee.Image.geetools.full([1])
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_full_with_name(self, vatican_buffer, num_regression):
        image = ee.Image.geetools.full([1], ["toto"])
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_full_with_lists(self, vatican_buffer, num_regression):
        image = ee.Image.geetools.full([1, 2, 3], ["toto", "titi", "tata"])
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


class TestFullLike:
    """Test the ``fullLike`` method."""

    def test_full_like(self, vatican_buffer, s2_sr_vatican_2020, num_regression):
        image = s2_sr_vatican_2020.set({"props": "toto"})
        image = image.geetools.fullLike(0)
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        assert "props" not in image.propertyNames().getInfo()
        num_regression.check(values.getInfo())

    def test_full_like_with_properties(self, s2_sr_vatican_2020):
        image = s2_sr_vatican_2020.set({"props": "toto"})
        image = image.geetools.fullLike(0, copyProperties=1)
        assert "props" in image.propertyNames().getInfo()

    def test_full_like_with_mask(self, s2_sr_vatican_2020, num_regression):
        image = s2_sr_vatican_2020.geetools.fullLike(0, keepMask=1)
        values = image.geetools.getValues(ee.Geometry.Point(0, 0))
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})


class TestReduceBands:
    """Test the ``reduceBands`` method."""

    def test_reduce_bands(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.reduceBands("sum")
        values = image.select("sum").reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_reduce_bands_with_bands(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.reduceBands("sum", ["B1", "B2"])
        values = image.select("sum").reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_reduce_bands_with_name(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.reduceBands("sum", name="toto")
        values = image.select("toto").reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


class TestNegativeClip:
    """Test the ``negativeClip`` method."""

    def test_negative_clip(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.negativeClip(vatican_buffer)
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})


class testFormat:
    """Test the ``toString`` method."""

    def test_to_string(self, s2_sr_vatican_2020):
        string = s2_sr_vatican_2020.geetools.toString("date: {system_date}")
        assert string.getInfo() == "date: 2020-01-01"


class TestPrefixSuffix:
    """Test the ``prefix`` and ``suffix`` methods."""

    def test_prefix(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addPrefix("prefix_")
        data_regression.check(image.bandNames().getInfo())

    def test_suffix(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addSuffix("_suffix")
        data_regression.check(image.bandNames().getInfo())


class TestGauss:
    """Test the ``gauss`` method."""

    def test_gauss(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.gauss()
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_gauss_with_band(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.gauss("B2")
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


class TestDoyToDate:
    """Test the ``doyToDate`` method."""

    def test_doy_to_date(self, doy_image, vatican_buffer, num_regression):
        image = doy_image.geetools.doyToDate(2023)
        values = image.reduceRegion(ee.Reducer.min(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_doy_to_date_with_format(self, doy_image, vatican_buffer, num_regression):
        image = doy_image.geetools.doyToDate(2023, dateFormat="yyyy.DDD")
        values = image.reduceRegion(ee.Reducer.min(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_doy_to_date_with_band(self, doy_image, vatican_buffer, num_regression):
        image = doy_image.geetools.doyToDate(2023, band="doy2")
        values = image.reduceRegion(ee.Reducer.min(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


class TestRepeat:
    """Test the ``repeat`` method."""

    def test_repeat(self, image_instance):
        image = image_instance.geetools.repeat("B1", 2)
        assert image.bandNames().getInfo() == ["B1", "B2", "B3", "B1_1", "B1_2"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestmatchHistogram:
    """Test the ``histogramMatch`` method."""

    def test_histogram_match(self, image_source, image_target, vatican_buffer, num_regression):
        bands = {"R": "R", "G": "G", "B": "B"}
        image = image_source.geetools.matchHistogram(image_target, bands)
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    @pytest.fixture
    def dates(self):
        """The dates of my imagery."""
        return "2023-06-01", "2023-06-30"

    @pytest.fixture
    def image_source(self, vatican_buffer, dates):
        """image from the S2 copernicus program over vatican city."""
        return (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(vatican_buffer)
            .filterDate(*dates)
            .first()
            .select("B4", "B3", "B2")
            .rename("R", "G", "B")
        )

    @pytest.fixture
    def image_target(self, vatican_buffer, dates):
        """image from the L8 Landsat program over vatican city."""
        return (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(vatican_buffer)
            .filterDate(*dates)
            .first()
            .select("SR_B4", "SR_B3", "SR_B2")
            .rename("R", "G", "B")
        )


class TestRemoveZeros:
    """Test the ``removeZeros`` method."""

    def test_remove_zeros(self, image_instance, vatican_buffer):
        image = image_instance.geetools.removeZeros()
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        assert values.getInfo() == {"array": [1, 2]}

    @pytest.fixture
    def image_instance(self):
        """A random image instance with array data containing zeros."""
        return ee.Image([0, 1, 2]).toArray()


class TestInterpolateBands:
    """Test the ``interpolateBands`` method."""

    def test_interpolate_bands(self, image_instance, vatican_buffer, num_regression):
        image = image_instance.geetools.interpolateBands([0, 3000], [0, 30])
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    @pytest.fixture
    def image_instance(self, vatican_buffer):
        """A sentinel 2 single image centered on the vatican."""
        src = "COPERNICUS/S2_SR_HARMONIZED"
        return ee.ImageCollection(src).filterBounds(vatican_buffer).first().select(["B4", "B2"])


class TestIsletMask:
    """Test the ``isletMask`` method."""

    def test_islet_mask(self, image_instance, tmp_path, image_regression):
        image = image_instance.geetools.isletMask(20)
        file = self.get_image(image, tmp_path / "test.tif")
        image_regression.check(file.read_bytes())

    def get_image(self, image, dst):

        link = image.getDownloadURL(
            {
                "name": "test",
                "region": ee.Geometry.Point([12.4534, 41.9033]).buffer(1000),
                "filePerBand": False,
                "scale": 10,
            }
        )

        with TemporaryDirectory() as dir:
            tmp = Path(dir) / "tmp.zip"
            urlretrieve(link, tmp)
            with zipfile.ZipFile(tmp, "r") as zip_:
                dst.write_bytes(zip_.read(zip_.namelist()[0]))

        return dst

    @pytest.fixture
    def image_instance(self):
        """An image on top of the buffer."""
        buffer = ee.Geometry.Point([12.4534, 41.9033]).buffer(1000)
        return (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(buffer)
            .filterDate("2023-01-01", "2023-01-31")
            .first()
            .select("B4", "B3", "B2")
        )


class TestIndicexList:
    """Test the ``index_list`` method."""

    def test_indices(self):
        indices = ee.Image.geetools.index_list()
        assert "NDVI" in indices.keys()
        assert len(indices) == 247


class TestSpectralIndices:
    """Test the ``spectralIndices`` method."""

    def test_default_spectral_indices(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.spectralIndices("all")
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})


class TestMaskClouds:
    """Test the ``maskClouds`` method."""

    def test_mask_S2_clouds(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.maskClouds()
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        values = {k: np.nan if v is None else v for k, v in values.getInfo().items()}
        num_regression.check(values)


class TestGetscaleParams:
    """Test the ``getScaleParams`` method."""

    def test_get_scale_params(self, s2_sr_vatican_2020, data_regression):
        params = s2_sr_vatican_2020.geetools.getScaleParams()
        data_regression.check(params)


class TestGetOffsetParams:
    """Test the ``getOffsetParams`` method."""

    def get_offset_params(self, s2_sr_vatican_2020, data_regression):
        params = s2_sr_vatican_2020.geetools.getOffsetParams()
        data_regression.check(params)


class TestScaleAndOffset:
    """Test the ``scaleAndOffset`` method."""

    def test_scale_and_offset(self, vatican_buffer, s2_sr_vatican_2020, num_regression):
        image = s2_sr_vatican_2020.geetools.scaleAndOffset()
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


class TestPreprocess:
    """Test the ``preprocess`` method."""

    def test_preprocess(self, vatican_buffer, s2_sr_vatican_2020, num_regression):
        image = s2_sr_vatican_2020.geetools.preprocess()
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


class TestGetSTAC:
    """Test the ``getSTAC`` method."""

    def test_get_stac_schema(self, s2_sr_vatican_2020, stac_schema):
        stac = s2_sr_vatican_2020.geetools.getSTAC()
        validate(stac, stac_schema)

    def test_get_stac(self, s2_sr_vatican_2020):
        stac = s2_sr_vatican_2020.geetools.getSTAC()
        assert stac["id"] == "COPERNICUS/S2_SR_HARMONIZED"


class TestGetDOI:
    """Test the ``getDOI`` method."""

    def get_doi(self, s2_sr_vatican_2020, data_regression):
        doi = s2_sr_vatican_2020.geetools.getDOI()
        data_regression.check(doi)


class TestGetCitation:
    """Test the ``getCitation`` method."""

    def get_citation(self, s2_sr_vatican_2020, data_regression):
        citation = s2_sr_vatican_2020.first().geetools.getCitation()
        data_regression.check(citation)


class TestPanSharpen:
    """Test the panSharpen method."""

    @pytest.mark.xfail(
        reason="This test is failing because the panSharpen method is not implemented for this platform."
    )
    def test_pan_sharpen(self, l8_sr_vatican_2020, num_regression):
        sharp = l8_sr_vatican_2020.geetools.panSharpen(
            method="HPFA", qa=["MSE", "RMSE"], maxPixels=1e13
        )
        centroid = sharp.geometry().centroid().buffer(100)
        values = sharp.reduceRegion(ee.Reducer.mean(), centroid, 1)
        num_regression.check(values.getInfo())


class TestTasseledCap:
    """Test the tasseledCap method."""

    @pytest.mark.xfail(
        reason="This test is failing because the tasseledCap method is not implemented for this platform."
    )
    def test_tasseled_cap(self, l8_sr_vatican_2020, num_regression):
        img = l8_sr_vatican_2020.geetools.tasseledCap()
        centroid = img.geometry().centroid().buffer(100)
        values = img.reduceRegion(ee.Reducer.mean(), centroid, 1)
        num_regression.check(values.getInfo())


class TestRemoveProperties:
    """Test the removeProperties method."""

    def test_remove_properties(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.removeProperties(["system:time_start"])
        data_regression.check(image.propertyNames().getInfo())


class TestDistanceToMask:
    """Test the distanceToMask method."""

    def test_distance_to_mask(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        centerBuffer = vatican_buffer.centroid().buffer(100)
        BufferMask = ee.Image.constant(1).clip(centerBuffer)
        mask = ee.Image.constant(0).where(BufferMask, 1)
        distance = s2_sr_vatican_2020.geetools.distanceToMask(mask)
        values = distance.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_deprecated_distance_to_mask(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        centerBuffer = vatican_buffer.centroid().buffer(100)
        BufferMask = ee.Image.constant(1).clip(centerBuffer)
        mask = ee.Image.constant(0).where(BufferMask, 1)
        with pytest.deprecated_call():
            distance = geetools.algorithms.distanceToMask(s2_sr_vatican_2020, mask)
            values = distance.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())


class TestDistance:
    """Test the ``distance`` method."""

    def test_distance(self, vatican_buffer, num_regression):
        # 2 images from june in vatican
        distance = self.image.geetools.distance(self.other)
        values = distance.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_deprecated_euclidian_distance(self, vatican_buffer, num_regression):
        # 2 images from june in vatican
        with pytest.deprecated_call():
            distance = geetools.algorithms.euclideanDistance(self.image, self.other)
            values = distance.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    @property
    def image(self):
        """Return an image from june in vatican."""
        image_id = "COPERNICUS/S2_SR_HARMONIZED/20210604T100029_20210604T100027_T32TQM"
        return ee.Image(image_id).select(["B4", "B3", "B2"])

    @property
    def other(self):
        """Return another image from june in vatican."""
        other_id = "COPERNICUS/S2_SR_HARMONIZED/20210604T100029_20210604T100027_T33TTG"
        return ee.Image(other_id).select(["B4", "B3", "B2"])


class TestMaskCover:
    """Test the ``maskCoverRegion`` method."""

    def test_mask_cover_region(self):
        aoi = ee.Geometry.Point([12.210900891755129, 41.928551351175386]).buffer(2200)
        ratio = self.image.geetools.maskCoverRegion(aoi, scale=10)
        assert isclose(ratio.getInfo(), 9.99, abs_tol=0.01)

    def test_mask_cover_region_zero(self):
        aoi = ee.Geometry.Point([11.880190936531116, 42.0159494554553]).buffer(1000)
        ratio = self.image.geetools.maskCoverRegion(aoi, scale=10)
        assert isclose(ratio.getInfo(), 0)

    def test_mask_cover_regions(self):
        geom = ee.Geometry.Point([12.210900891755129, 41.928551351175386]).buffer(2200)
        aoi = ee.FeatureCollection([ee.Feature(geom, {"test_property": 1})])
        result = self.image.geetools.maskCoverRegions(aoi, scale=10)
        feat = ee.Feature(result.first())
        ratio = feat.getInfo()["properties"]["mask_cover"]
        # ratio = ee.Number(feat.get('mask_cover'))
        # the last line should work, but it doesn't, I don't know why
        assert isclose(ratio, 9.99, abs_tol=0.01)

    def test_mask_cover_regions_zero(self):
        geom = ee.Geometry.Point([11.880190936531116, 42.0159494554553]).buffer(1000)
        aoi = ee.FeatureCollection([ee.Feature(geom, {"test_property": 1})])
        result = self.image.geetools.maskCoverRegions(aoi, scale=10)
        feat = ee.Feature(result.first())
        ratio = feat.getInfo()["properties"]["mask_cover"]
        # ratio = ee.Number(feat.get('mask_cover'))
        # the last line should work, but it doesn't, I don't know why
        assert isclose(ratio, 0)

    def test_deprecated_mask_cover(self):
        with pytest.deprecated_call():
            image = geetools.algorithms.maskCover(self.image)
            assert isclose(image.get("mask_cover").getInfo(), 18.04, rel_tol=0.01)

    @property
    def image(self):
        image_id = "COPERNICUS/S2_SR_HARMONIZED/20180401T100019_20180401T100022_T32TQM"
        image = ee.Image(image_id)
        qa = image.select("QA60")
        cloudBitMask, cirrusBitMask = 1 << 10, 1 << 11
        mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
        image = image.updateMask(mask)
        return image.select(["B4", "B3", "B2"])


class TestPlot:
    """Test the ``plot`` method."""

    def test_plot(self, s2_sr_vatican_2020, vatican, image_regression):
        fig, ax = plt.subplots()
        s2_sr_vatican_2020.geetools.plot(["B4", "B3", "B2"], vatican.geometry(), ax)

        with BytesIO() as image_byte:
            fig.savefig(image_byte, format="png")
            image_byte.seek(0)
            image_regression.check(image_byte.getvalue())

    def test_plot_one_band(self, s2_sr_vatican_2020, vatican, image_regression):
        fig, ax = plt.subplots()
        ndvi = s2_sr_vatican_2020.geetools.spectralIndices("NDVI")
        ndvi.geetools.plot(["NDVI"], vatican.geometry(), ax)

        with BytesIO() as image_byte:
            fig.savefig(image_byte, format="png")
            image_byte.seek(0)
            image_regression.check(image_byte.getvalue())

    def test_plot_one_band_cmap(self, s2_sr_vatican_2020, vatican, image_regression):
        fig, ax = plt.subplots()
        ndvi = s2_sr_vatican_2020.geetools.spectralIndices("NDVI")
        ndvi.geetools.plot(["NDVI"], vatican.geometry(), ax, cmap="RdYlGn")

        with BytesIO() as image_byte:
            fig.savefig(image_byte, format="png")
            image_byte.seek(0)
            image_regression.check(image_byte.getvalue())

    def test_plot_with_fc(self, s2_sr_vatican_2020, vatican, image_regression):
        fig, ax = plt.subplots()
        s2_sr_vatican_2020.geetools.plot(["B4", "B3", "B2"], vatican.geometry(), ax, fc=vatican)

        with BytesIO() as image_byte:
            fig.savefig(image_byte, format="png")
            image_byte.seek(0)
            image_regression.check(image_byte.getvalue())

    def test_plot_with_crs(self, s2_sr_vatican_2020, vatican, image_regression):
        fig, ax = plt.subplots()
        ndvi = s2_sr_vatican_2020.geetools.spectralIndices("NDVI")
        ndvi.geetools.plot(["NDVI"], vatican.geometry(), ax, crs="EPSG:3857", scale=10)

        with BytesIO() as image_byte:
            fig.savefig(image_byte, format="png")
            image_byte.seek(0)
            image_regression.check(image_byte.getvalue())


class TestFromList:
    """Test ``fromList`` method."""

    def test_from_list_unique(self):
        """Test using a list of unique band names."""
        sequence = ee.List([1, 2, 3])
        images = sequence.map(lambda i: ee.Image(ee.Number(i)).rename(ee.Number(i).int().format()))
        image = ee.Image.geetools.fromList(images)
        assert image.bandNames().getInfo() == ["1", "2", "3"]

    def test_from_list_multiband(self):
        """Test using a list of multiband images."""
        images = ee.List(
            [
                ee.Image([1, 2, 3]).rename(["1", "2", "3"]),
                ee.Image([4, 5]).rename(["4", "5"]),
            ]
        )
        image = ee.Image.geetools.fromList(images)
        assert image.bandNames().getInfo() == ["1", "2", "3", "4", "5"]


class TestPlotByRegions:
    """Test the ``plot_by_regions`` method."""

    def test_plot_by_regions_bar(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        self.image.geetools.plot_by_regions(
            type = "bar",
            regions = self.ecoregions,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ["01_tmean", "02_tmean", "03_tmean", "04_tmean", "05_tmean", "06_tmean", "07_tmean", "08_tmean", "09_tmean", "10_tmean", "11_tmean", "12_tmean"],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ['#604791', '#1d6b99', '#39a8a7', '#0f8755', '#76b349', '#f0af07', '#e37d05', '#cf513e', '#96356f', '#724173', '#9c4f97', '#696969'],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_regions_barh(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        self.image.geetools.plot_by_regions(
            type = "barh",
            regions = self.ecoregions,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ["01_tmean", "02_tmean", "03_tmean", "04_tmean", "05_tmean", "06_tmean", "07_tmean", "08_tmean", "09_tmean", "10_tmean", "11_tmean", "12_tmean"],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ['#604791', '#1d6b99', '#39a8a7', '#0f8755', '#76b349', '#f0af07', '#e37d05', '#cf513e', '#96356f', '#724173', '#9c4f97', '#696969'],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_regions_stacked(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        self.image.geetools.plot_by_regions(
            type = "stacked",
            regions = self.ecoregions,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ["01_tmean", "02_tmean", "03_tmean", "04_tmean", "05_tmean", "06_tmean", "07_tmean", "08_tmean", "09_tmean", "10_tmean", "11_tmean", "12_tmean"],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ['#604791', '#1d6b99', '#39a8a7', '#0f8755', '#76b349', '#f0af07', '#e37d05', '#cf513e', '#96356f', '#724173', '#9c4f97', '#696969'],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def ecoregions(self):
        return ee.FeatureCollection("projects/google/charts_feature_example").select(
            ["label", "value", "warm"]
        )

    @property
    def image(self):
        return ee.ImageCollection("OREGONSTATE/PRISM/Norm91m").toBands()


class TestPlotByBands:
    """Test the ``plot_by_bands`` method."""

    def test_plot_by_bands_bar(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        self.image.geetools.plot_by_bands(
            type = "bar",
            regions = self.ecoregions,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ['01_ppt', '02_ppt', '03_ppt', '04_ppt', '05_ppt', '06_ppt', '07_ppt', '08_ppt', '09_ppt', '10_ppt', '11_ppt', '12_ppt'],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ["#f0af07", "#0f8755", "#76b349"],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_bands_plot(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        self.image.geetools.plot_by_bands(
            type = "plot",
            regions = self.ecoregions,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ['01_ppt', '02_ppt', '03_ppt', '04_ppt', '05_ppt', '06_ppt', '07_ppt', '08_ppt', '09_ppt', '10_ppt', '11_ppt', '12_ppt'],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ["#f0af07", "#0f8755", "#76b349"],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_bands_area(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        self.image.geetools.plot_by_bands(
            type = "fill_between",
            regions = self.ecoregions,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ['01_ppt', '02_ppt', '03_ppt', '04_ppt', '05_ppt', '06_ppt', '07_ppt', '08_ppt', '09_ppt', '10_ppt', '11_ppt', '12_ppt'],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ["#f0af07", "#0f8755", "#76b349"],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_bands_pie(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregion = self.ecoregions.filter(ee.Filter.eq("label", "Forest"))
        self.image.geetools.plot_by_bands(
            type = "pie",
            regions = ecoregion,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ['01_ppt', '02_ppt', '03_ppt', '04_ppt', '05_ppt', '06_ppt', '07_ppt', '08_ppt', '09_ppt', '10_ppt', '11_ppt', '12_ppt'],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ['#604791', '#1d6b99', '#39a8a7', '#0f8755', '#76b349', '#f0af07', '#e37d05', '#cf513e', '#96356f', '#724173', '#9c4f97', '#696969'],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_bands_donut(self, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregion = self.ecoregions.filter(ee.Filter.eq("label", "Forest"))
        self.image.geetools.plot_by_bands(
            type = "donut",
            regions = ecoregion,
            reducer = "mean",
            scale = 500,
            regionId = "label",
            bands = ['01_ppt', '02_ppt', '03_ppt', '04_ppt', '05_ppt', '06_ppt', '07_ppt', '08_ppt', '09_ppt', '10_ppt', '11_ppt', '12_ppt'],
            labels = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors = ['#604791', '#1d6b99', '#39a8a7', '#0f8755', '#76b349', '#f0af07', '#e37d05', '#cf513e', '#96356f', '#724173', '#9c4f97', '#696969'],
            ax = ax
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def ecoregions(self):
        return ee.FeatureCollection("projects/google/charts_feature_example").select(
            ["label", "value", "warm"]
        )

    @property
    def image(self):
        return ee.ImageCollection("OREGONSTATE/PRISM/Norm91m").toBands()


class TestPlotHist:
    """Test the ``plot_hist`` method."""

    def test_plot_hist(self, image_regression):
        fig, ax = plt.subplots()
        self.image.geetools.plot_hist(
            bands=["sur_refl_b01", "sur_refl_b02", "sur_refl_b06"],
            labels=[["Red", "NIR", "SWIR"]],
            colors=["#cf513e", "#1d6b99", "#f0af07"],
            ax=ax,
            bins=100,
            scale=500,
            region=self.region,
        )
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue(), diff_threshold=0.2)

    @property
    def image(self):
        return (
            ee.ImageCollection("MODIS/061/MOD09A1")
            .filter(ee.Filter.date("2018-06-01", "2018-09-01"))
            .select(["sur_refl_b01", "sur_refl_b02", "sur_refl_b06"])
            .mean()
        )

    @property
    def region(self):
        return ee.Geometry.Rectangle([-112.60, 40.60, -111.18, 41.22])
