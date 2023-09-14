"""Test the ``Image`` class."""
import ee
import pytest

import geetools


class TestAddDate:
    """Test the ``addDate`` method."""

    def test_add_date(self, image_instance):
        image = image_instance.geetools.addDate()
        date = image.select("date").reduceRegion(ee.Reducer.first()).get("date")
        assert image.bandNames().size().getInfo() > 1
        assert ee.Date(date).format("YYYY-MM-DD").getInfo() == "2020-01-01"

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.date.makeDateBand(image_instance)
            date = image.select("date").reduceRegion(ee.Reducer.first()).get("date")
            assert image.bandNames().size().getInfo() > 1
            assert ee.Date(date).format("YYYY-MM-DD").getInfo() == "2020-01-01"

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        return ee.Image(
            "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        )


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
