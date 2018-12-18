# coding=utf-8
from __future__ import absolute_import, division, print_function

__version__ = "0.1.6"

__title__ = "geetools"
__summary__ = "A set of useful tools to use with Google Earth Engine Python" \
              "API"
__uri__ = "http://geetools.readthedocs.io"

__author__ = "Rodrigo E. Principe"
__email__ = "fitoprincipe82@gmail.com"

__license__ = "MIT"
__copyright__ = "2017 Rodrigo E. Principe"

from . import tools, bitreader, cloud_mask, expressions, decision_tree,\
              filters, indices

from .ui.ipymap import Map
from .ui import eprint
from . import algorithms
from .satellite import Satellite
from .satellite import today
from .tools.imagecollection import wrapper
