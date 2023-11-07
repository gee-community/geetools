"""A package to use with Google Earth Engine Python API."""
import ee

# it needs to be imported first as it's the mother class
from . import ComputedObject  # noqa: F401
from . import _deprecated_expressions as expressions  # noqa: F401

# reproduce older structure of the lib (deprecated)
# will be removed along the deprecation cycle
from . import _deprecated_filters as filters  # noqa: F401
from . import _deprecated_manager as manager  # noqa: F401
from . import _deprecated_oauth as oauth  # noqa: F401
from . import _deprecated_visualization as visualization  # noqa: F401

# then we extend all the other classes
from .Array import Array  # noqa: F401
from .Date import Date  # noqa: F401
from .DateRange import DateRange  # noqa: F401
from .Dictionary import Dictionary  # noqa: F401
from .Feature import Feature  # noqa: F401
from .FeatureCollection import FeatureCollection  # noqa: F401
from .Filter import Filter  # noqa: F401
from .Float import Float
from .Geometry import Geometry  # noqa: F401
from .Image import Image  # noqa: F401
from .Integer import Integer
from .Join import Join  # noqa: F401
from .List import List  # noqa: F401
from .Number import Number  # noqa: F401
from .String import String  # noqa: F401
from .tools import (
    array,  # noqa: F401
    collection,  # noqa: F401
    date,  # noqa: F401
    dictionary,  # noqa: F401
    element,  # noqa: F401
    feature,  # noqa: F401
    featurecollection,  # noqa: F401
    geometry,  # noqa: F401
    number,  # noqa: F401
    string,  # noqa: F401
)

# from .User import User

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
