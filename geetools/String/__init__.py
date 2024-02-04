"""Extra methods for the ``ee.String`` class."""
from __future__ import annotations

import ee

from geetools.accessors import register_class_accessor
from geetools.types import ee_dict, ee_str


@register_class_accessor(ee.String, "geetools")
class StringAccessor:
    """Toolbox for the ``ee.String`` class."""

    def __init__(self, obj: ee.String):
        """Initialize the String class."""
        self._obj = obj

    def eq(self, other: ee_str) -> ee.Number:
        """Compare two strings and return a ``ee.Number``.

        Parameters:
            other: The string to compare with.

        Returns:
            ``1`` if the strings are equal, ``0`` otherwise.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                s = ee.String("foo").geetools.eq("foo")
                s.getInfo()
        """
        return self._obj.compareTo(ee.String(other)).Not()

    def format(self, template: ee_dict) -> ee.String:
        """Format a string with a dictionary.

        Replace the keys in the string using the values provided in the dictionary. Follow the same pattern: value format as Python string.format method.

        Parameters:
            template: A dictionary with the values to replace.

        Returns:
            The formatted string.

        Examples:
            .. code-block:: python

                import ee, geetools

                ee.Initialize()

                s = ee.String("{greeting} {name} !").geetools.format({"greeting": "Hello", "name": "bob"})
                s.getInfo()
        """
        template = ee.Dictionary(template)
        templateList = template.keys().zip(template.values())

        def replace_format(kv, s):
            kv = ee.List(kv)
            key, value = ee.String(kv.get(0)), ee.String(kv.get(1))
            pattern = ee.String("{").cat(key).cat(ee.String("}"))
            return ee.String(s).replace(pattern, value)

        return templateList.iterate(replace_format, self._obj)
