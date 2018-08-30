# coding=utf-8
import unittest
import ee
ee.Initialize()

from ..tools import ee_list as listools

class TestList(unittest.TestCase):
    def setUp(self):
        self.list1 = ee.List([1, 2, 3, 4, 5])
        self.list2 = ee.List([4, 5, 6, 7])

    def test_list_intersection(self):
        intersection = listools.intersection(self.list1, self.list2).getInfo()
        self.assertEqual(intersection, [4, 5])

    def test_list_difference(self):
        diff = listools.difference(self.list1, self.list2).getInfo()
        self.assertEqual(diff, [1, 2, 3, 6, 7])

    def test_remove_duplicates(self):
        duplicated = ee.List([1, 2, 2, 1, 3, 5])
        unique = listools.remove_duplicates(duplicated).getInfo()
        self.assertEqual(unique, [1, 2, 3, 5])

    def test_replace_many(self):
        replaced = listools.replace_many(self.list1, {1:'test', 4:8}).getInfo()
        self.assertEqual(replaced, ['test', 2, 3, 8, 5])

        # new test to match image's test
        newlist = ee.List(["B1", "B2", "B3", "B4", "B5", "B6", "B7",
                            "cfmask", "cfmask_conf"])
        self.assertEqual(
            listools.replace_many(newlist, {'B1':'BLUE', 'B2':'GREEN'}).getInfo(),
            ["BLUE", "GREEN", "B3", "B4", "B5", "B6", "B7",
             "cfmask", "cfmask_conf"])

    def test_get_from_dict(self):
        test_list = ee.List(['a', 'c'])
        test_dict = ee.Dictionary({'a':1, 'b':5, 'c':8})

        values = listools.get_from_dict(test_list, test_dict).getInfo()

        # assert
        self.assertEqual(values, [1, 8])
