"""Legacy tools for the ee.List class."""
import ee
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use ee.List.geetools.complement instead")
def difference(list1, list2):
    """Return the difference between two lists."""
    return ee.List(list1).geetools.complement(list2)


@deprecated(version="1.0.0", reason="Use ee.List.geetools.product instead")
def intersection(list1, list2):
    """Return the intersection between two lists."""
    return ee.List(list1).geetools.intersection(list2)


@deprecated(version="1.0.0", reason="Use ee.List.distinct instead")
def removeDuplicates(list):
    """Remove duplicates from a list."""
    return ee.List(list).distinct()


@deprecated(version="1.0.0", reason="Use ee.List.geetools.delete instead")
def removeIndex(list, index):
    """Remove an element from a list by index."""
    return ee.List(list).geetools.delete(index)


@deprecated(version="1.0.0", reason="Use ee.List.geetools.sequence instead")
def sequence(start, stop, step=1):
    """Create a sequence of numbers."""
    return ee.List.geetools.sequence(start, stop, step)


@deprecated(version="1.0.0", reason="Use ee.List.geetools.replaceMany instead")
def replaceDict(eelist, to_replace):
    """Replace many elements of a Earth Engine List object using a dictionary."""
    return ee.List(eelist).geetools.replaceMany(to_replace)


@deprecated(version="1.0.0", reason="Use ee.List.geetools.toStrings instead")
def toString(eelist):
    """Convert elements of a list into Strings."""
    return ee.List(eelist).geetools.toStrings()


@deprecated(version="1.0.0", reason="Use ee.List.geetools.format instead")
def format(eelist):
    """Format a list to a string."""
    return ee.String("[").cat(ee.List(eelist).geetools.join(",")).cat(ee.String("]"))


@deprecated(version="1.0.0", reason="Use ee.Dictionary.geetools.getMany instead")
def getFromDict(eelist, values):
    """Get a list of Dict's values from a list object."""
    return ee.Dictionary(values).geetools.getMany(eelist)


@deprecated(version="1.0.0", reason="Cast the list to ee.Array instead")
def transpose(eelist):
    """Transpose a list of lists."""
    return ee.Array(eelist).transpose()


@deprecated(version="1.0.0", reason="Use ee.List.geetools.zip instead")
def zip(eelist):
    """Zip a list of lists."""
    return ee.List(eelist).geetools.zip()
