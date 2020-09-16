""" EE Element """
import ee

STRING = 'String'
INTEGER = 'Integer'
FLOAT = 'Float'
IMAGE = 'Image'
IMAGECOLLECTION = 'ImageCollection'
FEATURE = 'Feature'
GEOMETRY = 'Geometry'


def _isType(element, checktype):
    """ Return 1 if the element is the passed type or 0 if not """
    otype = ee.Algorithms.ObjectType(element)
    return otype.compareTo(checktype).eq(0)


def isString(element):
    return _isType(element, STRING)


def isInteger(element):
    return _isType(element, INTEGER)


def isFloat(element):
    return _isType(element, FLOAT)


def isNumber(element):
    return isFloat(element).Or(isInteger(element))


def isImage(element):
    return _isType(element, IMAGE)


def isImageCollection(element):
    return _isType(element, IMAGECOLLECTION)


def isFeature(element):
    return _isType(element, FEATURE)


def isGeometry(element):
    return _isType(element, GEOMETRY)
