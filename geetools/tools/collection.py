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
