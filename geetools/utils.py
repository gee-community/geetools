# coding=utf-8
""" Some util functions """

import pandas as pd
from copy import deepcopy
import ee


def getReducerName(reducer):
    """
    Get the name of the parsed reducer.

    WARNING: This function makes a request to EE Servers (getInfo). Do not use
    in server side functions (example: inside a mapping function)
    """
    reducer_type = reducer.getInfo()['type']

    relations = dict(
        mean=['Reducer.mean', 'Reducer.intervalMean'],
        median=['Reducer.median'],
        mode=['Reducer.mode'],
        first=['Reducer.first', 'Reducer.firstNonNull'],
        last=['Reducer.last', 'Reducer.lastNonNull'],
        stdDev=['Reducer.stdDev', 'Reducer.sampleStdDev'],
        all=['Reducer.allNoneZero'],
        any=['Reducer.anyNoneZero'],
        count=['Reducer.count', 'Reducer.countDistinct'],
        max=['Reducer.max'],
        min=['Reducer.min'],
        product=['Reducer.product'],
        variance=['Reducer.sampleVariance', 'Reducer.variance'],
        skew=['Reducer.skew'],
        sum=['Reducer.sum']
    )

    for name, options in relations.items():
        if reducer_type in options:
            return name


def reduceRegionsPandas(data, index='system:index', add_coordinates=False,
                        duplicate_index=False):
    """ Transform data coming from Image.reduceRegions to a pandas dataframe

    :param data: data coming from Image.reduceRegions
    :type data: ee.Dictionary or dict
    :param index: the index of the dataframe
    :param add_coordinates: if True adds the coordinates to the dataframe
    :param duplicate_index: if True adds the index data to the dataframe too
    :return: a pandas dataframe
    :rtype: pd.DataFrame
    """
    if not isinstance(data, dict):
        if add_coordinates:
            def addCentroid(feat):
                feat = ee.Feature(feat)
                centroid = feat.centroid().geometry()
                coords = ee.List(centroid.coordinates())
                return feat.set('longitude', ee.Number(coords.get(0)),
                                'latitude', ee.Number(coords.get(1)))
            data = data.map(addCentroid)

        data = data.getInfo()

    features = data['features']

    d, indexes = [], []
    for feature in features:
        nf = deepcopy(feature)
        props = nf['properties']

        if not duplicate_index:
            props.pop(index) if index in props else props

        d.append(props)
        if index == 'system:index':
            indexes.append(feature['id'])
        else:
            indexes.append(feature['properties'][index])

    return pd.DataFrame(d, indexes)