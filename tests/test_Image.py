"""Test the ``Image`` class."""
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

import ee
import pytest

import geetools


class TestAddDate:
    """Test the ``addDate`` method."""

    def test_add_date(self, image_instance, vatican):
        image = image_instance.geetools.addDate()
        dateBand = image.select("date")
        date = dateBand.reduceRegion(ee.Reducer.first(), vatican, 10).get("date")
        assert image.bandNames().size().getInfo() > 1
        assert ee.Date(date).format("YYYY-MM-DD").getInfo() == "2020-01-01"

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.date.makeDateBand(image_instance)
            dateBand = image.select("date")
            date = dateBand.reduceRegion(ee.Reducer.first(), vatican, 10).get("date")
            assert image.bandNames().size().getInfo() > 1
            assert ee.Date(date).format("YYYY-MM-DD").getInfo() == "2020-01-01"

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        return ee.Image(
            "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        )

    @pytest.fixture
    def vatican(self):
        """A 10 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)


class TestAddSuffix:
    """Test the ``addSuffix`` method."""

    def test_add_suffix_to_all(self, image_instance):
        image = image_instance.geetools.addSuffix("_suffix")
        assert image.bandNames().size().getInfo() > 1
        assert image.bandNames().getInfo() == [
            "B1_suffix",
            "B2_suffix",
            "B3_suffix",
        ]

    def test_add_suffix_to_selected(self, image_instance):
        image = image_instance.geetools.addSuffix("_suffix", bands=["B1", "B2"])
        assert image.bandNames().size().getInfo() > 1
        assert image.bandNames().getInfo() == ["B1_suffix", "B2_suffix", "B3"]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.addSuffix(
                image_instance, "_suffix", ["B1", "B2"]
            )
            assert image.bandNames().getInfo() == ["B1_suffix", "B2_suffix", "B3"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestAddPrefix:
    """Test the ``addPrefix`` method."""

    def test_add_prefix_to_all(self, image_instance):
        image = image_instance.geetools.addPrefix("prefix_")
        assert image.bandNames().size().getInfo() > 1
        assert image.bandNames().getInfo() == [
            "prefix_B1",
            "prefix_B2",
            "prefix_B3",
        ]

    def test_add_prefix_to_selected(self, image_instance):
        image = image_instance.geetools.addPrefix("prefix_", bands=["B1", "B2"])
        assert image.bandNames().size().getInfo() > 1
        assert image.bandNames().getInfo() == ["prefix_B1", "prefix_B2", "B3"]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.addPrefix(
                image_instance, "prefix_", ["B1", "B2"]
            )
            assert image.bandNames().getInfo() == ["prefix_B1", "prefix_B2", "B3"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestGetValues:
    """Test the ``getValues`` method."""

    def test_get_values(self, image_instance, vatican):
        values = image_instance.geetools.getValues(vatican)
        assert values.getInfo() == {"B1": 218, "B2": 244, "B3": 251}

    def test_get_values_with_scale(self, image_instance, vatican):
        values = image_instance.geetools.getValues(vatican, scale=100)
        assert values.getInfo() == {"B1": 117, "B2": 161, "B3": 247}

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            values = geetools.tools.image.getValue(image_instance, vatican)
            assert values.getInfo() == {"B1": 218, "B2": 244, "B3": 251}

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])

    @pytest.fixture
    def vatican(self):
        """Return a vatican in the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9029])


class TestMinScale:
    """Test the ``minScale`` method."""

    def test_min_scale(self, image_instance):
        scale = image_instance.geetools.minScale()
        assert scale.getInfo() == 10

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            scale = geetools.tools.image.minscale(image_instance)
            assert scale.getInfo() == 10

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestMerge:
    """Test the ``merge`` method."""

    def test_merge(self, image_instance):
        image = image_instance.geetools.merge([image_instance, image_instance])
        assert image.bandNames().getInfo() == [
            "B1",
            "B2",
            "B1_1",
            "B2_1",
            "B1_2",
            "B2_2",
        ]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.addMultiBands([image_instance, image_instance])
            assert image.bandNames().getInfo() == ["B1", "B2", "B1_1", "B2_1"]

    def test_deprecated_method2(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.mixBands([image_instance, image_instance])
            assert image.bandNames().getInfo() == ["B1", "B2", "B1_1", "B2_1"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2"])


class TestRename:
    """Test the ``rename`` method."""

    def test_rename(self, image_instance):
        image = image_instance.geetools.rename({"B1": "newB1", "B2": "newB2"})
        assert image.bandNames().getInfo() == ["newB1", "newB2", "B3"]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.renameDict(
                image_instance, {"B1": "newB1", "B2": "newB2"}
            )
            assert image.bandNames().getInfo() == ["newB1", "newB2", "B3"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestRemove:
    """Test the ``remove`` method."""

    def test_remove(self, image_instance):
        image = image_instance.geetools.remove(["B1", "B2"])
        assert image.bandNames().getInfo() == ["B3"]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.removeBands(image_instance, ["B1", "B2"])
            assert image.bandNames().getInfo() == ["B3"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestToGrid:
    """Test the ``toGrid`` method."""

    def test_to_grid(self, image_instance, vatican, data_regression):
        grid = image_instance.geetools.toGrid(1, "B2", vatican)
        data_regression.check(grid.getInfo())

    def test_deprecated_method(self, image_instance, vatican, data_regression):
        with pytest.deprecated_call():
            grid = geetools.tools.image.toGrid(image_instance, 1, "B2", vatican)
            data_regression.check(grid.getInfo())

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])

    @pytest.fixture
    def vatican(self):
        """Return a buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9029]).buffer(100)


class TestClipOnCollection:
    """Test the ``clipOnCollection`` method."""

    def test_clip_on_collection(self, image_instance, fc_instance):
        clipped = image_instance.geetools.clipOnCollection(fc_instance)
        assert clipped.first().bandNames().getInfo() == ["B1", "B2", "B3"]
        assert clipped.size().getInfo() == 2
        assert "Id" in clipped.first().propertyNames().getInfo()

    def test_clip_on_collection_without_properties(self, image_instance, fc_instance):
        clipped = image_instance.geetools.clipOnCollection(fc_instance, 0)
        assert clipped.first().bandNames().getInfo() == ["B1", "B2", "B3"]
        assert clipped.size().getInfo() == 2
        assert "Id" not in clipped.first().propertyNames().getInfo()

    def test_deprecated_method(self, image_instance, fc_instance):
        with pytest.deprecated_call():
            clipped = geetools.tools.image.clipToCollection(image_instance, fc_instance)
            assert clipped.first().bandNames().getInfo() == ["B1", "B2", "B3"]
            assert clipped.size().getInfo() == 2
            assert "Id" in clipped.first().propertyNames().getInfo()

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])

    @pytest.fixture
    def fc_instance(self):
        """Return 2 little buffers in vaticanc city as a featurecollection."""
        return ee.FeatureCollection(
            [
                ee.Feature(ee.Geometry.Point([12.4534, 41.9029]).buffer(50), {"Id": 1}),
                ee.Feature(
                    ee.Geometry.Point([12.4534, 41.9029]).buffer(100), {"Id": 2}
                ),
            ]
        )


class TestBufferMask:
    """Test the ``bufferMask`` method."""

    @pytest.mark.xfail
    def test_buffer_mask(self, image_instance, vatican):
        """I don't know what to test here."""
        assert False


class TestFull:
    """Test the ``full`` method."""

    def test_full(self, vatican):
        image = ee.Image.geetools.full()
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert values.getInfo() == {"constant": 0}

    def test_full_with_value(self, vatican):
        image = ee.Image.geetools.full([1])
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert values.getInfo() == {"constant": 1}

    def test_full_with_name(self, vatican):
        image = ee.Image.geetools.full([1], ["toto"])
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert values.getInfo() == {"toto": 1}

    def test_full_with_lists(self, vatican):
        image = ee.Image.geetools.full([1, 2, 3], ["toto", "titi", "tata"])
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert values.getInfo() == {"toto": 1, "titi": 2, "tata": 3}

    def test_deprecated_method(self, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.empty()
            values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
            assert values.getInfo() == {"constant": 0}

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)


class TestFullLike:
    """Test the ``fullLike`` method."""

    def test_full_like(self, vatican, image_instance):
        image = image_instance.geetools.fullLike(0)
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert "props" not in image.propertyNames().getInfo()
        assert values.getInfo() == {"B1": 0, "B2": 0, "B3": 0}

    def test_full_like_with_properties(self, image_instance):
        image = image_instance.geetools.fullLike(0, copyProperties=1)
        assert "props" in image.propertyNames().getInfo()

    def test_full_like_with_mask(self, image_instance):
        image = image_instance.geetools.fullLike(0, keepMask=1)
        values = image.geetools.getValues(ee.Geometry.Point(0, 0))
        assert values.getInfo() == {"B1": None, "B2": None, "B3": None}

    def test_deprecated_method(self, vatican, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.emptyCopy(image_instance)
            values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
            assert values.getInfo() == {"B1": 0, "B2": 0, "B3": 0}

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)

    @pytest.fixture
    def image_instance(self, vatican):
        """Return an Image instance masked over the vatican."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        image = ee.Image(src).select(["B1", "B2", "B3"])
        return image.set({"props": "toto"}).clip(vatican)


class TestReduceBands:
    """Test the ``reduceBands`` method."""

    def test_reduce_bands(self, image_instance, vatican):
        image = image_instance.geetools.reduceBands("sum")
        values = image.select("sum").reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert "sum" in image.bandNames().getInfo()
        assert values.getInfo() == {"sum": 2333.794228356336}

    def test_reduce_bands_with_bands(self, image_instance, vatican):
        image = image_instance.geetools.reduceBands("sum", ["B1", "B2"])
        values = image.select("sum").reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert "sum" in image.bandNames().getInfo()
        assert values.getInfo() == {"sum": 1008.5144291091593}

    def test_reduce_bands_with_name(self, image_instance, vatican):
        image = image_instance.geetools.reduceBands("sum", name="toto")
        values = image.select("toto").reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert "toto" in image.bandNames().getInfo()
        assert values.getInfo() == {"toto": 2333.794228356336}

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.sumBands(image_instance, "sum", ["B1", "B2"])
            values = image.select("sum").reduceRegion(ee.Reducer.mean(), vatican, 1)
            assert "sum" in image.bandNames().getInfo()
            assert values.getInfo() == {"sum": 1008.5144291091593}

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(1)


class TestNegativeClip:
    """Test the ``negativeClip`` method."""

    def test_negative_clip(self, image_instance, vatican):
        image = image_instance.geetools.negativeClip(vatican)
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"B1": None, "B2": None, "B3": None}

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(1)

    @pytest.fixture
    def image_instance(self, vatican):
        """The first image in COpernicus hovering the vatican."""
        src, bands = "COPERNICUS/S2_SR_HARMONIZED", ["B1", "B2", "B3"]
        return ee.ImageCollection(src).filterBounds(vatican).first().select(bands)


class testFormat:
    """Test the ``toString`` method."""

    def test_to_string(self, image_instance):
        string = image_instance.geetools.toString("date: {system_date}")
        assert string.getInfo() == "date: 2020-01-01"

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            string = geetools.tools.image.makeName(
                image_instance, "date: {system_date}"
            )
            assert string.getInfo() == "date: 2020-01-01"

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestPrefixSuffix:
    """Test the ``prefix`` and ``suffix`` methods."""

    def test_prefix(self, image_instance):
        image = image_instance.geetools.addPrefix("prefix_")
        assert image.bandNames().getInfo() == ["prefix_B1", "prefix_B2", "prefix_B3"]

    def test_suffix(self, image_instance):
        image = image_instance.geetools.addSuffix("_suffix")
        assert image.bandNames().getInfo() == ["B1_suffix", "B2_suffix", "B3_suffix"]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.renamePattern(
                image_instance, "prefix_{band}_suffix"
            )
            assert image.bandNames().getInfo() == [
                "prefix_B1_suffix",
                "prefix_B2_suffix",
                "prefix_B3_suffix",
            ]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestGauss:
    """Test the ``gauss`` method."""

    def test_gauss(self, image_instance, vatican):
        image = image_instance.geetools.gauss()
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"B1_gauss": 0.5596584633629059}

    def test_gauss_with_band(self, image_instance, vatican):
        image = image_instance.geetools.gauss("B2")
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"B2_gauss": 0.11127562017793}

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.gaussFunction(image_instance, "B2")
            values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
            assert values.getInfo() == {"B2_gauss": 0.11127562017793}

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(1)

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3"])


class TestDoyToDate:
    """Test the ``doyToDate`` method."""

    def test_doy_to_date(self, image_instance, vatican):
        image = image_instance.geetools.doyToDate(2023)
        values = image.reduceRegion(ee.Reducer.min(), vatican, 1)
        assert values.getInfo() == {"doy1": 20230101}

    def test_doy_to_date_with_format(self, image_instance, vatican):
        image = image_instance.geetools.doyToDate(2023, dateFormat="yyyy.DDD")
        values = image.reduceRegion(ee.Reducer.min(), vatican, 1)
        assert values.getInfo() == {"doy1": 2023.001}

    def test_doy_to_date_with_band(self, image_instance, vatican):
        image = image_instance.geetools.doyToDate(2023, band="doy2")
        values = image.reduceRegion(ee.Reducer.min(), vatican, 1)
        assert values.getInfo() == {"doy2": 20230101}

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.doyToDate(image_instance, year=2023)
            values = image.reduceRegion(ee.Reducer.min(), vatican, 1)
            assert values.getInfo() == {"doy1": 20230101}

    @pytest.fixture
    def vatican(self):
        """A 10 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9029]).buffer(100)

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance with 2 random doy bands."""
        doy = ee.Image.random(seed=0).multiply(365).toInt().rename("doy1")
        return doy.rename("doy1").addBands(doy.rename("doy2"))


class TestRepeat:
    """Test the ``repeat`` method."""

    def test_repeat(self, image_instance):
        image = image_instance.geetools.repeat("B1", 2)
        assert image.bandNames().getInfo() == ["B1", "B2", "B3", "B1_1", "B1_2"]

    def test_deprecated_method(self, image_instance):
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

    def test_histogram_match(
        self, image_source, image_target, vatican, data_regression
    ):
        bands = {"R": "R", "G": "G", "B": "B"}
        image = image_source.geetools.matchHistogram(image_target, bands)
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        data_regression.check(values.getInfo())

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9029]).buffer(1)

    @pytest.fixture
    def dates(self):
        """The dates of my imagery."""
        return "2023-06-01", "2023-06-30"

    @pytest.fixture
    def image_source(self, vatican, dates):
        """image from the S2 copernicus program over vatican city."""
        return (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(vatican)
            .filterDate(*dates)
            .first()
            .select("B4", "B3", "B2")
            .rename("R", "G", "B")
        )

    @pytest.fixture
    def image_target(self, vatican, dates):
        """image from the L8 Landsat program over vatican city."""
        return (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(vatican)
            .filterDate(*dates)
            .first()
            .select("SR_B4", "SR_B3", "SR_B2")
            .rename("R", "G", "B")
        )


class TestRemoveZeros:
    """Test the ``removeZeros`` method."""

    def test_remove_zeros(self, image_instance, vatican):
        image = image_instance.geetools.removeZeros()
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert values.getInfo() == {"array": [1, 2]}

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.arrayNonZeros(image_instance)
            values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
            assert values.getInfo() == {"array": [1, 2]}

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(1)

    @pytest.fixture
    def image_instance(self):
        """A random image instance with array data containing zeros."""
        return ee.Image([0, 1, 2]).toArray()


class TestInterpolateBands:
    """Test the ``interpolateBands`` method."""

    def test_interpolate_bands(self, image_instance, vatican):
        image = image_instance.geetools.interpolateBands([0, 3000], [0, 30])
        values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
        assert values.getInfo() == {"B2": 11.79, "B4": 19.04}

    def test_deprecated_method(self, image_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.parametrize(image_instance, [0, 3000], [0, 30])
            values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
            assert values.getInfo() == {"B2": 11.79, "B4": 19.04}

    def test_deprecated_method_2(self, image_instance, vatican):
        with pytest.deprecated_call():
            band = image_instance.bandNames().get(0)
            image = geetools.tools.image.linearFunction(
                image_instance, band, 0, 3000, output_min=0, output_max=30
            )
            values = image.reduceRegion(ee.Reducer.first(), vatican, 1)
            assert values.getInfo() == {"B4": 19.04}

    @pytest.fixture
    def vatican(self):
        """A 1 m buffer around the Vatican."""
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(1)

    @pytest.fixture
    def image_instance(self, vatican):
        """A sentinel 2 single image centered on the vatican."""
        src = "COPERNICUS/S2_SR_HARMONIZED"
        return (
            ee.ImageCollection(src).filterBounds(vatican).first().select(["B4", "B2"])
        )


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

    def test_default_spectral_indices(self, image_instance, vatican, data_regression):
        image = image_instance.geetools.spectralIndices("all")
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        data_regression.check(values.getInfo())

    @pytest.fixture
    def image_instance(self):
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src)

    @pytest.fixture
    def vatican(self):
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)


class TestMaskClouds:
    """Test the ``maskClouds`` method."""

    def test_mask_S2_clouds(self, image_instance, vatican, data_regression):
        image = image_instance.geetools.maskClouds()
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        data_regression.check(values.getInfo())

    @pytest.fixture
    def image_instance(self):
        src = "COPERNICUS/S2/20230105T100319_20230105T100317_T32TQM"
        return ee.Image(src)

    @pytest.fixture
    def vatican(self):
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)


class TestGetscaleParams:
    """Test the ``getScaleParams`` method."""

    def test_get_scale_params(self, data_regression):
        params = (
            ee.ImageCollection("MODIS/006/MOD11A2").first().geetools.getScaleParams()
        )
        data_regression.check(params)


class TestGetOffsetParams:
    """Test the ``getOffsetParams`` method."""

    def get_offset_params(self, data_regression):
        params = (
            ee.ImageCollection("MODIS/006/MOD11A2").first().geetools.getOffsetParams()
        )
        data_regression.check(params)


class TestScaleAndOffset:
    """Test the ``scaleAndOffset`` method."""

    def test_scale_and_offset(self, vatican, image_instance, data_regression):
        image = image_instance.geetools.scaleAndOffset()
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        data_regression.check(values.getInfo())

    @pytest.fixture
    def vatican(self):
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)

    @pytest.fixture
    def image_instance(self):
        src = "COPERNICUS/S2/20230105T100319_20230105T100317_T32TQM"
        return ee.Image(src)


class TestPreprocess:
    """Test the ``preprocess`` method."""

    def test_preprocess(self, vatican, image_instance, data_regression):
        image = image_instance.geetools.preprocess()
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        data_regression.check(values.getInfo())

    @pytest.fixture
    def vatican(self):
        return ee.Geometry.Point([12.4534, 41.9033]).buffer(100)

    @pytest.fixture
    def image_instance(self):
        src = "COPERNICUS/S2/20230105T100319_20230105T100317_T32TQM"
        return ee.Image(src)


class TestGetSTAC:
    """Test the ``getSTAC`` method."""

    def test_get_stac(self, data_regression):
        stac = ee.ImageCollection("COPERNICUS/S2_SR").first().geetools.getSTAC()
        data_regression.check(stac)


class TestGetDOI:
    """Test the ``getDOI`` method."""

    def get_doi(self, data_regression):
        doi = ee.ImageCollection("COPERNICUS/S2_SR").first().geetools.getDOI()
        data_regression.check(doi)


class TestGetCitation:
    """Test the ``getCitation`` method."""

    def get_citation(self, data_regression):
        citation = ee.ImageCollection("COPERNICUS/S2_SR").first().geetools.getCitation()
        data_regression.check(citation)


class TestPanSharpen:
    """Test the panSharpen method."""

    def test_pan_sharpen(self, data_regression):
        source = ee.Image("LANDSAT/LC08/C01/T1_TOA/LC08_047027_20160819")
        sharp = source.geetools.panSharpen(
            method="HPFA", qa=["MSE", "RMSE"], maxPixels=1e13
        )
        centroid = sharp.geometry().centroid().buffer(100)
        values = sharp.reduceRegion(ee.Reducer.mean(), centroid, 1)
        data_regression.check(values.getInfo())


class TestTasseledCap:
    """Test the tasseledCap method."""

    def test_tasseled_cap(self, data_regression):
        img = ee.Image("LANDSAT/LT05/C01/T1/LT05_044034_20081011")
        img = img.geetools.tasseledCap()
        centroid = img.geometry().centroid().buffer(100)
        values = img.reduceRegion(ee.Reducer.mean(), centroid, 1)
        data_regression.check(values.getInfo())
