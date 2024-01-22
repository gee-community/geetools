"""A set of custom mixin types to use in the package when dealing with Python/GEE functions."""
from __future__ import annotations

from pathlib import Path
from typing import Union

import ee

ee_str = Union[str, ee.String]
ee_int = Union[int, ee.Number]
ee_float = Union[float, ee.Number]
ee_number = Union[float, int, ee.Number]
ee_list = Union[list, ee.List]
ee_dict = Union[dict, ee.Dictionary]
ee_geomlike = Union[ee.Geometry, ee.Feature, ee.FeatureCollection]

pathlike = Union[str, Path]
number = Union[float, int]
