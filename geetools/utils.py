# coding=utf-8
""" Some util functions """

import pandas as pd
from copy import deepcopy
import ee
from .tools import string


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


def castImage(value):
    """ Cast a value into an ee.Image if it is not already """
    if isinstance(value, ee.Image) or value is None:
        return value
    else:
        return ee.Image.constant(value)


def makeName(img, pattern, date_pattern=None, extra=None):
    """ Make a name with the given pattern. The pattern must contain the
    propeties to replace between curly braces. There are 2 special words:

    * 'system_date': replace with the date of the image formatted with
      `date_pattern`, which defaults to 'yyyyMMdd'
    * 'id' or 'ID': the image id. If None, it'll be replaced with 'id'

    Pattern example (supposing each image has a property called `city`):
    'image from {city} on {system_date}'

    You can add extra parameters using keyword `extra`
    """
    img = ee.Image(img)
    props = img.toDictionary()
    props = ee.Dictionary(ee.Algorithms.If(
        img.id(),
        props.set('id', img.id()).set('ID', img.id()),
        props))
    props = ee.Dictionary(ee.Algorithms.If(
        img.propertyNames().contains('system:time_start'),
        props.set('system_date', img.date().format(date_pattern)),
        props))
    if extra:
        extra = ee.Dictionary(extra)
        props = props.combine(extra)
    name = string.format(pattern, props)

    return name


def dict2namedtuple(thedict, name='NamedDict'):
    """ Create a namedtuple from a dict object. It handles nested dicts. If
    you want to scape this behaviour the dict must be placed into a list as its
    unique element """
    from collections import namedtuple

    thenametuple = namedtuple(name, [])

    for key, val in thedict.items():
        if not isinstance(key, str):
            msg = 'dict keys must be strings not {}'
            raise ValueError(msg.format(key.__class__))

        if not isinstance(val, dict):
            # workaround to include a dict as an attribute
            if isinstance(val, list):
                if isinstance(val[0], dict):
                    val = val[0]

            setattr(thenametuple, key, val)
        else:
            newname = dict2namedtuple(val, key)
            setattr(thenametuple, key, newname)

    return thenametuple


def formatVisParams(visParams):
    """ format visualization parameters to match EE requirements at
    ee.data.getMapId """
    formatted = dict()
    for param, value in visParams.items():
        if isinstance(value, list):
            value = [str(v) for v in value]
        if param in ['bands', 'palette']:
            formatted[param] = ','.join(value) if len(value) == 3 else str(value[0])
        if param in ['min', 'max', 'gain', 'bias', 'gamma']:
            formatted[param] = str(value) if isinstance(value, (int, str)) else ','.join(value)
    return formatted


def authenticate(credential_path):
    """ Authenticate to GEE with the specified credentials """
    from google.oauth2.credentials import Credentials
    import json
    def get_credentials():
        try:
            tokens = json.load(open(credential_path))
            refresh_token = tokens['refresh_token']
            return Credentials(
                None,
                refresh_token=refresh_token,
                token_uri=ee.oauth.TOKEN_URI,
                client_id=ee.oauth.CLIENT_ID,
                client_secret=ee.oauth.CLIENT_SECRET,
                scopes=ee.oauth.SCOPES)
        except IOError:
            raise ee.EEException(
                'Please authorize access to your Earth Engine account by '
                'running\n\nearthengine authenticate\n\nin your command line, and then '
                'retry.')

    credentials = get_credentials()
    ee.Initialize(credentials)
