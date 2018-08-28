# coding=utf-8
""" Tools for Earth Engine ee.List objects """

import ee


class List(object):
    """ List class to hold ee.List methods """

    @staticmethod
    def replace_many(ee_list, replace):
        """ Replace many elements of a Earth Engine List object

            **EXAMPLE**

        .. code:: python

            list = ee.List(["one", "two", "three", 4])
            newlist = replace_many(list, {"one": 1, 4:"four"})

            print newlist.getInfo()

        >> [1, "two", "three", "four"]

        :param ee_list: list
        :type ee_list: ee.List
        :param replace: values to replace
        :type replace: dict
        :return: list with replaced values
        :rtype: ee.List
        """
        for key, val in replace.items():
            if val:
                ee_list = ee_list.replace(key, val)
        return ee_list

    @staticmethod
    def intersection(ee_list1, ee_list2):
        """ Find matching values. If ee_list1 has duplicated values that are
        present on ee_list2, all values from ee_list1 will apear in the result

        :param ee_list1: one Earth Engine List
        :param ee_list2: the other Earth Engine List
        :return: list with the intersection (matching values)
        :rtype: ee.List
        """
        newlist = ee.List([])
        def wrap(element, first):
            first = ee.List(first)

            return ee.Algorithms.If(ee_list2.contains(element),
                                    first.add(element), first)

        return ee.List(ee_list1.iterate(wrap, newlist))

    @staticmethod
    def difference(ee_list1, ee_list2):
        """ Difference between two earth engine lists

        :param ee_list1: one list
        :param ee_list2: the other list
        :return: list with the values of the difference
        :rtype: ee.List
        """
        return ee_list1.removeAll(ee_list2).add(ee_list2.removeAll(ee_list1))\
                       .flatten()

    @staticmethod
    def remove_duplicates(ee_list):
        """ Remove duplicated values from a EE list object """
        newlist = ee.List([])
        def wrap(element, init):
            init = ee.List(init)
            contained = init.contains(element)
            return ee.Algorithms.If(contained, init, init.add(element))
        return ee.List(ee_list.iterate(wrap, newlist))