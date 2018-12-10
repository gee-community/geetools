# coding=utf-8
""" Tools for Earth Engine ee.List objects """

import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


def replace_many(eelist, to_replace):
    """ Replace many elements of a Earth Engine List object

        **EXAMPLE**

    .. code:: python

        list = ee.List(["one", "two", "three", 4])
        newlist = replace_many(list, {"one": 1, 4:"four"})

        print newlist.getInfo()

    >> [1, "two", "three", "four"]

    :param to_replace: values to replace
    :type to_replace: dict
    :return: list with replaced values
    :rtype: ee.List
    """
    for key, val in to_replace.items():
        if val:
            eelist = eelist.replace(key, val)
    return eelist


def intersection(eelist, intersect):
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

    return ee.List(eelist.iterate(wrap, newlist))


def difference(eelist, to_compare):
    """ Difference between two earth engine lists

    :param ee_list2: the other list
    :return: list with the values of the difference
    :rtype: ee.List
    """
    return eelist.removeAll(to_compare).add(to_compare.removeAll(eelist)) \
        .flatten()


def remove_duplicates(eelist):
    """ Remove duplicated values from a EE list object """
    newlist = ee.List([])
    def wrap(element, init):
        init = ee.List(init)
        contained = init.contains(element)
        return ee.Algorithms.If(contained, init, init.add(element))
    return ee.List(eelist.iterate(wrap, newlist))


def get_from_dict(eelist, values):
    """ Get a list of Dict's values from a list object. Keys must be unique

    :param values: dict to get the values for list's keys
    :type values: ee.Dictionary
    :return: a list of values
    :rtype: ee.List
    """
    values = ee.Dictionary(values) if isinstance(values, dict) else values

    empty = ee.List([])

    def wrap(el, first):
        f = ee.List(first)
        cond = values.contains(el)
        return ee.Algorithms.If(cond, f.add(values.get(el)), f)

    values = ee.List(eelist.iterate(wrap, empty))
    return values


def sequence(ini, end, step=1):
    """ Create a sequence from ini to end by step. Similar to
    ee.List.sequence, but if end != last item then adds the end to the end
    of the resuting list
    """
    end = ee.Number(end)
    if step == 0:
        step = 1
    amplitude = end.subtract(ini)
    mod = ee.Number(amplitude).mod(step)
    seq = ee.List.sequence(ini, end, step)
    condition = mod.neq(0)
    final = ee.Algorithms.If(condition, seq.add(end), seq)
    return ee.List(final)


def removeIndex(list, index):
    list = ee.List(list)
    index = ee.Number(index)
    size = list.size()

    def allowed():
        def zerof(list):
            return list.slice(1, list.size())

        def rest(list, index):
            list = ee.List(list)
            index = ee.Number(index)
            last = index.eq(list.size())

            def lastf(list):
                return list.slice(0, list.size().subtract(1))

            def restf(list, index):
                list = ee.List(list)
                index = ee.Number(index)
                first = list.slice(0, index)
                return first.cat(list.slice(index.add(1), list.size()))

            return ee.List(ee.Algorithms.If(last, lastf(list), restf(list, index)))

        return ee.List(ee.Algorithms.If(index, rest(list, index), zerof(list)))

    condition = index.gte(size).Or(index.lt(0))

    return ee.List(ee.Algorithms.If(condition, -1, allowed()))
