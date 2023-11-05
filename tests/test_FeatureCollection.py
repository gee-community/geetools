"""Test the ``FeatureCollection`` class."""
import ee
import pytest

import geetools


class TestToImage:
    """Test the ``toImage`` method."""

    def test_to_image(self, fc_instance, vatican):
        image = fc_instance.geetools.toImage()
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"constant": 0}

    def test_to_image_with_color(self, fc_instance, vatican):
        image = fc_instance.geetools.toImage(color="ADM0_CODE")
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"constant": 110}

    @pytest.mark.skip(reason="Not working yet")
    def test_deprecated_method(self, fc_instance, vatican):
        with pytest.deprecated_call():
            image = geetools.tools.image.paint(ee.Image(), fc_instance)
            values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
            assert values.getInfo() == {"constant": 110}

    @pytest.fixture
    def fc_instance(self):
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level0")
        return gaul.filter(ee.Filter.eq("ADM0_CODE", 110))

    @pytest.fixture
    def vatican(self):
        """Return a buffer around the Vatican City."""
        return ee.Geometry.Point([12.453386, 41.903282]).buffer(1)


class TestAddId:
    """Test the ``addId`` method."""

    def test_add_id(self, fc_instance):
        fc = fc_instance.geetools.addId()
        assert fc.first().get("id").getInfo() == 1

    def test_deprecated_method(self, fc_instance):
        with pytest.deprecated_call():
            fc = geetools.tools.featurecollection.addId(fc_instance)
            assert fc.first().get("id").getInfo() == 1

    @pytest.fixture
    def fc_instance(self):
        return ee.FeatureCollection("FAO/GAUL/2015/level0").limit(10)
