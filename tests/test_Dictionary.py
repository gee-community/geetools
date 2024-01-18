"""Test the Dictionary class methods."""
import ee
import pytest

import geetools


class TestFromPairs:
    """Test the fromPairs method."""

    def test_from_pairs_with_list(self):
        d = ee.Dictionary.geetools.fromPairs([["foo", 1], ["bar", 2]])
        assert d.getInfo() == {"foo": 1, "bar": 2}

    def test_from_pairs_with_ee_list(self):
        d = ee.Dictionary.geetools.fromPairs(ee.List([["foo", 1], ["bar", 2]]))
        assert d.getInfo() == {"foo": 1, "bar": 2}

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            d = geetools.tools.dictionary.fromList([["foo", 1], ["bar", 2]])
            assert d.getInfo() == {"foo": 1, "bar": 2}


class TestSort:
    """Test the sort method."""

    def test_sort(self):
        d = ee.Dictionary({"foo": 1, "bar": 2}).geetools.sort()
        assert d.getInfo() == {"bar": 2, "foo": 1}

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            d = ee.Dictionary({"foo": 1, "bar": 2})
            d = geetools.tools.dictionary.sort(d)
            assert d.getInfo() == {"bar": 2, "foo": 1}


class TestGetMany:
    """Test the getMany method."""

    def test_getMany(self):
        d = ee.Dictionary({"foo": 1, "bar": 2}).geetools.getMany(["foo"])
        assert d.getInfo() == [1]

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            d = ee.Dictionary({"foo": 1, "bar": 2})
            li = geetools.tools.dictionary.extractList(d, ["foo"])
            assert li.getInfo() == [1]

    def test_deprecated_list_method(self):
        with pytest.deprecated_call():
            d = ee.Dictionary({"foo": 1, "bar": 2})
            li = geetools.tools.ee_list.getFromDict(["foo"], d)
            assert li.getInfo() == [1]
