# coding=utf-8
""" Module holding tools for creating composites """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


def Max(collection, qa_band):
    """ Simple composite with the highest values for the qa_band

    :type collection: ee.ImageCollection
    :param qa_band: quality band
    :type qa_band: str
    :return:
    """
    return collection.qualityMosaic(qa_band)
