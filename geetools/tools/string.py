# coding=utf-8
"""Tools for Earth Engine ee.List objects."""
import ee

from . import dictionary, ee_list


def format(string, replacement):
    """Format a string using variables (as str.format).

    You can format numbers
    using the pattern: `{var:format}` where format string must be according to
    the argument in function ee.Number.format, which is based on
    https://docs.oracle.com/javase/7/docs/api/java/util/Formatter.html.

    Example:
        string = ee.String('hello {nn:%.2f} {ll} {something} {else}')
        replacement = {'something': 'world', 'else': 'people',
                       'nn': 1.2555555654, 'pp': 'ignore'}

        formatted = geetools.tools.string.format(string, replacement)

        >
    """
    # casts
    replacement = ee.Dictionary(replacement)
    s = ee.String(string)
    # get keywords from string
    match = ee.String(string).match("{.*?}", "g")
    match = match.map(lambda s: ee.String(s).slice(1, -1))

    # get keywords from replacement
    keys = replacement.keys()

    def addFormat(st):
        st = ee.String(st)
        split = ee.List(st.split(":"))
        length = split.size()
        cond = length.eq(1)

        def true():
            return split.add("0")

        def false():
            split.set(0, st)
            return split

        return ee.List(ee.Algorithms.If(cond, true(), false()))

    formats = dictionary.fromList(match.map(addFormat))
    selection = ee_list.intersection(keys, formats.keys())

    # filter replacement by the intersection keywords
    repl = replacement.select(selection)
    keys = repl.keys()

    def formatValues(k, val):
        f = ee.String(formats.get(k))

        def true(v):
            return ee.Number(val).format(f)

        def false(v):
            return ee.Algorithms.String(v)

        cond = f.compareTo("0")  # returns 0 if equals
        return ee.String(ee.Algorithms.If(cond, true(val), false(val)))

    repl = repl.map(formatValues)
    values = repl.values()  # .map(lambda v: ee.Algorithms.String(v))
    # get a list of lists [key, value]
    # example: [['foo', 'foovar'], ['bar', 'barvar']]
    z = keys.zip(values)

    def wrap(kv, ini):
        keyval = ee.List(kv)
        ini = ee.String(ini)

        key = ee.String(keyval.get(0))
        value = ee.String(keyval.get(1))

        pattern = ee.String("{").cat(key).cat(ee.String(".*?}"))

        return ini.replace(pattern, value, "g")

    newstr = z.iterate(wrap, s)
    return ee.String(newstr)


def _zip(l1, l2):
    l1 = ee_list.toString(l1)
    l2 = ee_list.toString(l2)

    def wrap(el):
        el = ee.String(el)
        return l2.map(lambda e: el.cat(ee.String(e)))

    return l1.map(wrap).flatten()
