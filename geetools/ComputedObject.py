"""Extra tools for the ``ee.ComputedObject`` class."""
from __future__ import annotations

from typing import Type

import ee


def _extend(cls):
    """Extends the cls class.

    This is only used on the ``ComputedObject`` as it's the parent class of all.
    Using the regular accessor would lead to a duplicate member and undesired behavior.

    Parameters:
        cls: Class to extend.

    Returns:
        Decorator for extending classes.
    """
    return lambda f: (setattr(cls, f.__name__, f) or f)


@_extend(ee.ComputedObject)
def isInstance(self, klass: Type) -> ee.Number:
    """Return 1 if the element is the passed type or 0 if not.

    Parameters:
        klass: The class to check the instance of.

    Returns:
        ``1`` if the element is the passed type or ``0`` if not.

    Examples:
        .. jupyter-execute::

            import ee, geetools

            ee.Initialize()

            s = ee.String("foo").geetools.isInstance(ee.String)
            s.getInfo()
    """
    return ee.Algorithms.ObjectType(self).compareTo(klass.__name__).eq(0)
