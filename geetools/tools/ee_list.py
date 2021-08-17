# coding=utf-8
""" Tools for Earth Engine ee.List objects """

import ee
from . import computedobject


def difference(eelist, to_compare):
    """ Difference between two earth engine lists

    :param ee_list2: the other list
    :return: list with the values of the difference
    :rtype: ee.List
    """
    return eelist.removeAll(to_compare).add(to_compare.removeAll(eelist)) \
        .flatten()


def format(eelist):
    """ Convert a list to a string """
    def wrap(el, ini):
        ini = ee.String(ini)
        strel = ee.Algorithms.String(el)
        return ini.cat(',').cat(strel)

    liststr = ee.String(eelist.iterate(wrap, ''))
    return liststr.replace('^,', '[').cat(']')


def getFromDict(eelist, values):
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


def intersection(eelist, intersect):
    """ Find matching values. If ee_list1 has duplicated values that are
    present on ee_list2, all values from ee_list1 will apear in the result

    :param intersect: the other Earth Engine List
    :return: list with the intersection (matching values)
    :rtype: ee.List
    """
    eelist = ee.List(eelist)
    intersect = ee.List(intersect)
    newlist = ee.List([])
    def wrap(element, first):
        first = ee.List(first)

        return ee.Algorithms.If(intersect.contains(element),
                                first.add(element), first)

    return ee.List(eelist.iterate(wrap, newlist))


def removeDuplicates(eelist):
    """ Remove duplicated values from a EE list object """
    # TODO: See ee.List.distinct()
    newlist = ee.List([])
    def wrap(element, init):
        init = ee.List(init)
        contained = init.contains(element)
        return ee.Algorithms.If(contained, init, init.add(element))
    return ee.List(eelist.iterate(wrap, newlist))


def removeIndex(list, index):
    """ Remove an element by its index """
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


def replaceDict(eelist, to_replace):
    """ Replace many elements of a Earth Engine List object using a dictionary

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
    eelist = ee.List(eelist)
    to_replace = ee.Dictionary(to_replace)
    keys = to_replace.keys()
    def wrap(el):
        # Convert to String
        elstr = ee.Algorithms.String(el)
        condition = ee.List(keys).indexOf(elstr)
        return ee.Algorithms.If(condition.neq(-1), to_replace.get(elstr), el)
    return eelist.map(wrap)


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


def toString(eelist):
    """ Convert elements of a list into Strings. If the list contains other
    elements that are not strings or numbers, it will return the object type.
    For example, ['a', 1, ee.Image(0)] -> ['a', '1', 'Image']
    """
    eelist = ee.List(eelist)
    def wrap(el):
        def false(el):
            otype = ee.Algorithms.ObjectType(el)
            return ee.String(ee.Algorithms.If(computedobject.isNumber(el),
                                              ee.Number(el).format(),
                                              otype))

        return ee.String(ee.Algorithms.If(computedobject.isString(el), el, false(el)))

    return eelist.map(wrap)


def zip(eelist):
    """ Zip a list of lists.

    Example:
        nested = ee.List([[1,2,3], [4,5,6], [7,8,9]])
        zipped = geetools.tools.ee_list.zip(nested)
        print(zipped.getInfo())
        >> [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
    """
    eelist = ee.List(eelist)
    first = ee.List(eelist.get(0))
    rest = ee.List(eelist).slice(1)
    def wrap(l, accum):
        accum = ee.List(accum)
        return accum.zip(l).map(lambda l: ee.List(l).flatten())
    return ee.List(rest.iterate(wrap, first))


def transpose(eelist):
    """ Transpose a list of lists. Similar to ee.Array.transpose but using
    ee.List. All inner lists must have the same size """
    first = ee.List(eelist.get(0))
    size = first.size()
    result = ee.List.repeat(ee.List([]), size)
    indices = ee.List.sequence(0, size.subtract(1))

    def wrap(i, acc):
        i = ee.Number(i)
        acc = ee.List(acc)

        def wrap2(ll, accum):
            ll = ee.List(ll)
            accum = ee.List(accum)
            val = ll.get(i)
            toset = ee.List(accum.get(i))
            return accum.set(i, toset.add(val))

        return ee.List(eelist.iterate(wrap2, acc))

    return ee.List(indices.iterate(wrap, result))