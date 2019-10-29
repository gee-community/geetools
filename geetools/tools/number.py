# coding=utf-8
""" Module holding tools for ee.Number """
import ee
import ee.data


def trimDecimals(number, places=2):
    """ Decrease the number of decimals in a ee.Number

    :param places: number of decimal places to leave
    :return: a function to map over a list
    """
    factor = ee.Number(10).pow(ee.Number(places).toInt())

    return number.multiply(factor).toInt().divide(factor)
