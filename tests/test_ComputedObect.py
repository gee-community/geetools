"""Test the ComputedObject class methods."""
import ee
import pytest

import geetools


class TestIsinstance:
    """Test the isInstance method."""

    def test_isinstance_with_string(self):
        assert ee.String("").isInstance(ee.String).getInfo() == 1

    def test_isinstance_with_integer(self):
        assert ee.Number(1).isInstance(ee.Integer).getInfo() == 1

    def test_isinstance_with_float(self):
        assert ee.Number(1.1).isInstance(ee.Float).getInfo() == 1

    def test_isinstance_with_image(self):
        assert ee.Image().isInstance(ee.Image).getInfo() == 1

    def test_isinstance_with_imagecollection(self):
        ic = ee.ImageCollection([ee.Image()])
        assert ic.isInstance(ee.ImageCollection).getInfo() == 1

    def test_isinstance_with_feature(self):
        assert ee.Feature(None).isInstance(ee.Feature).getInfo() == 1

    def test_isinstance_with_geometry(self):
        assert ee.Geometry.Point([0, 0]).isInstance(ee.Geometry).getInfo() == 1

    def test_deprecated_string(self):
        with pytest.deprecated_call():
            s = ee.String("")
            assert geetools.tools.computedobject.isString(s).getInfo() == 1

    def test_deprecated_integer(self):
        with pytest.deprecated_call():
            i = ee.Number(1)
            assert geetools.tools.computedobject.isInteger(i).getInfo() == 1

    def test_deprecated_float(self):
        with pytest.deprecated_call():
            f = ee.Number(1.1)
            assert geetools.tools.computedobject.isFloat(f).getInfo() == 1

    def test_deprecated_image(self):
        with pytest.deprecated_call():
            i = ee.Image()
            assert geetools.tools.computedobject.isImage(i).getInfo() == 1

    def test_deprecated_imagecollection(self):
        with pytest.deprecated_call():
            ic = ee.ImageCollection([ee.Image()])
            assert geetools.tools.computedobject.isImageCollection(ic).getInfo() == 1

    def test_deprecated_feature(self):
        with pytest.deprecated_call():
            f = ee.Feature(None)
            assert geetools.tools.computedobject.isFeature(f).getInfo() == 1

    def test_deprecated_geometry(self):
        with pytest.deprecated_call():
            g = ee.Geometry.Point([0, 0])
            assert geetools.tools.computedobject.isGeometry(g).getInfo() == 1


class TestSave:
    """Test the ``save`` method."""

    def test_save(self, image_instance, tmp_path):
        file = tmp_path / "test.gee"
        image_instance.save(file)
        assert file.exists()

    def test_deprecated_method(self, image_instance, tmp_path):
        file = tmp_path / "test.gee"
        with pytest.deprecated_call():
            geetools.manager.esave(image_instance, file)
            assert file.exists()

    @pytest.fixture
    def image_instance(self):
        """Return an image instance."""
        return ee.Image("COPERNICUS/S2/20151128T112653_20151128T135750_T29SND")


class TestOpen:
    """Test the ``open`` method."""

    def test_open(self, fc_instance, tmp_path):
        file = tmp_path / "test.gee"
        fc_instance.save(file)
        fc_open = ee.FeatureCollection.open(file)
        list_instance = fc_instance.toList(fc_instance.size())
        list_open = fc_open.toList(fc_open.size())
        assert list_instance.equals(list_open).getInfo()

    def test_deprecated_method(self, fc_instance, tmp_path):
        file = tmp_path / "test.gee"
        fc_instance.save(file)
        with pytest.deprecated_call():
            fc_open = geetools.manager.eopen(file)
            list_instance = fc_instance.toList(fc_instance.size())
            list_open = fc_open.toList(fc_open.size())
            assert list_instance.equals(list_open).getInfo()

    @pytest.fixture
    def fc_instance(self):
        """Return a feature collection instance."""
        return ee.FeatureCollection("FAO/GAUL/2015/level0")
