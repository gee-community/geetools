""" subpackage holding modules with tools """

from . import imagecollection, date, dictionary, image, number, \
              segmentation, geometry, featurecollection, ee_list
from .image import Mapping


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