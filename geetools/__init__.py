"""A package to use with Google Earth Engine Python API."""
from ._version import __version__  # noqa: F401

__title__ = "geetools"
__summary__ = "A set of useful tools to use with Google Earth Engine Python" "API"
__uri__ = "http://geetools.readthedocs.io"

__author__ = "Rodrigo E. Principe"
__email__ = "fitoprincipe82@gmail.com"

__license__ = "MIT"
__copyright__ = "2017 Rodrigo E. Principe"

# from geetools import (
# bitreader,
# cloud_mask,
# expressions,
# decision_tree,
# filters,
# indices,
# batch,
# algorithms,
# composite,
# manager,
# utils,
# collection,
# oauth,
# visualization,
# classification
# )
# from geetools.tools import (
# array,
# date,
# dictionary,
# ee_list,
# featurecollection,
# geometry,
# image,
# imagecollection,
# string
# )
# from geetools.ui import eprint
# from geetools.batch import Export, Import, Convert, Download
# from geetools.oauth import Initialize
# from geetools.utils import evaluate

from .Number import Number  # noqa: F401

# reproduce older structure of the lib (deprecated)
# will be removed along the deprecation cycle
from .tools import number  # noqa: F401
