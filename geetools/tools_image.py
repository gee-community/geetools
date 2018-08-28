# coding=utf-8
"""
Tools for ee.Image
"""
import ee
import ee.data
if not ee.data._initialized: ee.Initialize()

class Image(object):
    """ Image class to hold ee.Image methods """

    @staticmethod
    def constant(value=0, names=None, from_dict=None):
        """ Create a constant image with the given band names and value, and/or
        from a dictionary of {name: value}

        :param names: list of names
        :type names: ee.List or list
        :param value: value for every band of the resulting image
        :type value: int or float
        :param from_dict: {name: value}
        :type from_dict: dict
        :rtype: ee.Image
        """
        image = ee.Image.constant(0)
        bandnames = ee.List([])
        if names:
            bandnames = names if isinstance(names, ee.List) else ee.List(names)
            def bn(name, img):
                img = ee.Image(img)
                newi = ee.Image(value).select([0], [name])
                return img.addBands(newi)
            image = ee.Image(bandnames.iterate(bn, image)) \
                .select(bandnames)

        if from_dict:
            bandnames = bandnames.cat(ee.List(from_dict.keys()))
            for name, value in from_dict.items():
                i = ee.Image(value).select([0], [name])
                image = image.addBands(i).select(bandnames)

        if not from_dict and not names:
            image = ee.Image.constant(value)

        return image

    @staticmethod
    def addMultiBands(*imgs):
        """ Image.addBands for many images. All bands from all images will be
        put together, so if there is one band with the same name in different
        images, the first occurrence will keep the name and the rest will have a
        number suffix ({band}_1, {band}_2, etc)

        :param imgs: images to add bands
        :type imgs: tuple
        :rtype: ee.Image
        """
        img  = imgs[0]
        for i in imgs[1:]:
            img = img.addBands(i)
        return img