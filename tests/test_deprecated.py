"""Test all the deprecated methods that have not been kept in the new implementation."""

from datetime import datetime

import ee
import pytest

import geetools


class TestVizualisation:
    """Test methods from the deprecated_visualization module."""

    def test_stretch_std(self):
        with pytest.raises(NotImplementedError):
            geetools.visualization.stretch_std(None, None)

    def test_stretch_percentile(self):
        with pytest.raises(NotImplementedError):
            geetools.visualization.stretch_percentile(None, None)


class TestDate:
    """Test methods from the deprecated_date module."""

    def test_millis_to_datetime(self):
        with pytest.deprecated_call():
            date = geetools.date.millisToDatetime(1527811200000)
            assert date == datetime.strptime("2018-06-01", "%Y-%m-%d")


class TestCollection:
    """Test methods from the deprecated_collection module."""

    def test_enumerate(self):
        with pytest.raises(NotImplementedError):
            geetools.collection.enumerate(None)


class TestElement:
    """Test the methods from the deprecated_element module."""

    def test_fillNull(self):
        with pytest.raises(NotImplementedError):
            geetools.element.fillNull(None, None)


class TestDecisionTree:
    """Test the methods from the deprecated_decision_tree module."""

    def test_deprecated_binary(self):
        with pytest.raises(NotImplementedError):
            geetools.decision_tree.binary(None, None)


class TestUtils:
    """Test the methods from the deprecated_utils module."""

    def test_get_reduce_name(self):
        with pytest.deprecated_call():
            name = geetools.utils.getReducerName(ee.Reducer.min)
            assert name == "min"

    def test_reduce_regions_pandas(self):
        with pytest.raises(NotImplementedError):
            geetools.utils.reduceRegionsPandas(None)

    def test_deprecated_cast_image(self, data_regression):
        point = ee.Geometry.Point(0, 0).buffer(10)
        with pytest.deprecated_call():
            image = geetools.utils.castImage(1)
            values = image.reduceRegion(ee.Reducer.first(), point, 10)
            data_regression.check(values.getInfo())

    def test_dict_2_tuple(self):
        with pytest.raises(NotImplementedError):
            geetools.utils.dict2namedtuple(None)

    def test_format_viz_params(self):
        with pytest.raises(NotImplementedError):
            geetools.utils.formatVisParams(None)

    def test_evaluate(self):
        with pytest.raises(NotImplementedError):
            geetools.utils.evaluate(None, None, None)


class TestImageCollection:
    """Test the deprecated_imagecollection module."""

    def test_get_id(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.getId(None)

    def test_wrapper(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.wrapper(None)

    def test_merge_geometry(self, s2_sr, data_regression):
        with pytest.deprecated_call():
            geom = geetools.imagecollection.mergeGeometries(s2_sr.limit(10))
            data_regression.check(geom.getInfo())

    def test_data2pandas(self):
        with pytest.raises(NotImplementedError):
            geetools.imagecollection.data2pandas(None)

    def test_tobands(self, s2_sr, data_regression):
        with pytest.deprecated_call():
            image = geetools.imagecollection.toBands(s2_sr.limit(3))
            data_regression.check(image.bandNames().getInfo())
