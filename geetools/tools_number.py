# coding=utf-8
""" Module holding tools for ee.Number """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


def trim_decimals(number, places=2):
    """ Decrease the number of decimals in a ee.Number

    :param places: number of decimal places to leave
    :return: a function to map over a list
    """
    factor = ee.Number(10).pow(ee.Number(places).toInt())

    floor = number.floor()
    decimals = number.subtract(floor)
    take = decimals.multiply(factor).toInt()
    newdecimals = take.toFloat().divide(factor)
    return floor.add(newdecimals).toFloat()
