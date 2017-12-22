# !/usr/bin/env python
# coding=utf-8

import tools
import ee

# MODIS
def modis(img):
    """ Function to use in MODIS Collection

    Use:

    `masked = collection.map(cloud_mask.modis)`
    """
    cmask = img.select("state_1km")
    cloud = tools.compute_bits(cmask, 1, 1, "cloud")
    mix = tools.compute_bits(cmask, 0, 0, "mix")
    shadow = tools.compute_bits(cmask, 2, 2, "shadow")
    cloud2 = tools.compute_bits(cmask, 10, 10, "cloud2")
    snow = tools.compute_bits(cmask, 11, 11, "snow")

    mask = cloud.Or(mix).Or(shadow).Or(cloud2).Or(snow)

    return img.updateMask(mask.Not())

# SENTINEL 2
def sentinel2(image):
    """ Function to use in SENTINEL2 Collection

    Use:

    `masked = collection.map(cloud_mask.sentinel2)`
    """
    nubes = image.select("QA60")
    opaque = tools.compute_bits(nubes, 10, 10, "opaque")
    cirrus = tools.compute_bits(nubes, 11, 11, "cirrus")
    mask = opaque.Or(cirrus)
    result = image.updateMask(mask.Not())
    return result

# LEDAPS
def ledaps(image):
    """ Function to use in Surface Reflectance Collections computed by
    LEDAPS

    Use:

    `masked = collection.map(cloud_mask.ledaps)`
    """
    cmask = image.select('QA')

    valid_data_mask = tools.compute_bits(cmask, 1, 1, 'valid_data')
    cloud_mask = tools.compute_bits(cmask, 2, 2, 'cloud')
    snow_mask = tools.compute_bits(cmask, 4, 4, 'snow')

    good_pix = cloud_mask.eq(0).And(valid_data_mask.eq(0)).And(snow_mask.eq(0))
    result = image.updateMask(good_pix)

    return result

# FMASK
def fmask(bandname="fmask"):
    """ Function to use in Collections that have a quality band computed with
    fmask algorithm

    The use of this function is a little different from the other because it
    is a function that returns a function, so you must call it to return the
    function to use in map:

    `masked = collection.map(cloud_mask.fmask())`

    :param bandname: name of the band that holds the fmask information
    :type bandname: str
    :return: a function to use in map
    :rtype: function
    """

    def fmask(image):
        imgFmask = image.select(bandname)
        shadow = imgFmask.eq(3)
        snow = imgFmask.eq(4)
        cloud = imgFmask.eq(5)

        mask = shadow.Or(snow).Or(cloud)

        imgMask = image.updateMask(mask.Not())
        return imgMask
    return fmask

def usgs(image):
    """ Function to use in Surface Reflectance Collections computed by USGS

    Use:

    `masked = collection.map(cloud_mask.usgs)`
    """
    image = fmask("cfmask")(image)
    cloud = image.select("sr_cloud_qa").neq(255)
    shad = image.select("sr_cloud_shadow_qa").neq(255)
    return image.updateMask(cloud).updateMask(shad)

def cfmask_bits(image):
    """ Function to use in new Surface Reflectance Collections assets.
    LANDSAT/LT04/C01/T1_SR, LANDSAT/LT05/C01/T1_SR, LANDSAT/LE07/C01/T1_SR,
    LANDSAT/LC08/C01/T1_SR

    Use:

    `masked = collection.map(cloud_mask.cfmask_bits)`
    """
    bands = image.bandNames()
    contains_sr = bands.contains('sr_cloud_qa')

    def sr():
        mask = image.select('sr_cloud_qa')
        cloud_mask = tools.compute_bits(mask, 1, 1, 'cloud')
        shadow_mask = tools.compute_bits(mask, 2, 2, 'shadow')
        adjacent_mask = tools.compute_bits(mask, 3, 3, 'adjacent')
        snow_mask = tools.compute_bits(mask, 4, 4, 'snow')

        good_pix = cloud_mask.eq(0).And(shadow_mask.eq(0)).And(snow_mask.eq(0)).And(adjacent_mask.eq(0))
        return good_pix

    def pix():
        mask = image.select('pixel_qa')
        cloud_mask = tools.compute_bits(mask, 5, 5, 'cloud')
        shadow_mask = tools.compute_bits(mask, 3, 3, 'shadow')
        snow_mask = tools.compute_bits(mask, 4, 4, 'snow')

        good_pix = cloud_mask.eq(0).And(shadow_mask.eq(0)).And(snow_mask.eq(0))
        return good_pix

    good_pix = ee.Algorithms.If(contains_sr, sr(), pix())

    result = image.updateMask(good_pix)

    return result