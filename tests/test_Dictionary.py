"""Test the Dictionary class methods."""
import ee

import geetools  # noqa: F401


class TestFromPairs:
    """Test the fromPairs method."""

    def test_from_pairs_with_list(self):
        d = ee.Dictionary.geetools.fromPairs([["foo", 1], ["bar", 2]])
        assert d.getInfo() == {"foo": 1, "bar": 2}

    def test_from_pairs_with_ee_list(self):
        d = ee.Dictionary.geetools.fromPairs(ee.List([["foo", 1], ["bar", 2]]))
        assert d.getInfo() == {"foo": 1, "bar": 2}


class TestSort:
    """Test the sort method."""

    def test_sort(self):
        d = ee.Dictionary({"foo": 1, "bar": 2}).geetools.sort()
        assert d.getInfo() == {"bar": 2, "foo": 1}


class TestGetMany:
    """Test the getMany method."""

    def test_getMany(self):
        d = ee.Dictionary({"foo": 1, "bar": 2}).geetools.getMany(["foo"])
        assert d.getInfo() == [1]


class TestToTable:
    """Test the `toTable` method."""

    def test_to_table_any(self, data_regression):
        ee_dict = ee.Dictionary({"foo": 1, "bar": 2})
        res = ee_dict.geetools.toTable()
        data_regression.check(res.getInfo())

    def test_to_table_list(self, data_regression):
        ee_dict = ee.Dictionary({"Argentina": [12, 278.289196625], "Armenia": [13, 3.13783139285]})
        res = ee_dict.geetools.toTable("list")
        data_regression.check(res.getInfo())

    def test_to_table_dict(self, data_regression):
        ee_dict = ee.Dictionary(
            {
                "Argentina": {"ADM0_CODE": 12, "Shape_Area": 278.289196625},
                "Armenia": {"ADM0_CODE": 13, "Shape_Area": 3.13783139285},
            }
        )
        res = ee_dict.geetools.toTable("dict")
        data_regression.check(res.getInfo())
