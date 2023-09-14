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
            "B4_suffix",
        ]

    def test_add_suffix_to_selected(self, image_instance):
        image = image_instance.geetools.addSuffix("_suffix", bands=["B1", "B2"])
        assert image.bandNames().size().getInfo() > 1
        assert image.bandNames().getInfo() == ["B1_suffix", "B2_suffix", "B3", "B4"]

    def test_deprecated_method(self, image_instance):
        with pytest.deprecated_call():
            image = geetools.tools.image.addSuffix(
                image_instance, "_suffix", ["B1", "B2"]
            )
            assert image.bandNames().getInfo() == ["B1_suffix", "B2_suffix", "B3", "B4"]

    @pytest.fixture
    def image_instance(self):
        """Return an Image instance."""
        src = "COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM"
        return ee.Image(src).select(["B1", "B2", "B3", "B4"])
