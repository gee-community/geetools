"""A package to use with Google Earth Engine Python API."""
import ee

# it needs to be imported first as it's the mother class
from . import ComputedObject

# reproduce older structure of the lib (deprecated)
# will be removed along the deprecation cycle
from . import _deprecated_filters as filters
from . import _deprecated_manager as manager
from . import _deprecated_oauth as oauth
from . import _deprecated_visualization as visualization
from . import _deprecated_expressions as expressions
from .tools import array
from .tools import collection
from .tools import date
from .tools import dictionary
from .tools import element
from .tools import feature
from .tools import featurecollection
from .tools import geometry
from .tools import number
from .tools import string

# then we extend all the other classes
from .Array import Array
from .Date import Date
from .DateRange import DateRange
from .Dictionary import Dictionary
from .Feature import Feature
from .FeatureCollection import FeatureCollection
from .Filter import Filter
from .Float import Float
from .Geometry import Geometry
from .Image import Image
from .Integer import Integer
from .Join import Join
from .List import List
from .Number import Number
from .String import String

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
