"""Test the List class methods."""
import ee


class TestProduct:
    """Test the product method."""

    def test_product_with_same_type(self, letter_list, data_regression):
        product_list = letter_list.geetools.product(letter_list)
        data_regression.check(product_list.getInfo())

    def test_product_with_different_type(self, letter_list, int_list, data_regression):
        product_list = letter_list.geetools.product(int_list)
        data_regression.check(product_list.getInfo())


class TestComplement:
    """Test the complement method."""

    def test_complement_with_same_type(self, letter_list, data_regression):
        complement_list = letter_list.geetools.complement(letter_list)
        data_regression.check(complement_list.getInfo())

    def test_complement_with_different_type(self, letter_list, int_list, data_regression):
        complement_list = letter_list.geetools.complement(int_list)
        data_regression.check(complement_list.getInfo())


class TestIntersection:
    """Test the intersection method."""

    def test_intersection_with_same_type(self, letter_list, data_regression):
        intersection_list = letter_list.geetools.intersection(letter_list)
        data_regression.check(intersection_list.getInfo())

    def test_intersection_with_different_type(self, letter_list, int_list, data_regression):
        intersection_list = letter_list.geetools.intersection(int_list)
        data_regression.check(intersection_list.getInfo())


class TestUnion:
    """Test the union method."""

    def test_union_with_duplicate(self, letter_list, data_regression):
        union_list = letter_list.geetools.union(letter_list)
        data_regression.check(union_list.getInfo())

    def test_union_without_dupplicates(self, letter_list, int_list, data_regression):
        union_list = letter_list.geetools.union(int_list)
        data_regression.check(union_list.getInfo())


class TestDelete:
    """Test the delete method."""

    def test_delete(self, letter_list, data_regression):
        deleted_list = letter_list.geetools.delete(1)
        data_regression.check(deleted_list.getInfo())


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

    def test_replace_many(self, letter_list, data_regression):
        replaced_list = letter_list.geetools.replaceMany({"a": "foo", "c": "bar"})
        data_regression.check(replaced_list.getInfo())


class TestZip:
    """Test the zip method."""

    def test_zip(self, letter_list, data_regression):
        zipped_list = ee.List([letter_list, letter_list]).geetools.zip()
        data_regression.check(zipped_list.getInfo())


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
