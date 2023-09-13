"""Test the List class methods."""
import ee
import pytest

import geetools


class TestProduct:
    """Test the product method."""

    def test_product_with_same_type(self, list_instance):
        product_list = list_instance.geetools.product(list_instance)
        expected = ["aa", "ab", "ac", "ba", "bb", "bc", "ca", "cb", "cc"]
        assert product_list.getInfo() == expected

    @pytest.mark.xfail
    def test_product_with_different_type(self, list_instance, list_int):
        """waiting for https://gis.stackexchange.com/questions/466702/compute-the-cartesian-product-of-2-ee-lists."""
        product_list = list_instance.geetools.product(list_int)
        expected = ["a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "c3"]
        assert product_list.getInfo() == expected

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            product_list = geetools.string.mix([list_instance, list_instance])
            expected = ["aa", "ab", "ac", "ba", "bb", "bc", "ca", "cb", "cc"]
            assert product_list.getInfo() == expected

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", "b", "c"])

    @pytest.fixture
    def list_int(self):
        """Return a defined list instance."""
        return ee.List([1, 2, 3])


class TestComplement:
    """Test the complement method."""

    def test_complement_with_same_type(self, list_instance):
        complement_list = list_instance.geetools.complement(list_instance)
        assert complement_list.getInfo() == []

    def test_complement_with_different_type(self, list_instance, list_int):
        complement_list = list_instance.geetools.complement(list_int)
        assert complement_list.getInfo() == ["a", "b", "c", 1, 2, 3]

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            complement_list = geetools.tools.ee_list.difference(
                list_instance, list_instance
            )
            assert complement_list.getInfo() == []

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", "b", "c"])

    @pytest.fixture
    def list_int(self):
        """Return a defined list instance."""
        return ee.List([1, 2, 3])
