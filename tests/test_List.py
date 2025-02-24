"""Test the List class methods."""
import ee

import geetools  # noqa: F401


class TestProduct:
    """Test the product method."""

    def test_product_with_same_type(self, letter_list, ee_list_regression):
        product_list = letter_list.geetools.product(letter_list)
        ee_list_regression.check(product_list, prescision=4)

    def test_product_with_different_type(self, letter_list, int_list, ee_list_regression):
        product_list = letter_list.geetools.product(int_list)
        ee_list_regression.check(product_list, prescision=4)


class TestComplement:
    """Test the complement method."""

    def test_complement_with_same_type(self, letter_list, ee_list_regression):
        complement_list = letter_list.geetools.complement(letter_list)
        ee_list_regression.check(complement_list, prescision=4)

    def test_complement_with_different_type(self, letter_list, int_list, ee_list_regression):
        complement_list = letter_list.geetools.complement(int_list)
        ee_list_regression.check(complement_list, prescision=4)


class TestIntersection:
    """Test the intersection method."""

    def test_intersection_with_same_type(self, letter_list, ee_list_regression):
        intersection_list = letter_list.geetools.intersection(letter_list)
        ee_list_regression.check(intersection_list, prescision=4)

    def test_intersection_with_different_type(self, letter_list, int_list, ee_list_regression):
        intersection_list = letter_list.geetools.intersection(int_list)
        ee_list_regression.check(intersection_list, prescision=4)


class TestUnion:
    """Test the union method."""

    def test_union_with_duplicate(self, letter_list, ee_list_regression):
        union_list = letter_list.geetools.union(letter_list)
        ee_list_regression.check(union_list, prescision=4)

    def test_union_without_dupplicates(self, letter_list, int_list, ee_list_regression):
        union_list = letter_list.geetools.union(int_list)
        ee_list_regression.check(union_list, prescision=4)


class TestDelete:
    """Test the delete method."""

    def test_delete(self, letter_list, ee_list_regression):
        deleted_list = letter_list.geetools.delete(1)
        ee_list_regression.check(deleted_list, prescision=4)


class TestSequence:
    """Test the sequence method."""

    def test_sequence(self):
        seq = ee.List.geetools.sequence(1, 10)
        assert seq.getInfo() == list(range(1, 11))

    def test_sequence_with_step(self):
        seq = ee.List.geetools.sequence(1, 10, 2)
        assert seq.getInfo() == list(range(1, 11, 2)) + [10]

    def test_sequence_with_uneven_step(self):
        seq = ee.List.geetools.sequence(1, 10, 3)
        assert seq.getInfo() == list(range(1, 10, 3)) + [10]

    def test_sequence_with_0_step(self):
        seq = ee.List.geetools.sequence(1, 10, 0)
        assert seq.getInfo() == list(range(1, 11))


class TestReplaceMany:
    """Test the replaceMany method."""

    def test_replace_many(self, letter_list, ee_list_regression):
        replaced_list = letter_list.geetools.replaceMany({"a": "foo", "c": "bar"})
        ee_list_regression.check(replaced_list, prescision=4)


class TestZip:
    """Test the zip method."""

    def test_zip(self, letter_list, ee_list_regression):
        zipped_list = ee.List([letter_list, letter_list]).geetools.zip()
        ee_list_regression.check(zipped_list, prescision=4)


class TestToStrings:
    """Test the toStrings method."""

    def test_to_strings(self, mix_list, data_regression):
        strings = mix_list.geetools.toStrings()
        data_regression.check(strings.getInfo())


class TestJoin:
    """Test the join method."""

    def test_join(self, mix_list):
        formatted = mix_list.geetools.join()
        assert formatted.getInfo() == "a, 1, Image"

    def test_join_with_separator(self, mix_list):
        formatted = mix_list.geetools.join(separator="; ")
        assert formatted.getInfo() == "a; 1; Image"


class TestChunked:
    """Test the chunked method."""

    def test_chunked_even(self, ee_list_regression):
        input = ee.List([1, 2, 3, 4, 5, 6, 7, 8])
        chunked = input.geetools.chunked(4)
        # should return -> [[1, 2], [3, 4], [5, 6], [7, 8]]
        ee_list_regression.check(chunked)

    def test_chunked_odd(self, ee_list_regression):
        input = ee.List([1, 2, 3, 4, 5, 6, 7, 8, 9])
        chunked = input.geetools.chunked(4)
        # should return -> [[1, 2], [3, 4], [5, 6], [7, 8, 9]]
        ee_list_regression.check(chunked)
