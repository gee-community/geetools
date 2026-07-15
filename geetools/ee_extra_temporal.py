"""Temporal utilities for Earth Engine ImageCollections."""

from typing import Literal, TypeVar, Union

import ee

ImageCollectionLike = TypeVar("ImageCollectionLike", bound=ee.ImageCollection)

TimeUnit = Literal["year", "month", "week", "day", "hour", "minute", "second"]

# Time unit conversion to days
UNIT_CONVERSION = {
    "year": 365,
    "month": 30,
    "week": 7,
    "day": 1,
    "hour": 1 / 24,
    "minute": 1 / (24 * 60),
    "second": 1 / (24 * 3600),
}


def closest(
    collection: ee.ImageCollection,
    date: Union[ee.Date, str],
    tolerance: int = 1,
    unit: TimeUnit = "month",
) -> ee.ImageCollection:
    """Get the closest image(s) to a specified date in an ImageCollection.

    Finds the image(s) in the collection that are closest to the specified date,
    optionally within a tolerance window.

    Parameters:
        collection: ImageCollection to search.
        date: Target date to find closest image(s) to.
        tolerance: Size of time window to search within (before filtering for closest).
        unit: Time unit for tolerance. One of: 'year', 'month', 'week', 'day',
              'hour', 'minute', 'second'.

    Returns:
        ImageCollection containing the closest image(s) to the specified date.

    Examples:
        >>> import ee
        >>> import geetools
        >>> ee.Initialize()
        >>> geom = ee.Geometry.point(-122.196, 41.411)
        >>> s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        >>> closest = geetools.ee_image_collection.closest(
        ...     s2.filterBounds(geom),
        ...     date='2020-10-15',
        ...     tolerance=1,
        ...     unit='month'
        ... )
    """
    if isinstance(date, str):
        date = ee.Date(date)

    # Convert tolerance to days
    tolerance_days = tolerance * UNIT_CONVERSION.get(unit, 30)

    # Filter to tolerance window
    start_date = date.advance(-tolerance_days, "day")
    end_date = date.advance(tolerance_days, "day")
    filtered = collection.filterDate(start_date, end_date)

    # Calculate absolute difference from target date for each image
    def add_date_diff(img: ee.Image) -> ee.Image:
        """Calculate days from target date."""
        img_date = ee.Image(img).date()
        diff = img_date.difference(date, "day").abs()
        return img.set("date_diff", diff)

    with_diff = filtered.map(add_date_diff)

    # Find minimum difference
    min_diff = with_diff.reduceColumns(ee.Reducer.min(), ["date_diff"]).get("min")

    # Filter to images with minimum difference
    closest_images = with_diff.filter(ee.Filter.eq("date_diff", min_diff))

    return closest_images
