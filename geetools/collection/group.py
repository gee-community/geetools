# coding=utf-8
""" Group of collections """
from . import getCommonBands, rescale
from datetime import date

class CollectionGroup(object):
    def __init__(self, *args):
        self.collections = args

    @property
    def ids(self):
        return [col.id for col in self.collections]

    def commonBands(self, reference='all', match='id'):
        """ Get a list of the bands that exist in all collections """
        return getCommonBands(*self.collections, reference=reference,
                              match=match)

    def scales(self):
        """ Get the minimum scale value that takes evey common band """
        scales = {}
        common = self.commonBands()
        for band in common:
            band_scales = []
            for collection in self.collections:
                scale = collection.scales()[band]
                band_scales.append(scale)
            scales[band] = {'min': min(band_scales),
                            'max': max(band_scales)}

        return scales

    def start_date(self):
        """ Get the absolute start date for the group """
        starts = [date.fromisoformat(c.start_date) for c in self.collections]
        return min(starts).isoformat()

    def end_date(self):
        """ Get the absolute end date for the group """
        starts = [date.fromisoformat(c.end_date) for c in self.collections]
        return max(starts).isoformat()
