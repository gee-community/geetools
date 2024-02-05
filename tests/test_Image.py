"""Test the ``Image`` class."""
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

import ee
import numpy as np
import pytest

import geetools


class TestAddDate:
    """Test the ``addDate`` method."""

    def test_add_date(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.addDate()
        values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
        num_regression.check(values.getInfo())

    def test_deprecated_make_date_band(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.date.makeDateBand(s2_sr_vatican_2020)
            values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
            num_regression.check(values.getInfo())


class TestAddSuffix:
    """Test the ``addSuffix`` method."""

    def test_add_suffix_to_all(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addSuffix("_suffix")
        data_regression.check(image.bandNames().getInfo())

    def test_add_suffix_to_selected(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addSuffix("_suffix", bands=["B1", "B2"])
        data_regression.check(image.bandNames().getInfo())

    def test_deprecated_add_suffix(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.addSuffix(s2_sr_vatican_2020, "_suffix", ["B1", "B2"])
            data_regression.check(image.bandNames().getInfo())


class TestAddPrefix:
    """Test the ``addPrefix`` method."""

    def test_add_prefix_to_all(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addPrefix("prefix_")
        data_regression.check(image.bandNames().getInfo())

    def test_add_prefix_to_selected(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addPrefix("prefix_", bands=["B1", "B2"])
        data_regression.check(image.bandNames().getInfo())

    def test_deprecated_add_prefix(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.addPrefix(s2_sr_vatican_2020, "prefix_", ["B1", "B2"])
            data_regression.check(image.bandNames().getInfo())


class TestGetValues:
    """Test the ``getValues`` method."""

    def test_get_values(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        values = s2_sr_vatican_2020.geetools.getValues(vatican_buffer.centroid())
        num_regression.check(values.getInfo())

    def test_get_values_with_scale(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        values = s2_sr_vatican_2020.geetools.getValues(vatican_buffer.centroid(), scale=100)
        num_regression.check(values.getInfo())

    def test_deprecated_get_value(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            values = geetools.tools.image.getValue(s2_sr_vatican_2020, vatican_buffer.centroid())
            num_regression.check(values.getInfo())


class TestMinScale:
    """Test the ``minScale`` method."""

    def test_min_scale(self, s2_sr_vatican_2020):
        scale = s2_sr_vatican_2020.geetools.minScale()
        assert scale.getInfo() == 10

    def test_deprecated_minscale(self, s2_sr_vatican_2020):
        with pytest.deprecated_call():
            scale = geetools.tools.image.minscale(s2_sr_vatican_2020)
            assert scale.getInfo() == 10


class TestMerge:
    """Test the ``merge`` method."""

    def test_merge(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.merge([s2_sr_vatican_2020, s2_sr_vatican_2020])
        data_regression.check(image.bandNames().getInfo())

    def test_deprecated_add_multi_band(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.addMultiBands([s2_sr_vatican_2020, s2_sr_vatican_2020])
            data_regression.check(image.bandNames().getInfo())

    def test_deprecated_mix_bands(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.mixBands([s2_sr_vatican_2020, s2_sr_vatican_2020])
            data_regression.check(image.bandNames().getInfo())


class TestRename:
    """Test the ``rename`` method."""

    def test_rename(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.rename({"B1": "newB1", "B2": "newB2"})
        data_regression.check(image.bandNames().getInfo())

    def test_deprecated_rename_dict(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            replace = {"B1": "newB1", "B2": "newB2"}
            image = geetools.tools.image.renameDict(s2_sr_vatican_2020, replace)
            data_regression.check(image.bandNames().getInfo())


class TestRemove:
    """Test the ``remove`` method."""

    def test_remove(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.remove(["B1", "B2"])
        data_regression.check(image.bandNames().getInfo())

    def test_deprecated_remove_bands(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.removeBands(s2_sr_vatican_2020, ["B1", "B2"])
            data_regression.check(image.bandNames().getInfo())


class TestToGrid:
    """Test the ``toGrid`` method."""

    def test_to_grid(self, s2_sr_vatican_2020, vatican_buffer, ndarrays_regression):
        grid = s2_sr_vatican_2020.geetools.toGrid(1, "B2", vatican_buffer)
        grid = [f["geometry"]["coordinates"] for f in grid.getInfo()["features"]]
        grid = {f"geometry_{i}": np.array(c) for i, c in enumerate(grid)}
        ndarrays_regression.check(grid)

    def test_deprecated_to_grid(self, s2_sr_vatican_2020, vatican_buffer, ndarrays_regression):
        with pytest.deprecated_call():
            grid = geetools.tools.image.toGrid(s2_sr_vatican_2020, 1, "B2", vatican_buffer)
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

    def test_deprecated_clip_to_collection(self, s2_sr_vatican_2020, fc_instance, data_regression):
        with pytest.deprecated_call():
            clipped = geetools.tools.image.clipToCollection(s2_sr_vatican_2020, fc_instance)
            name = "test_deprecated_clip_to_collection"
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

    def test_deprecated_empty(self, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.empty()
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

    def test_deprecated_empty_copy(self, vatican_buffer, s2_sr_vatican_2020, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.emptyCopy(s2_sr_vatican_2020)
            values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
            num_regression.check(values.getInfo())


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

    def test_deprecated_sum_bands(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.sumBands(s2_sr_vatican_2020, "sum", ["B1", "B2"])
            values = image.select("sum").reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
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

    def test_deprecated_make_name(self, s2_sr_vatican_2020):
        with pytest.deprecated_call():
            string = geetools.tools.image.makeName(s2_sr_vatican_2020, "date: {system_date}")
            assert string.getInfo() == "date: 2020-01-01"

    def test_deprecated_utils_make_name(self, s2_sr_vatican_2020):
        with pytest.deprecated_call():
            string = geetools.tools.utils.makeName(s2_sr_vatican_2020, "date: {system_date}")
            assert string.getInfo() == "date: 2020-01-01"


class TestPrefixSuffix:
    """Test the ``prefix`` and ``suffix`` methods."""

    def test_prefix(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addPrefix("prefix_")
        data_regression.check(image.bandNames().getInfo())

    def test_suffix(self, s2_sr_vatican_2020, data_regression):
        image = s2_sr_vatican_2020.geetools.addSuffix("_suffix")
        data_regression.check(image.bandNames().getInfo())

    def test_deprecated_rename_pattern(self, s2_sr_vatican_2020, data_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.renamePattern(s2_sr_vatican_2020, "prefix_{band}_suffix")
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

    def test_deprecated_gauss_function(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.gaussFunction(s2_sr_vatican_2020, "B2")
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

    def test_deprecated_doy_to_date(self, doy_image, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.doyToDate(doy_image, year=2023)
            values = image.reduceRegion(ee.Reducer.min(), vatican_buffer, 10)
            num_regression.check(values.getInfo())


class TestRepeat:
    """Test the ``repeat`` method."""

    def test_repeat(self, image_instance):
        image = image_instance.geetools.repeat("B1", 2)
        assert image.bandNames().getInfo() == ["B1", "B2", "B3", "B1_1", "B1_2"]

    def test_deprecated_repeat_band(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.repeatBand(image_instance, 2, ["B1", "B2"])
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

    def test_deprecated_array_non_zeros(self, image_instance, vatican_buffer):
        with pytest.deprecated_call():
            image = geetools.tools.image.arrayNonZeros(image_instance)
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

    def test_deprecated_parametrize(self, image_instance, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.tools.image.parametrize(image_instance, [0, 3000], [0, 30])
            values = image.reduceRegion(ee.Reducer.first(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    def test_deprecated_linear_function(self, image_instance, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            band = image_instance.bandNames().get(0)
            image = geetools.tools.image.linearFunction(
                image_instance, band, 0, 3000, output_min=0, output_max=30
            )
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

    def test_deprecated_mask_island(self, image_instance, tmp_path, image_regression):
        with pytest.deprecated_call():
            image = geetools.utils.maskIslands(image_instance, 20)
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
        assert len(indices) == 228


class TestSpectralIndices:
    """Test the ``spectralIndices`` method."""

    def test_default_spectral_indices(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.spectralIndices("all")
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check({k: np.nan if v is None else v for k, v in values.getInfo().items()})

    def test_deprecated_compute(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.indices.compute(s2_sr_vatican_2020, "NDVI", None)
            values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    def test_deprecated_ndvi(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.indices.ndvi(s2_sr_vatican_2020, None, None)
            values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    def test_deprecated_evi(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.indices.evi(s2_sr_vatican_2020, None, None, None)
            values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    def test_deprecated_nbr2(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.indices.nbr2(s2_sr_vatican_2020, None, None)
            values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    def test_deprecated_nbr(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.indices.nbr(s2_sr_vatican_2020, None, None)
            values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())

    def test_deprecated_ndfi(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        with pytest.deprecated_call():
            image = geetools.indices.ndfi(s2_sr_vatican_2020, None, None, None, None, None, None)
            values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
            num_regression.check(values.getInfo())


class TestMaskClouds:
    """Test the ``maskClouds`` method."""

    def test_mask_S2_clouds(self, s2_sr_vatican_2020, vatican_buffer, num_regression):
        image = s2_sr_vatican_2020.geetools.maskClouds()
        values = image.reduceRegion(ee.Reducer.mean(), vatican_buffer, 10)
        num_regression.check(values.getInfo())


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

    def test_get_stac(self, s2_sr_vatican_2020, data_regression):
        stac = s2_sr_vatican_2020.geetools.getSTAC()
        stac["extent"].pop("temporal")  # it will change all the time
        data_regression.check(stac)


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

    def test_pan_sharpen(self, num_regression):
        source = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_047027_20160819")
        sharp = source.geetools.panSharpen(method="HPFA", qa=["MSE", "RMSE"], maxPixels=1e13)
        centroid = sharp.geometry().centroid().buffer(100)
        values = sharp.reduceRegion(ee.Reducer.mean(), centroid, 1)
        num_regression.check(values.getInfo())


class TestTasseledCap:
    """Test the tasseledCap method."""

    def test_tasseled_cap(self, num_regression):
        img = ee.Image("LANDSAT/LT05/C01/T1/LT05_044034_20081011")
        img = img.geetools.tasseledCap()
        centroid = img.geometry().centroid().buffer(100)
        values = img.reduceRegion(ee.Reducer.mean(), centroid, 1)
        num_regression.check(values.getInfo())

    def test_deprecated_tasseled_cap(self, num_regression):
        img = ee.Image("LANDSAT/LT05/C01/T1/LT05_044034_20081011")
        with pytest.deprecated_call():
            geetools.indices.tasseled_cap_s2(img)
            centroid = img.geometry().centroid().buffer(100)
            values = img.reduceRegion(ee.Reducer.mean(), centroid, 1)
            num_regression.check(values.getInfo())
