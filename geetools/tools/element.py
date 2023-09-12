"""EE Element. Common methods between Feature and Image."""
import ee


def fillNull(Element, proxy=-999):
    """Fill null values of an Element's properties with a proxy value."""
    todict = Element.toDictionary()
    null = Element.propertyNames().removeAll(todict.keys()).remove("system:index")
    null_list = ee.List.repeat(proxy, null.size())
    null_dict = ee.Dictionary.fromLists(null, null_list)
    return Element.setMulti(null_dict)
