# coding=utf-8
"""Legacy Manager module for file management."""
import json
import os
from pathlib import Path

import ee
import ee.data
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.save instead")
def esave(eeobject, filename, path=Path.home()):
    """Saves any EE object to a file with extension .gee."""
    return eeobject.save(path / filename)


def eopen(file, path=None):
    """Opens a files saved with `esave` method.

    :return: the EE object
    """
    path = path if path else os.getcwd()

    try:
        with open(os.path.join(path, file), "r") as gee:
            thefile = json.load(gee)
    except IOError:
        with open(os.path.join(path, file + ".gee"), "r") as gee:
            thefile = json.load(gee)

    return ee.deserializer.decode(thefile)
