# -*- coding: utf-8 -*-
"""
This file contains a bunch of useful functions to use in Google Earth Engine
"""
import ee
ee.Initialize()


def mask2zero(img):
    """ Converts masked pixels into zeros

    :param img: Image contained in the Collection
    :type img: ee.Image
    """
    theMask = img.mask()
    return theMask.where(1, img)

def mask2number(col, number):
    """ Converts masked pixels into the specified number in each image of
    the collection. As *number* has to be a float, the resulting Image will
    have all bands converted to Float.

    :param col: Collection that contains the images to process
    :type col: ee.ImageCollection
    :param number: number to fill masked pixels
    :type number: float
    :return: the Collection containing all images converted
    """
    # TODO: let the user choose the type of the output
    value = ee.Image(number).toFloat()

    def mapping(img):
        mask = img.mask()
        test = mask.Not()
        return img.where(test, value)

    return col.map(mapping)
