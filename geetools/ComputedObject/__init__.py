"""Extra tools for the ``ee.ComputedObject`` class."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Type

import ee

from geetools.accessors import _register_extention
from geetools.types import pathlike


# -- types management ----------------------------------------------------------
@_register_extention(ee.ComputedObject)
def isInstance(self, klass: Type) -> ee.Number:
    """Return 1 if the element is the passed type or 0 if not.

    Parameters:
        klass: The class to check the instance of.

    Returns:
        ``1`` if the element is the passed type or ``0`` if not.

    Examples:
        .. code-block:: python

            import ee, geetools

            ee.Initialize()

            s = ee.String("foo").isInstance(ee.String)
            s.getInfo()
    """
    return ee.Algorithms.ObjectType(self).compareTo(klass.__name__).eq(0)


# -- .gee files ----------------------------------------------------------------
@_register_extention(ee.ComputedObject)  # type: ignore
def save(self, path: pathlike) -> Path:
    """Save a ``ComputedObject`` to a .gee file.

    The file contains the JSON representation of the object. it still need to be computed via ``getInfo()`` to be used.

    Parameters:
        path: The path to save the object to.

    Returns:
        The path to the saved file.

    Examples:
        .. code-block:: python

            import ee, geetools
            from tempfile import TemporaryDirectory
            from pathlib import Path

            ee.Initialize()

            img = ee.Image("COPERNICUS/S2/20151128T112653_20151128T135750_T29SND")
            with TemporaryDirectory() as tmp:
                file = Path(tmp) / "test.gee"
                img.geetools.save(file)
                print(file.readText())
    """
    path = Path(path).with_suffix(".gee")
    path.write_text(json.dumps(ee.serializer.encode(self)))
    return path


@staticmethod  # type: ignore
@_register_extention(ee.ComputedObject)  # type: ignore
def open(path: pathlike) -> ee.ComputedObject:
    """Open a .gee file as a ComputedObject.

    Parameters:
        path: The path to the file to open.

    Returns:
        The ComputedObject instance.

    Examples:
        .. code-block:: python

            import ee, geetools
            from tempfile import TemporaryDirectory
            from pathlib import Path

            ee.Initialize()

            img = ee.Image("COPERNICUS/S2/20151128T112653_20151128T135750_T29SND")
            with TemporaryDirectory() as tmp:
                file = Path(tmp) / "test.gee"
                img.geetools.save(file)
                obj = ee.Image.open(file)
                print(obj)
    """
    if (path := Path(path)).suffix != ".gee":
        raise ValueError("File must be a .gee file")

    return ee.deserializer.decode(json.loads(path.read_text()))


# placeholder classes for the isInstance method --------------------------------
@_register_extention(ee)
class Float:
    """Placeholder Float class to be used in the isInstance method."""

    def __init__(self):
        """Avoid initializing the class."""
        raise NotImplementedError("This class is a placeholder, it should not be initialized")

    def __name__(self):
        """Return the class name."""
        return "Float"


@_register_extention(ee)
class Integer:
    """Placeholder Integer class to be used in the isInstance method."""

    def __init__(self):
        """Avoid initializing the class."""
        raise NotImplementedError("This class is a placeholder, it should not be initialized")

    def __name__(self):
        """Return the class name."""
        return "Integer"
