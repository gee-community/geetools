"""Module holding tools for creating composites."""

import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.5.0", reason="Only used to build the medoid composite.")
def medoidScore(collection, bands=None, discard_zeros=False, bandname="sumdist", normalize=True):
    """Compute a score to reflect 'how far' is from the medoid."""
    raise NotImplementedError(
        "This method was only used to build the medoid composite. "
        "The medoid composite is still available in the lib."
    )


@deprecated(version="1.5.0", reason="Use ee.imageCollection.geetools.medoid instead")
def medoid(collection, bands=None, discard_zeros=False):
    """Medoid Composite. Adapted from https://www.mdpi.com/2072-4292/5/12/6481."""
    return ee.ImageCollection(collection).geetools.medoid()


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.closestDate instead")
def closestDate(col, clip_to_first=False):
    """Make a composite in which masked pixels are filled with the last available pixel."""
    return ee.ImageCollection(col).geetools.closestDate()


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead")
def compositeRegularIntervals(
    collection,
    interval=1,
    unit="month",
    date_range=(1, 0),
    date_range_unit="month",
    direction="backward",
    start=None,
    end=None,
    composite_function=None,
    composite_args=None,
    composite_kwargs=None,
):
    """Make a composite at regular intervals parsing a composite."""
    return ee.ImageCollection(collection).geetools.reduceInterval(unit=unit)


@deprecated(version="1.5.0", reason="Use ee.ImageCollection.geetools.reduceInterval instead")
def compositeByMonth(
    collection, composite_function=None, composite_args=None, composite_kwargs=None
):
    """Make a composite at regular intervals parsing a composite."""
    return ee.ImageCollection(collection).geetools.reduceInterval(unit="month")


@deprecated(version="1.4.0", reason="Use the vanilla Earth Engine API")
def max(collection, band=None):
    """Make a max composite using the specified band."""
    return collection.max()
