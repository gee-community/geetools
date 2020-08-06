# coding=utf-8
""" Module holding tools for ee.Collection """
import ee


def enumerate(collection):
    """ Create a list of lists in which each element of the list is:
    [index, element]. For example, if you parse a FeatureCollection with 3
    Features you'll get: [[0, feat0], [1, feat1], [2, feat2]]

    :param collection: can be an ImageCollection or a FeatureCollection
    :return: ee.Collection
    """
    collist = collection.toList(collection.size())

    # first element
    ini = ee.Number(0)
    first_image = ee.Image(collist.get(0))
    first = ee.List([ini, first_image])

    start = ee.List([first])
    rest = collist.slice(1)

    def over_list(im, s):
        im = ee.Image(im)
        s = ee.List(s)
        last = ee.List(s.get(-1))
        last_index = ee.Number(last.get(0))
        index = last_index.add(1)
        return s.add(ee.List([index, im]))

    list = ee.List(rest.iterate(over_list, start))

    return list


def joinByProperty(primary, secondary, propertyField, outer=False):
    """ Join 2 collections by a given property field.
    It assumes ids are unique so uses ee.Join.saveFirst.
    It drops non matching features.

    Example:

    fc1 = ee.FeatureCollection([ee.Feature(geom=ee.Geometry.Point([0,0]),
                                       opt_properties={'id': 1, 'prop_from_fc1': 'I am from fc1'})])
    fc2 = ee.FeatureCollection([ee.Feature(geom=ee.Geometry.Point([0,0]),
                                       opt_properties={'id': 1, 'prop_from_fc2': 'I am from fc2'})])
    joined = joinById(fc1, fc2, 'id')
    print(joined.getInfo())

    """
    Filter = ee.Filter.equals(leftField=propertyField,
                              rightField=propertyField)
    join = ee.Join.saveFirst(matchKey='match', outer=outer)
    joined = join.apply(primary, secondary, Filter)
    def overJoined(feat):
        properties = feat.propertyNames()
        retain = properties.remove('match')
        match = ee.Feature(feat.get('match'))
        matchprop = match.toDictionary()
        return feat.select(retain).setMulti(matchprop)

    return joined.map(overJoined)
