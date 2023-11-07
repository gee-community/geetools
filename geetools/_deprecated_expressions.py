# -*- coding: utf-8 -*-
"""Expression generator for Google Earth Engine."""
from deprecated.sphinx import deprecated


class Expression:
    @deprecated(version="1.0.0", reason="Use pure python string instead")
    @staticmethod
    def max(a, b):
        """Generates the expression for max between a and b."""
        return "({a}>{b})?{a}:{b}".format(a=a, b=b)

    @deprecated(version="1.0.0", reason="Use pure python string instead")
    @staticmethod
    def min(a, b):
        """Generates the expression for min between a and b."""
        return "({a}>{b})?{b}:{a}".format(a=a, b=b)
