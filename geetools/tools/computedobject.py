"""EE Computed Object."""
import ee

STRING = "String"
INTEGER = "Integer"
FLOAT = "Float"
IMAGE = "Image"
IMAGECOLLECTION = "ImageCollection"
FEATURE = "Feature"
GEOMETRY = "Geometry"


def _isType(ComputedObject, checktype):
    """Return 1 if the element is the passed type or 0 if not."""
    otype = ee.Algorithms.ObjectType(ComputedObject)
    return otype.compareTo(checktype).eq(0)


def isString(ComputedObject):
    return _isType(ComputedObject, STRING)


def isInteger(ComputedObject):
    return _isType(ComputedObject, INTEGER)


def isFloat(ComputedObject):
    return _isType(ComputedObject, FLOAT)


def isNumber(ComputedObject):
    return isFloat(ComputedObject).Or(isInteger(ComputedObject))


def isImage(ComputedObject):
    return _isType(ComputedObject, IMAGE)


def isImageCollection(ComputedObject):
    return _isType(ComputedObject, IMAGECOLLECTION)


def isFeature(ComputedObject):
    return _isType(ComputedObject, FEATURE)


def isGeometry(ComputedObject):
    return _isType(ComputedObject, GEOMETRY)
