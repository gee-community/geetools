# coding=utf-8
""" Group of collections """
from . import get_common_bands, rescale

class CollectionGroup(object):
    def __init__(self, *args):
        self.collections = args

    @property
    def ids(self):
        return [col.id for col in self.collections]

    def common_bands(self, reference='all'):
        """ Get a list of the bands that exist in all collections """
        return get_common_bands(*self.collections, reference=reference)

    def scales(self):
        """ Get the minimum scale value that takes evey common band """
        scales = {}
        common = self.common_bands()
        for band in common:
            band_scales = []
            for collection in self.collections:
                scale = collection.scales[band]
                band_scales.append(scale)
            scales[band] = {'min': min(band_scales),
                            'max': max(band_scales)}

        return scales

    def ee_collection(self):
        """ Build a unique Earth Engine ImageCollection with common bands
        renamed and scaled to match the first collection of the group """
        first_col = self.collections[0]
        bands = self.common_bands()

        first_col_ee = first_col.collection
        first_col_ee_renamed = first_col_ee.map(
            lambda img: first_col.rename_all(img)).select(bands)

        for i, col in enumerate(self.collections):
            if i == 0: continue
            col_ee = col.collection
            renamed = col_ee.map(lambda img: col.rename_all(img))
            rescaled = renamed.map(
                lambda img: rescale(img, col, first_col,
                                    renamed=True)).select(bands)

            first_col_ee_renamed = first_col_ee_renamed.merge(rescaled)

        return first_col_ee_renamed