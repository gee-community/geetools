# coding=utf-8

from __future__ import absolute_import, division, print_function
from .tools import eprint

from .tools_image import Mapping
from .tools_collection import FeatureCollection
from .tools_segmentation import SNIC

from . import tools
from . import tools_image, tools_list, tools_number, tools_dictionary,\
              tools_collection, tools_segmentation

__version__ = "0.0.21dev"

__title__ = "geetools"
__summary__ = "A set of useful tools to use with Google Earth Engine Python" \
              "API"
__uri__ = "http://geetools.readthedocs.io"

__author__ = "Rodrigo E. Principe"
__email__ = "fitoprincipe82@gmail.com"

__license__ = "MIT"
__copyright__ = "2017 Rodrigo E. Principe"