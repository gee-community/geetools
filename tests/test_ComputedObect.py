"""Test the ComputedObject class methods."""

import ee
import pytest


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


class TestSave:
    """Test the ``save`` method."""

    def test_save(self, tmp_path):
        file = tmp_path / "test.gee"
        ee.Number(1.1).save(file)
        assert file.exists()


class TestOpen:
    """Test the ``open`` method."""

    def test_open(self, tmp_path):
        (object := ee.Number(1.1)).save((file := tmp_path / "test.gee"))
        opened = ee.Number.open(file)
        assert object.eq(opened).getInfo()

    def test_open_not_correct_suffix(self):
        with pytest.raises(ValueError):
            ee.Number.open("file.toto")
