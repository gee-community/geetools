# coding=utf-8
"""ee.Array helpers."""
import ee


def set2DValue(array, position, value):
    """Set the x and y values in a 2-D array."""
    xpos = ee.Number(ee.List(position).get(0))
    ypos = ee.Number(ee.List(position).get(1))

    value = ee.Number(value)

    alist = ee.Array(array).toList()
    row = ee.List(alist.get(ypos))
    newrow = row.set(xpos, value)

    newlist = alist.set(ypos, newrow)

    return ee.Array(newlist)
