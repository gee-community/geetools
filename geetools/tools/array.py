# coding=utf-8
""" ee.Array helpers """
import ee


def constant2DArray(width, height, value):
    """Create an array of width x height with a fixed value"""
    cols = ee.List.repeat(value, height)
    rows = ee.List.repeat(value, width)
    return ee.Array(cols.map(lambda n: rows))


def set2DValue(array, position, value):
    """set the x and y values in a 2-D array"""
    xpos = ee.Number(ee.List(position).get(0))
    ypos = ee.Number(ee.List(position).get(1))

    value = ee.Number(value)

    alist = ee.Array(array).toList()
    row = ee.List(alist.get(ypos))
    newrow = row.set(xpos, value)

    newlist = alist.set(ypos, newrow)

    return ee.Array(newlist)
