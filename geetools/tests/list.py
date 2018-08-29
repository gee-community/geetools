# coding=utf-8
import unittest
import ee
from ..tools import List
ee.Initialize()


class TestList(unittest.TestCase):
    def setUp(self):
        self.list1 = List([1, 2, 3, 4, 5])
        self.list2 = List([4, 5, 6, 7])

    def test_list_intersection(self):
        intersection = self.list1.intersection(self.list2).getInfo()
        self.assertEqual(intersection, [4, 5])

    def test_list_difference(self):
        diff = self.list1.difference(self.list2).getInfo()
        self.assertEqual(diff, [1, 2, 3, 6, 7])

    def test_remove_duplicates(self):
        duplicated = List([1, 2, 2, 1, 3, 5])
        unique = duplicated.remove_duplicates().getInfo()
        self.assertEqual(unique, [1, 2, 3, 5])

    def test_replace_many(self):
        replaced = self.list1.replace_many({1:'test', 4:8}).getInfo()
        self.assertEqual(replaced, ['test', 2, 3, 8, 5])

    def test_get_from_dict(self):
        test_list = List(['a', 'c'])
        test_dict = ee.Dictionary({'a':1, 'b':5, 'c':8})

        values = test_list.get_from_dict(test_dict).getInfo()

        # assert
        self.assertEqual(values, [1, 8])

