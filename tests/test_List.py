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

    def test_product_with_different_type(self, list_instance, list_int):
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


class TestIntersection:
    """Test the intersection method."""

    def test_intersection_with_same_type(self, list_instance):
        intersection_list = list_instance.geetools.intersection(list_instance)
        assert intersection_list.getInfo() == ["a", "b", "c"]

    def test_intersection_with_different_type(self, list_instance, list_int):
        intersection_list = list_instance.geetools.intersection(list_int)
        assert intersection_list.getInfo() == []

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            intersection_list = geetools.tools.ee_list.intersection(
                list_instance, list_instance
            )
            assert intersection_list.getInfo() == ["a", "b", "c"]

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", "b", "c"])

    @pytest.fixture
    def list_int(self):
        """Return a defined list instance."""
        return ee.List([1, 2, 3])


class TestUnion:
    """Test the union method."""

    def test_union_with_duplicate(self, list_instance):
        union_list = list_instance.geetools.union(list_instance)
        assert union_list.getInfo() == ["a", "b", "c"]

    def test_union_without_dupplicates(self, list_instance, list_int):
        union_list = list_instance.geetools.union(list_int)
        assert union_list.getInfo() == ["a", "b", "c", 1, 2, 3]

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", "b", "c"])

    @pytest.fixture
    def list_int(self):
        """Return a defined list instance."""
        return ee.List([1, 2, 3])


class TestDelete:
    """Test the delete method."""

    def test_delete(self, list_instance):
        deleted_list = list_instance.geetools.delete(1)
        assert deleted_list.getInfo() == ["a", "c"]

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            deleted_list = geetools.tools.ee_list.removeIndex(list_instance, 1)
            assert deleted_list.getInfo() == ["a", "c"]

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", "b", "c"])


@pytest.mark.xfail
class TestSequence:
    """Test the sequence method.

    waiting for https://gis.stackexchange.com/questions/466871/how-to-remove-duplicates-from-a-ee-list
    """

    def test_sequence(self):
        seq = ee.List.geetools.sequence(1, 10)
        assert seq.getInfo() == list(range(1, 11))

    def test_sequence_with_step(self):
        seq = ee.List.geetools.sequence(1, 10, 2)
        assert seq.getInfo() == list(range(1, 11, 2))

    def test_sequence_with_uneven_step(self):
        seq = ee.List.geetools.sequence(1, 10, 3)
        assert seq.getInfo() == list(range(1, 10, 3)) + [10]

    def test_sequence_with_0_step(self):
        seq = ee.List.geetools.sequence(1, 10, 0)
        assert seq.getInfo() == list(range(1, 10))

    def test_sequence_with_negative_step(self):
        seq = ee.List.geetools.sequence(10, 1, -1)
        assert seq.getInfo() == list(range(10, 1, -1))

    def test_sequence_with_negative_and_uneven_step(self):
        seq = ee.List.geetools.sequence(10, 1, -3)
        assert seq.getInfo() == list(range(10, 1, -3)) + [1]

    def test_deprecated_method(self):
        with pytest.deprecated_call():
            seq = geetools.tools.ee_list.sequence(1, 10)
            assert seq.getInfo() == list(range(1, 10))


class TestReplaceMany:
    """Test the replaceMany method."""

    def test_replace_many(self, list_instance):
        replaced_list = list_instance.geetools.replaceMany({"a": "foo", "c": "bar"})
        assert replaced_list.getInfo() == ["foo", "b", "bar"]

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            replaced_list = geetools.tools.ee_list.replaceDict(
                list_instance, {"a": "foo", "c": "bar"}
            )
            assert replaced_list.getInfo() == ["foo", "b", "bar"]

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", "b", "c"])


class TestToStrings:
    """Test the toStrings method."""

    def test_to_strings(self, list_instance):
        strings = list_instance.geetools.toStrings()
        assert strings.getInfo() == ["a", "1", "Image"]

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            strings = geetools.tools.ee_list.toString(list_instance)
            assert strings.getInfo() == ["a", "1", "Image"]

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", 1, ee.Image(1)])


class TestJoin:
    """Test the join method."""

    def test_join(self, list_instance):
        formatted = list_instance.geetools.join()
        assert formatted.getInfo() == "a, 1, Image"

    def test_join_with_separator(self, list_instance):
        formatted = list_instance.geetools.join(separator="; ")
        assert formatted.getInfo() == "a; 1; Image"

    def test_deprecated_method(self, list_instance):
        with pytest.deprecated_call():
            formatted = geetools.tools.ee_list.format(list_instance)
            assert formatted.getInfo() == "[a,1,Image]"

    @pytest.fixture
    def list_instance(self):
        """Return a defined list instance."""
        return ee.List(["a", 1, ee.Image(1)])
