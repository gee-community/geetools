# coding=utf-8
""" Module holding tools for ee.ImageCollections and ee.FeatueCollections """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


class Dictionary(ee.Dictionary):

    def __init__(self, *args, **kwargs):
        super(Dictionary, self).__init__(*args, **kwargs)

    def sort_dict(self):
        """ Sort a dictionary """
        keys = self.keys()
        ordered = keys.sort()

        def iteration(key, first):
            new = ee.Dictionary(first)
            val = self.get(key)
            return new.set(key, val)

        return ee.Dictionary(ordered.iterate(iteration, ee.Dictionary()))