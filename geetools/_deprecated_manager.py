# coding=utf-8
"""Legacy Manager module for file management."""
from pathlib import Path

import ee
import ee.data
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.save instead")
def esave(eeobject, filename, path=Path.home()):
    """Saves any EE object to a file with extension .gee."""
    return eeobject.save(path / filename)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.open instead")
def eopen(file, path=Path.home()):
    """Opens a files saved with `esave` method."""
    return ee.ComputedObject.open(path / file)
