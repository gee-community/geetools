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
from . import _deprecated_utils as utils
from . import _deprecated_decision_tree as decision_tree
from . import _deprecated_indices as indices
from . import _deprecated_algorithms as algorithms
from . import _deprecated_composite as composite
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
from .tools import imagecollection

# then we extend all the other classes
from .Asset import Asset
from .Date import DateAccessor
from .Dictionary import DictionaryAccessor
from .Feature import FeatureAccessor
from .FeatureCollection import FeatureCollectionAccessor
from .Filter import FilterAccessor
from .Geometry import GeometryAccessor
from .Image import ImageAccessor
from .Join import JoinAccessor
from .List import ListAccessor
from .Number import NumberAccessor
from .String import StringAccessor
from .ImageCollection import ImageCollectionAccessor
from .Initialize import InitializeAccessor
from .Authenticate import AuthenticateAccessor
from .Array import ArrayAccessor
from .DateRange import DateRangeAccessor


__title__ = "geetools"
__summary__ = "A set of useful tools to use with Google Earth Engine Python" "API"
__uri__ = "http://geetools.readthedocs.io"
__version__ = "1.5.0"

__author__ = "Rodrigo E. Principe"
__email__ = "fitoprincipe82@gmail.com"

__license__ = "MIT"
__copyright__ = "2017 Rodrigo E. Principe"
