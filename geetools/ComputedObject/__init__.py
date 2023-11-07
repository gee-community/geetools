"""Extra tools for the ``ee.ComputedObject`` class."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Type, Union

import ee


def extend(cls):
    """Extends the cls class.

    This is only used on the ``ComputedObject`` as it's the parent class of all.
    Using the regular accessor would lead to a duplicate member and undesired behavior.

    Parameters:
        cls: Class to extend.

    Returns:
        Decorator for extending classes.
    """
    return lambda f: (setattr(cls, f.__name__, f) or f)


@extend(ee.ComputedObject)
def isInstance(self, klass: Type) -> ee.Number:
    """Return 1 if the element is the passed type or 0 if not.

    Parameters:
        klass: The class to check the instance of.

    Returns:
        ``1`` if the element is the passed type or ``0`` if not.

    Examples:
        .. jupyter-execute::

            import ee, geetools

            ee.Initialize()

            s = ee.String("foo").isInstance(ee.String)
            s.getInfo()
    """
    return ee.Algorithms.ObjectType(self).compareTo(klass.__name__).eq(0)


@extend(ee.ComputedObject)
def save(self, path: Union[str, Path]) -> Path:
    """Save a ``ComputedObject`` to a .gee file.

    The file contains the JSON representation of the object. it still need to be computed via ``getInfo()`` to be used.

    Parameters:
        path: The path to save the object to.

    Returns:
        The path to the saved file.

    Examples:
        .. jupyter-execute::

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


@extend(ee.ComputedObject)
@classmethod
def open(cls, path: Union[str, Path]) -> ee.ComputedObject:
    """Open a .gee file as a ComputedObject.

    Parameters:
        path: The path to the file to open.

    Returns:
        The ComputedObject instance.

    Examples:
        .. jupyter-execute::

            import ee, geetools
            from tempfile import TemporaryDirectory
            from pathlib import Path

            ee.Initialize()

            img = ee.Image("COPERNICUS/S2/20151128T112653_20151128T135750_T29SND")
            with TemporaryDirectory() as tmp:
                file = Path(tmp) / "test.gee"
                img.geetools.save(file)
                obj = geetools.open(file)
                print(obj)
    """
    if (path := Path(path)).suffix != ".gee":
        raise ValueError("File must be a .gee file")

    computedObject = ee.deserializer.decode(json.loads(path.read_text()))
    return cls(computedObject)
