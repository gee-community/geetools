# coding=utf-8
""" Group of collections """


class CollectionGroup(object):
    def __init__(self, *args):
        self.collections = args

    def common_bands(self):
        """ Get a list of the bands that exist in all collections """
        first = self.collections[0]
        first_bands = first.bands
        first_set = set(first_bands.keys())

        if (len(self.collections) == 1):
            return first_bands
        else:
            rest = self.collections[1:]
            for col in rest:
                bands = col.bands
                bandset = set(bands.keys())
                first_set = first_set.intersection(bandset)

        return list(first_set)

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

