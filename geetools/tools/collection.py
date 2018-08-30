# coding=utf-8
""" Module holding tools for ee.ImageCollections and ee.FeatueCollections """
import ee
import ee.data

if not ee.data._initialized:
    ee.Initialize()


def fill_with_last(collection):
    """ Fill masked values of each image pixel with the last available
    value

    :param self: the self that holds the images that will be filled
    :type self: ee.ImageCollection
    :rtype: ee.ImageCollection
    """

    new = collection.sort('system:time_start', True)
    collist = new.toList(new.size())
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


def get_values(collection, geometry, reducer=ee.Reducer.mean(), scale=None,
               id='system:index', properties=None, side='server'):
    """ Return all values of all bands of an image collection in the
        specified geometry

    :param geometry: Point from where to get the info
    :type geometry: ee.Geometry
    :param scale: The scale to use in the reducer. It defaults to 10 due
        to the minimum scale available in EE (Sentinel 10m)
    :type scale: int
    :param id: image property that will be the key in the result dict
    :type id: str
    :param properties: image properties that will be added to the resulting
        dict
    :type properties: list
    :param side: 'server' or 'client' side
    :type side: str
    :return: Values of all bands in the ponit
    :rtype: dict
    """
    if not scale:
        # scale = minscale(ee.Image(self.first()))
        scale = 1
    else:
        scale = int(scale)

    propid = ee.Image(collection.first()).get(id).getInfo()
    def transform(eeobject):
        if isinstance(propid, (int, float)):
            return ee.Number(eeobject).format()
        elif isinstance(propid, (str, unicode)):
            return ee.String(eeobject)
        else:
            msg = 'property must be a number or string, found {}'
            raise ValueError(msg.format(type(propid)))

    if not properties:
        properties = []
    properties = ee.List(properties)

    def listval(img, it):
        theid = ee.String(transform(img.get(id)))
        values = img.reduceRegion(reducer, geometry, scale)
        values = ee.Dictionary(values)
        img_props = img.propertyNames()

        def add_properties(prop, ini):
            ini = ee.Dictionary(ini)
            condition = img_props.contains(prop)
            def true():
                value = img.get(prop)
                return ini.set(prop, value)
            # value = img.get(prop)
            # return ini.set(prop, value)
            return ee.Algorithms.If(condition, true(), ini)

        with_prop = ee.Dictionary(properties.iterate(add_properties, values))
        return ee.Dictionary(it).set(theid, with_prop)

    result = collection.iterate(listval, ee.Dictionary({}))
    result = ee.Dictionary(result)

    if side == 'server':
        return result
    elif side == 'client':
        return result.getInfo()
    else:
        raise ValueError("side parameter must be 'server' or 'client'")


class FeatureCollection(ee.collection.Collection):

    @staticmethod
    def fromShapefile(filename):
        """ Convert an ESRI file (.shp and .dbf must be present) to a
        ee.FeatureCollection

        At the moment only works for shapes with less than 3000 records

        :param filename: the name of the filename. If the shape is not in the
            same path than the script, specify a path instead.
        :type filename: str
        :return: the FeatureCollection
        :rtype: ee.FeatureCollection
        """
        import shapefile
        from .tools import get_projection

        wgs84 = ee.Projection('EPSG:4326')
        # read the filename
        reader = shapefile.Reader(filename)
        fields = reader.fields[1:]
        field_names = [field[0] for field in fields]
        field_types = [field[1] for field in fields]
        types = dict(zip(field_names, field_types))
        features = []
        for sr in reader.shapeRecords():
            # atr = dict(zip(field_names, sr.record))
            atr = {}
            for fld, rec in zip(field_names, sr.record):
                fld_type = types[fld]
                if fld_type == 'D':
                    value = ee.Date(rec.isoformat()).millis().getInfo()
                elif fld_type in ['C', 'N', 'F']:
                    value = rec
                else:
                    continue
                atr[fld] = value
            geom = sr.shape.__geo_interface__
            geometry = ee.Geometry(geom, 'EPSG:' + get_projection(filename)) \
                .transform(wgs84, 1)
            feat = ee.Feature(geometry, atr)
            features.append(feat)

        return ee.FeatureCollection(features)