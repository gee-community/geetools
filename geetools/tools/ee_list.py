# coding=utf-8
"""Tools for Earth Engine ee.List objects."""

import ee


def getFromDict(eelist, values):
    """Get a list of Dict's values from a list object. Keys must be unique.

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


def zip(eelist):
    """Zip a list of lists.

    Example:
        nested = ee.List([[1,2,3], [4,5,6], [7,8,9]])
        zipped = geetools.tools.ee_list.zip(nested)
        print(zipped.getInfo())
        >> [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
    """
    eelist = ee.List(eelist)
    first = ee.List(eelist.get(0))
    rest = ee.List(eelist).slice(1)

    def wrap(li, accum):
        accum = ee.List(accum)
        return accum.zip(li).map(lambda lr: ee.List(lr).flatten())

    return ee.List(rest.iterate(wrap, first))


def transpose(eelist):
    """Transpose a list of lists. Similar to ee.Array.transpose but using.

    ee.List. All inner lists must have the same size
    .
    """
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
