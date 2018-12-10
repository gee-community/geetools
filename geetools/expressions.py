# -*- coding: utf-8 -*-
""" Expression generator for Google Earth Engine """
from __future__ import print_function


class Expression(object):
    def __init__(self):
        pass

    @staticmethod
    def max(a, b):
        """ Generates the expression for max(a, b)

        :param a: one value. Can be a number or a variable
        :type a: str
        :param b: the other value
        :type b: str
        :return: max number
        :rtype: str
        """
        return "({a}>{b})?{a}:{b}".format(a= a, b= b)

    @staticmethod
    def min(a, b):
        """ Generates the expression for min(a, b)

        :param a: one value. Can be a number or a variable
        :type a: str
        :param b: the other value
        :type b: str
        :return: max number
        :rtype: str
        """
        return "({a}>{b})?{b}:{a}".format(a= a, b= b)