# coding=utf-8
"""Legacy util functions."""
import ee
from deprecated.sphinx import deprecated


@deprecated(
    version="1.0.0",
    reason="The information is already in the object __name__ attribute",
)
def getReducerName(reducer):
    """Get the name of the parsed reducer."""
    return reducer.__name__.replace("Reducer.", "")


@deprecated(version="1.0.0", reason="Use geopandas instead")
def reduceRegionsPandas(data, index="system:index", add_coordinates=False, duplicate_index=False):
    """Transform data coming from Image.reduceRegions to a pandas dataframe."""
    raise NotImplementedError("Use geopandas.GeoDataFrame(data.getInfo()) instead")


@deprecated(version="1.0.0", reason="Use ee.Image(value) instead")
def castImage(value):
    """Cast a value into an ee.Image if it is not already."""
    return ee.Image(value)


@deprecated(version="1.0.0", reason="Use ee.Image.format instead")
def makeName(img, pattern, date_pattern=None, extra=None):
    """Make a name with the given pattern."""
    return ee.Image(img).geetools.format(pattern, date_pattern)


@deprecated(version="1.0.0", reason="Use ee.Image.isletMask instead")
def maskIslands(mask, limit, pixels_limit=1000):
    """Returns a new mask where connected pixels with less than 'limit'."""
    return ee.Image(mask).geetools.isletMask(limit)


@deprecated(version="1.0.0", reason="Use pure Python instead")
def dict2namedtuple(thedict, name="NamedDict"):
    """Create a namedtuple from a dict object. It handles nested dicts."""
    raise NotImplementedError("Use pure Python instead")


@deprecated(
    version="1.0.0",
    reason="Interactive methods have been moved to ipygee in version 0.5",
)
def formatVisParams(visParams):
    """Format visualization parameters."""
    raise NotImplementedError("Use ipygee instead")


@deprecated(
    version="1.0.0",
    reason="Interactive methods have been moved to ipygee in version 0.5",
)
def evaluate(obj, callback, args):
    """Retrieve eeobject value asynchronously. First argument of callback."""
    raise NotImplementedError("Use ipygee instead")
