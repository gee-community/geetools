"""Toolbox for the ``ee.Geometry`` class."""
from __future__ import annotations

import ee

from .accessors import geetools_accessor


@geetools_accessor(ee.Geometry)
class Geometry:
    """Toolbox for the ``ee.Geometry`` class."""

    def __init__(self, obj: ee.Geometry):
        """Initialize the Geometry class."""
        self._obj = obj
