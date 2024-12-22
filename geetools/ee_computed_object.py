"""Extra tools for the :py:class:`ee.ComputedObject` class."""
from __future__ import annotations

import json
import os
from pathlib import Path

import ee

from .accessors import _register_extention


# -- types management ----------------------------------------------------------
@_register_extention(ee.ComputedObject)
def isInstance(self, klass: type) -> ee.Number:
    """Return 1 if the element is the passed type or 0 if not.

    Parameters:
        klass: The class to check the instance of.

    Returns:
        ``1`` if the element is the passed type or ``0`` if not.

    Examples:
        .. jupyter-execute::

            import ee, geetools
            from geetools.utils import initialize_documentation

            initialize_documentation()

            # test if a String is a ee.String
            s = ee.String("foo")
            isString = ee.String("foo").isInstance(ee.String)
            print(f"{s.getInfo()} is a earthengine string: {isString.getInfo()}")

            # test if a Number is a ee.String
            n = ee.Number(1)
            isString = ee.Number(1).isInstance(ee.String)
            print(f"{n.getInfo()} is a earthengine string: {isString.getInfo()}")
    """
    return ee.Algorithms.ObjectType(self).compareTo(klass.__name__).eq(0)


# -- .gee files ----------------------------------------------------------------
@_register_extention(ee.ComputedObject)  # type: ignore
def save(self, path: os.PathLike) -> Path:
    """Save a :py:class:`ee.ComputedObject` to a .gee file.

    The file contains the JSON representation of the object. It still needs to be computed via :py:meth:`ee.ComputedObject.getInfo` to be used.

    Parameters:
        path: The path to save the object to.

    Returns:
        The path to the saved file.

    Examples:
        .. jupyter-execute::

            from tempfile import TemporaryDirectory
            from pathlib import Path
            import ee, geetools
            from geetools.utils import initialize_documentation

            initialize_documentation()

            img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM")

            with TemporaryDirectory() as tmp:
                file = Path(tmp) / "test.gee"
                img.save(file)
                print(file.read_text())
    """
    path = Path(path).with_suffix(".gee")
    path.write_text(json.dumps(ee.serializer.encode(self)))
    return path


@staticmethod  # type: ignore
@_register_extention(ee.ComputedObject)  # type: ignore
def open(path: os.PathLike) -> ee.ComputedObject:
    """Open a .gee file as a ComputedObject.

    Parameters:
        path: The path to the file to open.

    Returns:
        The ComputedObject instance.

    Examples:
        .. jupyter-execute::

            from tempfile import TemporaryDirectory
            from pathlib import Path
            import ee, geetools
            from geetools.utils import initialize_documentation

            initialize_documentation()

            img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/20200101T100319_20200101T100321_T32TQM")

            with TemporaryDirectory() as tmp:
                file = Path(tmp) / "test.gee"
                img.save(file)
                obj = ee.Image.open(file)
                print(obj.getInfo())
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
