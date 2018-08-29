# coding=utf-8
""" Tools for Earth Engine ee.List objects """

import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


class List(ee.ee_list.List):
    """ List class to hold ee.List methods """

    def __init__(self, *args, **kwargs):
        super(List, self).__init__(*args, **kwargs)

    def replace_many(self, replace):
        """ Replace many elements of a Earth Engine List object

            **EXAMPLE**

        .. code:: python

            list = ee.List(["one", "two", "three", 4])
            newlist = replace_many(list, {"one": 1, 4:"four"})

            print newlist.getInfo()

        >> [1, "two", "three", "four"]

        :param replace: values to replace
        :type replace: dict
        :return: list with replaced values
        :rtype: ee.List
        """
        new = self
        for key, val in replace.items():
            if val:
                new = new.replace(key, val)
        return new

    def intersection(self, intersect):
        """ Find matching values. If ee_list1 has duplicated values that are
        present on ee_list2, all values from ee_list1 will apear in the result

        :param intersect: the other Earth Engine List
        :return: list with the intersection (matching values)
        :rtype: ee.List
        """
        newlist = ee.List([])
        def wrap(element, first):
            first = ee.List(first)

            return ee.Algorithms.If(intersect.contains(element),
                                    first.add(element), first)

        return ee.List(self.iterate(wrap, newlist))

    def difference(self, ee_list):
        """ Difference between two earth engine lists

        :param ee_list2: the other list
        :return: list with the values of the difference
        :rtype: ee.List
        """
        return self.removeAll(ee_list).add(ee_list.removeAll(self)).flatten()

    def remove_duplicates(self):
        """ Remove duplicated values from a EE list object """
        newlist = ee.List([])
        def wrap(element, init):
            init = ee.List(init)
            contained = init.contains(element)
            return ee.Algorithms.If(contained, init, init.add(element))
        return ee.List(self.iterate(wrap, newlist))

    def get_from_dict(self, values):
        """ Get a list of Dict's values from a list object. Keys must be unique
    
        :param values: dict to get the values for list's keys
        :type values: ee.Dictionary
        :return: a list of values
        :rtype: ee.List
        """
        # self = ee.List(self) if isinstance(self, list) else self
        values = ee.Dictionary(values) if isinstance(values, dict) else values

        empty = ee.List([])

        def wrap(el, first):
            f = ee.List(first)
            cond = values.contains(el)
            return ee.Algorithms.If(cond, f.add(values.get(el)), f)

        values = ee.List(self.iterate(wrap, empty))
        return values
