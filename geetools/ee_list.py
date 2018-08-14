# coding=utf-8
""" Module holding tools for ee.List """

import ee


def replace_many(listEE, replace):
    """ Replace many elements of a Earth Engine List object

        **EXAMPLE**

    .. code:: python

        list = ee.List(["one", "two", "three", 4])
        newlist = replace_many(list, {"one": 1, 4:"four"})

        print newlist.getInfo()

    >> [1, "two", "three", "four"]

    :param listEE: list
    :type listEE: ee.List
    :param toreplace: values to replace
    :type toreplace: dict
    :return: list with replaced values
    :rtype: ee.List
    """
    for key, val in replace.items():
        if val:
            listEE = listEE.replace(key, val)
    return listEE


def intersection(listEE1, listEE2):
    """ Find matching values. If listEE1 has duplicated values that are present
    on listEE2, all values from listEE1 will apear in the result

    :param listEE1: one Earth Engine List
    :param listEE2: the other Earth Engine List
    :return: list with the intersection (matching values)
    :rtype: ee.List
    """
    newlist = ee.List([])
    def wrap(element, first):
        first = ee.List(first)

        return ee.Algorithms.If(listEE2.contains(element),
                                first.add(element), first)

    return ee.List(listEE1.iterate(wrap, newlist))


def difference(listEE1, listEE2):
    """ Difference between two earth engine lists

    :param listEE1: one list
    :param listEE2: the other list
    :return: list with the values of the difference
    :rtype: ee.List
    """
    return listEE1.removeAll(listEE2).add(listEE2.removeAll(listEE1)).flatten()


def remove_duplicates(listEE):
    """ Remove duplicated values from a EE list object """
    newlist = ee.List([])
    def wrap(element, init):
        init = ee.List(init)
        contained = init.contains(element)
        return ee.Algorithms.If(contained, init, init.add(element))
    return ee.List(listEE.iterate(wrap, newlist))


class List(ee.List):
    def __init__(self, **kwargs):
        super(List, self).__init__(**kwargs)

    def replace_many(self, replace):
        replace_many(self, replace)

    def intersection(self, list2):
        intersection(self, list2)

    def difference(self, list2):
        difference(self, list2)

    def remove_duplicates(self):
        remove_duplicates(self)