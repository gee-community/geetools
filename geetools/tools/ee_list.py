# coding=utf-8
"""Tools for Earth Engine ee.List objects."""

import ee


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
