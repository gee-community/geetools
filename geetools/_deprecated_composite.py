"""Module holding tools for creating composites."""

import ee
from deprecated.sphinx import deprecated

from . import _deprecated_algorithms, tools


def medoidScore(collection, bands=None, discard_zeros=False, bandname="sumdist", normalize=True):
    """Compute a score to reflect 'how far' is from the medoid.

    Same params
    as medoid()
    .
    """
    first_image = ee.Image(collection.first())
    if not bands:
        bands = first_image.bandNames()

    # Create a unique id property called 'enumeration'
    enumerated = tools.imagecollection.enumerateProperty(collection)
    collist = enumerated.toList(enumerated.size())

    def over_list(im):
        im = ee.Image(im)
        n = ee.Number(im.get("enumeration"))

        # Remove the current image from the collection
        filtered = tools.ee_list.removeIndex(collist, n)

        # Select bands for medoid
        to_process = im.select(bands)

        def over_collist(img):
            return ee.Image(img).select(bands)

        filtered = filtered.map(over_collist)

        # Compute the sum of the euclidean distance between the current image
        # and every image in the rest of the collection
        dist = _deprecated_algorithms.sumDistance(
            to_process, filtered, name=bandname, discard_zeros=discard_zeros
        )

        # Mask zero values
        if not normalize:
            # multiply by -1 to get the lowest value in the qualityMosaic
            dist = dist.multiply(-1)

        return im.addBands(dist)

    imlist = ee.List(collist.map(over_list))

    medcol = ee.ImageCollection.fromImages(imlist)

    # Normalize result to be between 0 and 1
    if normalize:
        min_sumdist = ee.Image(medcol.select(bandname).min()).rename("min_sumdist")
        max_sumdist = ee.Image(medcol.select(bandname).max()).rename("max_sumdist")

        def to_normalize(img):
            sumdist = img.select(bandname)
            newband = (
                ee.Image()
                .expression(
                    "1-((val-min)/(max-min))",
                    {"val": sumdist, "min": min_sumdist, "max": max_sumdist},
                )
                .rename(bandname)
            )
            return tools.image.replace(img, bandname, newband)

        medcol = medcol.map(to_normalize)

    return medcol


def medoid(collection, bands=None, discard_zeros=False):
    """Medoid Composite. Adapted from https://www.mdpi.com/2072-4292/5/12/6481.

    :param collection: the collection to composite
    :type collection: ee.ImageCollection
    :param bands: the bands to use for computation. The composite will include
        all bands
    :type bands: list
    :param discard_zeros: Masked and pixels with value zero will not be use
        for computation. Improves dark zones.
    :type discard_zeros: bool
    :return: the Medoid Composite
    :rtype: ee.Image
    """
    medcol = medoidScore(collection, bands, discard_zeros)
    comp = medcol.qualityMosaic("sumdist")
    final = tools.image.removeBands(comp, ["sumdist", "mask"])
    return final


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
