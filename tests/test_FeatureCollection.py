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


class TestMergeGeometries:
    """Test the ``mergeGeometries`` method."""

    def test_merge_geometries(self, fc_instance, data_regression):
        geom = fc_instance.geetools.mergeGeometries()
        data_regression.check(geom.getInfo())

    def test_deprecated_merge(self, fc_instance, data_regression):
        with pytest.deprecated_call():
            geom = geetools.tools.featurecollection.mergeGeometries(fc_instance)
            data_regression.check(geom.getInfo())

    @pytest.fixture
    def fc_instance(self):
        """Return Italy switzerland and France."""
        fc = ee.FeatureCollection("FAO/GAUL/2015/level0")
        return fc.filter(ee.Filter.inList("ADM0_CODE", [122, 237, 85]))


class TestToPolygons:
    """Test the ``toPolygons`` method."""

    def test_to_polygons(self, fc_instance, data_regression):
        fc = fc_instance.geetools.toPolygons()
        data_regression.check(fc.getInfo())

    def test_deprecated_clean(self, fc_instance, data_regression):
        with pytest.deprecated_call():
            fc = geetools.tools.featurecollection.clean(fc_instance)
            data_regression.check(fc.getInfo())

    @pytest.fixture
    def fc_instance(self):
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
