# coding=utf-8
""" Manager module for file managment """

import ee
import ee.data
import os
import json

if not ee.data._initialized:
    ee.Initialize()

def esave(eeobject, filename, path=None):
    """ Saves any EE object to a file with extension .gee

        The file has to be opened with `eopen`
    """
    obj = ee.serializer.encode(eeobject)

    path = path if path else os.getcwd()

    with open(os.path.join(path, filename+'.gee'), 'w') as js:
        json.dump(obj, js)

def eopen(file, path=None):
    """ Opens a files saved with `esave` method

    :return: the EE object """

    path = path if path else os.getcwd()

    try:
        with open(os.path.join(path, file), 'r') as gee:
            thefile = json.load(gee)
    except IOError:
        with open(os.path.join(path, file+'.gee'), 'r') as gee:
            thefile = json.load(gee)

    return ee.deserializer.decode(thefile)