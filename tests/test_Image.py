"""Test the ``Image`` class."""
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
