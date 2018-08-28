# coding=utf-8
""" Module holding tools for ee.ImageCollections and ee.FeatueCollections """
import ee


class Collection(object):

    @staticmethod
    def fill_with_last(collection):
        """ Fill masked values of each image pixel with the last available value

        :param collection: the collection that holds the images that will be filled
        :type collection: ee.ImageCollection
        :rtype: ee.ImageCollection
        """
        collection = collection.sort('system:time_start', True)
        collist = collection.toList(collection.size())
        first = ee.Image(collist.get(0)).unmask()
        rest = collist.slice(1)

        def wrap(img, ini):
            ini = ee.List(ini)
            img = ee.Image(img)
            last = ee.Image(ini.get(-1))
            mask = img.mask().Not()
            last_masked = last.updateMask(mask)
            last2add = last_masked.unmask()
            img2add = img.unmask()
            added = img2add.add(last2add) \
                .set('system:index', ee.String(img.id()))

            props = img.propertyNames()
            condition = props.contains('system:time_start')

            final = ee.Image(ee.Algorithms.If(condition,
                                              added.set('system:time_start',
                                                        img.date().millis()),
                                              added))

            return ini.add(final.copyProperties(img))

        newcol = ee.List(rest.iterate(wrap, ee.List([first])))
        return ee.ImageCollection.fromImages(newcol)
