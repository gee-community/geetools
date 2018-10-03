# coding=utf-8
""" Module holding tools for creating composites """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()

from . import today
from . import tools


def highest_qa(collection, qa_band):
    """ Simple composite with the highest values for the qa_band

    :type collection: ee.ImageCollection
    :param qa_band: quality band
    :type qa_band: str
    :return:
    """
    return collection.qualityMosaic(qa_band)


def closest_date(collection, target_date, mask_band=None, property_name=None,
                 clip_to_first=False, limit=50):
    """ Get the image closest to the given date, and fill masked values in
    that image with values from the closest date. Images must be already
    masked. Use parameter `limit` for better speed

    :param collection: the collection with masked images
    :type collection: ee.ImageCollection
    :param target_date: the target date
    :type target_date: ee.Date or str or int
    :param mask_band: the name of the band that holds the band. CAUTION: all
        bands will be masked with this mask to avoid mixing pixels from
        different images. If None, it'll use the first band
    :type mask_band: str
    :param limit: number of image to use. Too many can throw an error, and few
        many can leave 'holes' (masked pixels)
    :type limit: int
    :param clip_to_first: if True, the resulting composite will be clipped to
        the first image footprint. Defaults to False
    :type clip_to_first: bool
    :param property_name: name of the property that will hold the 'closeness'
        to the central image (closest to passed date)
    :type property_name: str
    """
    # HELPER
    def get_mask(img):
        """ Get a mask whether the passed image is already a mask or is a
        masked image """
        unmasked = img.unmask()
        return unmasked.divide(unmasked)

    if not mask_band:
        mask_band = ee.String(ee.Image(collection.first()).bandNames().get(0))

    if not property_name:
        property_name = 'diff_with_target_date'

    # target date
    date = ee.Date(target_date)

    # order collection
    new = collection.sort('system:time_start', True)

    # add date band
    def add_date(img):
        date_band = tools.date.get_date_band(img)
        return img.addBands(date_band)
    new = new.map(add_date)

    # assign difference to target date to each image and order the collection
    # according
    def set_diff_f(img):
        d = ee.Image(img).date()
        diff = d.difference(date, 'day').abs()
        return img.set(property_name, ee.Number(diff))

    set_diff = new.map(set_diff_f)
    ordered = set_diff.sort(property_name).limit(limit)
    ordered_list = ordered.toList(ordered.size())

    # the first image is the closest to the target date
    closest = ee.Image(ordered_list.get(0))
    rest = ee.ImageCollection(ordered_list.slice(1))

    footprint = closest.get('system:footprint')

    def fill(img, ini):
        ini = ee.Image(ini)
        # mask both ini and img
        mask_ini = get_mask(ini.select(mask_band))
        masked_ini = ini.updateMask(mask_ini)

        img = ee.Image(img)
        mask_img = get_mask(img.select(mask_band))
        masked_img = img.updateMask(mask_img)

        # mask match pixels (in ini and img)
        mask_ini_not = mask_ini.Not()
        img_not = masked_img.updateMask(mask_ini_not)

        # make masked values = 0
        zero_ini = masked_ini.unmask()
        zero_img = img_not.unmask()

        # add images
        added = zero_img.add(zero_ini)

        # update mask
        new_mask = mask_ini.add(img_not.mask())

        # final result
        if clip_to_first:
            return added.updateMask(new_mask).clip(footprint)
        else:
            return added.updateMask(new_mask)

    return ee.Image(rest.iterate(fill, closest))
