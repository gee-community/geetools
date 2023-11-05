"""A package to use with Google Earth Engine Python API."""
import ee

# from geetools import (
# bitreader,
# cloud_mask,
# expressions,
# decision_tree,
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
# ee_list,
# featurecollection,
# geometry,
# image,
# imagecollection,
# )
# from geetools.ui import eprint
# from geetools.batch import Export, Import, Convert, Download
# from geetools.oauth import Initialize
# from geetools.utils import evaluate
# it needs to be imported first as it's the mother class
from . import ComputedObject  # noqa: F401

# reproduce older structure of the lib (deprecated)
# will be removed along the deprecation cycle
from . import _deprecated_filters as filters  # noqa: F401

# then we extend all the other classes
from .Array import Array  # noqa: F401
from .Date import Date  # noqa: F401
from .DateRange import DateRange  # noqa: F401
from .Dictionary import Dictionary  # noqa: F401
from .FeatureCollection import FeatureCollection  # noqa: F401
from .Filter import Filter  # noqa: F401
from .Float import Float
from .Image import Image  # noqa: F401
from .Integer import Integer
from .List import List  # noqa: F401
from .Number import Number  # noqa: F401
from .String import String  # noqa: F401
from .tools import (
    array,  # noqa: F401
    date,  # noqa: F401
    dictionary,  # noqa: F401
    featurecollection,  # noqa: F401
    number,  # noqa: F401
    string,  # noqa: F401
)

# add the 2 placeholder classes to the ee namespace for consistency
ee.Integer = Integer
ee.Float = Float

__title__ = "geetools"
__summary__ = "A set of useful tools to use with Google Earth Engine Python" "API"
__uri__ = "http://geetools.readthedocs.io"
__version__ = "0.6.14"

__author__ = "Rodrigo E. Principe"
__email__ = "fitoprincipe82@gmail.com"

__license__ = "MIT"
__copyright__ = "2017 Rodrigo E. Principe"
