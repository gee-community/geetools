"""Extra methods for the :py:class:`ee.String` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.String, "geetools")
class StringAccessor:
    """Toolbox for the :py:class:`ee.String` class."""

    def __init__(self, obj: ee.String):
        """Initialize the String class."""
        self._obj = obj

    def eq(self, other: str | ee.String) -> ee.Number:
        """Compare two strings and return a ``ee.Number``.

        Parameters:
            other: The string to compare with.

        Returns:
            ``1`` if the strings are equal, ``0`` otherwise.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                isEqual = ee.String("foo").geetools.eq("foo")
                isEqual.getInfo()
        """
        return self._obj.compareTo(ee.String(other)).Not()

    def format(self, template: dict | ee.Dictionary) -> ee.String:
        """Format a string with a dictionary.

        Replace the keys in the string using the values provided in the dictionary. Follow the same pattern: value format as Python string.format method.

        Parameters:
            template: A dictionary with the values to replace.

        Returns:
            The formatted string.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                s = ee.String("{greeting} {name} !")
                s = s.geetools.format({"greeting": "Hello", "name": "bob"})
                s.getInfo()
        """
        template = ee.Dictionary(template)
        templateList = template.keys().zip(template.values())

        def replace_format(kv, s):
            kv = ee.List(kv)
            key, value = ee.String(kv.get(0)), ee.String(kv.get(1))
            pattern = ee.String("{").cat(key).cat(ee.String("}"))
            return ee.String(s).replace(pattern, value)

        return ee.String(templateList.iterate(replace_format, self._obj))
