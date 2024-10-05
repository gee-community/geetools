# coding=utf-8
"""legacy Module holding tools for ee.ImageCollections."""
import ee
from deprecated.sphinx import deprecated

import geetools  # noqa: F401


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.closestDate instead.")
def fillWithLast(collection, reverse=False, proxy=-999):
    """Fill each masked pixels with the last available not masked pixel."""
    return ee.ImageCollection(collection).geetools.closestDate()


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead.")
def mosaicSameDay(collection, qualityBand=""):
    """Return a collection where images from the same day are mosaicked."""
    reducer = "mosaic" if qualityBand == "" else "qualityMosaic"
    return ee.ImageCollection(collection).geetools.reduceInterval(reducer, "day", 1, qualityBand)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead.")
def reduceEqualInterval(
    collection, interval=30, unit="day", reducer=None, start_date=None, end_date=None
):
    """Reduce an ImageCollection into a new one that has one image per reduced interval."""
    return ee.ImageCollection(collection).geetools.reduceInterval(reducer, unit, interval)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.groupInterval instead.")
def makeEqualInterval(collection, interval=1, unit="month"):
    """Make a list of image collections filtered by the given interval."""
    return ee.ImageCollection(collection).geetools.groupInterval(unit, interval)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.groupInterval instead..")
def makeDayIntervals(collection, interval=30, reverse=False, buffer="second"):
    """Make day intervals."""
    return ee.ImageCollection(collection).geetools.groupInterval("day", 1)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead.")
def reduceDayIntervals(collection, reducer, interval=30, reverse=False, buffer="second"):
    """Reduce Day Intervals."""
    return ee.ImageCollection(collection).geetools.reduceInterval(reducer, "day", 1)


@deprecated(version="1.4.0", reason="Removed from the lib as untested")
def linearFunctionBand(*args, **kwargs):
    """Apply a linear function over the bands across every image of the ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested")
def linearFunctionProperty(*args, **kwargs):
    """Apply a linear function over the properties across every image of the ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def linearInterpolation(collection, date_property="system:time_start"):
    """TODO missing docstring."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def gaussFunctionBand(*args, **kwargs):
    """Compute a Gauss function using a specified band over an ImageCollection, See: https://en.wikipedia.org/wiki/Gaussian_function."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def gaussFunctionProperty(*args, **kwargs):
    """Compute a Gauss function using a specified property over an ImageCollection."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def normalDistributionProperty(*args, **kwargs):
    """Compute a normal distribution using a specified property, over an ImageCollection"""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.4.0", reason="Removed from the lib as untested.")
def normalDistributionBand(collection, band, mean=None, std=None, name="normal_distribution"):
    """Compute a normal distribution using a specified band, over an ImageCollection."""
    raise NotImplementedError(
        "As it was vastly untested this method has been removed from the lib."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )


@deprecated(version="1.5.0", reason="The output format is unclear.")
def moving_average(collection, back=5, reducer=None, use_original=True):
    """Compute the moving average over a time series."""
    raise NotImplementedError(
        "This method has been deprecated as the output format is unclear."
        "If a real use case for this method can be provided, please open an issue and we'll reimplement it."
    )
