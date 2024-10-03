"""Test the Dictionary class methods."""
import ee


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
