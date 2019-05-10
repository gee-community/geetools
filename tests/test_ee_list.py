# coding=utf-8

from geetools.tools import ee_list
import ee
ee.Initialize()

list1 = ee.List([1, 2, 3, 4, 5])
list2 = ee.List([4, 5, 6, 7])


# helper
def assert_equal(obj, compare):
    assert obj.getInfo() == compare


def test_list_intersection():
    intersection = ee_list.intersection(list1, list2)
    assert_equal(intersection, [4, 5])


def test_list_difference():
    diff = ee_list.difference(list1, list2)
    assert_equal(diff, [1, 2, 3, 6, 7])


def test_remove_duplicates():
    duplicated = ee.List([1, 2, 2, 1, 3, 5])
    unique = ee_list.removeDuplicates(duplicated)
    assert_equal(unique, [1, 2, 3, 5])


def test_replace_many():
    replaced = ee_list.replaceDict(list1, {1: 'test', 4:8})
    assert_equal(replaced, ['test', 2, 3, 8, 5])

    # new test to match image's test
    newlist = ee.List(["B1", "B2", "B3", "B4", "B5", "B6", "B7",
                        "cfmask", "cfmask_conf"])
    replaced = ee_list.replaceDict(newlist, {'B1': 'BLUE', 'B2': 'GREEN'})
    assert_equal(replaced, ["BLUE", "GREEN", "B3", "B4", "B5", "B6", "B7",
                            "cfmask", "cfmask_conf"])


def test_get_from_dict():
    test_list = ee.List(['a', 'c'])
    test_dict = ee.Dictionary({'a':1, 'b':5, 'c':8})

    values = ee_list.getFromDict(test_list, test_dict)

    # assert
    assert_equal(values, [1, 8])

