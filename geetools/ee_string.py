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

        Numbers and Dates can be formatted using formatters:
         - ee.Number
           - formatters: https://developers.google.com/earth-engine/apidocs/ee-number-format.
           - how to: %{formatter}
           - example: "%.2f" (converts 3.1415 -> 3.14)
         - ee.Date
           - formatters: https://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html
           - how to: %t{formatter}
           - example: "%tyyyy-MM-dd" (converts 1577836800000 -> 2020-01-01)
           - Dates in the template can be
             - ee.Date -> ee.Date('2020-01-01')
             - ee.Number (milliseconds) -> 1577836800000
             - ee.String -> "2020-01-01"

        Parameters:
            template: A dictionary with the values to replace.

        Returns:
            The formatted string.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                s = ee.String("{greeting} developer, pi={number%.2f} start={start%tyyyy-MM-dd} end={end%tdd MMM yyyy}")
                s = s.geetools.format({"greeting": "Hello", "number": 3.1415, "start": 1577836800000, "end": "2021-01-01"})
                s.getInfo()
        """
        template = ee.Dictionary(template)
        template.keys().zip(template.values())

        toFormat = self._obj.match("\\{([^\\}]+)\\}", "g")

        def replace_format(string, init):
            clean = ee.String(string).slice(1, -1)
            parts = clean.split("%")
            keys = ee.List.sequence(1, parts.size()).map(lambda k: ee.Number(k).toInt().format())
            rel = ee.Dictionary.fromLists(keys, parts)
            key = ee.String(rel.get("1"))
            value = template.get(key, "")
            format = ee.String(rel.get("2", ""))
            is_date = format.match("^t.+").size().gt(0)
            is_number = parts.size().eq(2).And(is_date.Not())
            formatted = ee.String(
                ee.Algorithms.If(
                    is_number,
                    ee.Number(value).format(ee.String("%").cat(format)),
                    ee.Algorithms.If(is_date, ee.Date(value).format(format.slice(1)), value),
                )
            )
            return ee.String(init).replace(string, formatted)

        return ee.String(toFormat.iterate(replace_format, self._obj))
