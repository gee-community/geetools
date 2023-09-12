"""Legacy method for all ``ee.ComputedObject`` subclasses."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isString(ComputedObject):
    return ComputedObject.isInstance(ee.String)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isInteger(ComputedObject):
    return ComputedObject.isInstance(ee.Integer)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isFloat(ComputedObject):
    return ComputedObject.isInstance(ee.Float)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isImage(ComputedObject):
    return ComputedObject.isInstance(ee.Image)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isImageCollection(ComputedObject):
    return ComputedObject.isInstance(ee.ImageCollection)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isFeature(ComputedObject):
    return ComputedObject.isInstance(ee.Feature)


@deprecated(version="1.0.0", reason="Use ee.ComputedObject.isInstance instead")
def isGeometry(ComputedObject):
    return ComputedObject.isInstance(ee.Geometry)
