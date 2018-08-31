# coding=utf-8

from __future__ import print_function
from . import tools
import ee

def binary(conditions, classes, mask_name='dt_mask'):

    cond = ee.Dictionary(conditions)
    paths = ee.Dictionary(classes)

    def C(condition, bool):
        # b = ee.Number(bool)
        return ee.Image(ee.Algorithms.If(bool, ee.Image(condition),
                                         ee.Image(condition).Not()))

    # function to iterate over the path (classes)
    def overpath(key, path):
        v = ee.List(path) # the path is a list of lists
        # define an intial image = 1 with one band with the name of the class
        ini = ee.Image.constant(1).select([0], [key])

        # iterate over the path (first arg is a pair: [cond, bool])
        def toiterate(pair, init):
            init = ee.Image(init)
            pair = ee.List(pair)
            boolean = pair.get(1)
            condition_key = pair.get(0)  # could need var casting
            condition = cond.get(condition_key)
            final_condition = C(condition, boolean)
            return ee.Image(init.And(ee.Image(final_condition)))

        result = ee.Image(v.iterate(toiterate, ini))
        return result

    new_classes = ee.Dictionary(paths.map(overpath))

    # UNIFY CLASSES. example: {'snow-1':x, 'snow-2':y} into {'snow': x.and(y)}
    new_classes_list = new_classes.keys()

    def mapclasses(el):
        return ee.String(el).split('-').get(0)

    repeated = new_classes_list.map(mapclasses)

    unique = tools.ee_list.remove_duplicates(repeated)

    # CREATE INITIAL DICT
    def createinitial(baseclass, ini):
        ini = ee.Dictionary(ini)
        i = ee.Image.constant(0).select([0], [baseclass])
        return ini.set(baseclass, i)

    ini = ee.Dictionary(unique.iterate(createinitial, ee.Dictionary({})))

    def unify(key, init):
        init = ee.Dictionary(init)
        baseclass = ee.String(key).split('-').get(0)
        mask_before = ee.Image(init.get(baseclass))
        mask = new_classes.get(key)
        new_mask = mask_before.Or(mask)
        return init.set(baseclass, new_mask)

    new_classes_unique = ee.Dictionary(new_classes_list.iterate(unify, ini))

    masks = new_classes_unique.values() # list of masks

    # Return an Image with one band per option

    def tomaskimg(mask, ini):
        ini = ee.Image(ini)
        return ini.addBands(mask)

    mask_img = ee.Image(masks.slice(1).iterate(tomaskimg,
                                               ee.Image(masks.get(0))))
    # print(mask_img)

    init = ee.Image.constant(0).rename(mask_name)

    def iterate_results(mask, ini):
        ini = ee.Image(ini)
        return ini.Or(mask)

    result = masks.iterate(iterate_results, init)

    not_mask = ee.Image(result).Not()

    return mask_img.addBands(not_mask)