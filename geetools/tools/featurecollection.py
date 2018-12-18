# coding=utf-8
""" Module holding tools for ee.FeatueCollections """
import ee
import ee.data
import shapefile
import json

from . import collection as eecollection

if not ee.data._initialized:
    ee.Initialize()

GEOMETRY_TYPES = {
    'LineString': ee.geometry.Geometry.LineString,
    'LineRing': ee.geometry.Geometry.LinearRing,
    'MultiLineString': ee.geometry.Geometry.MultiLineString,
    'MultiPolygon': ee.geometry.Geometry.MultiPolygon,
    'MultiPoint': ee.geometry.Geometry.MultiPoint,
    'Point': ee.geometry.Geometry.Point,
    'Polygon': ee.geometry.Geometry.Polygon,
    'Rectangle': ee.geometry.Geometry.Rectangle,
    'GeometryCollection': ee.geometry.Geometry,
}


def addId(collection, name='id', start=1):
    """ Add a unique numeric identifier, from parameter 'start' to
    collection.size() stored in a property called with parameter 'name'

    :param collection: the collection
    :type collection: ee.FeatureCollection
    :param name: the name of the resulting property
    :type name: str
    :param start: the number to start from
    :type start: int
    :return: the parsed collection with a new property
    :rtype: ee.FeatureCollection
    """
    start = ee.Number(start)
    collist = collection.toList(collection.size())
    first = ee.Feature(collist.get(0))
    rest = collist.slice(1)

    # Set first id
    first = ee.List([first.set(name, start)])

    # Set rest
    def over_col(feat, last):
        last = ee.List(last)
        last_feat = ee.Feature(last.get(-1))
        feat = ee.Feature(feat)
        last_id = ee.Number(last_feat.get('id'))
        return last.add(feat.set('id', last_id.add(1)))

    return ee.FeatureCollection(ee.List(rest.iterate(over_col, first)))


def enumerateProperty(col, name='enumeration'):
    """ Create a list of lists in which each element of the list is:
    [index, element]. For example, if you parse a FeatureCollection with 3
    Features you'll get: [[0, feat0], [1, feat1], [2, feat2]]

    :param collection: the collection
    :return: ee.FeatureCollection
    """
    enumerated = eecollection.enumerate(col)

    def over_list(l):
        l = ee.List(l)
        index = ee.Number(l.get(0))
        element = l.get(1)
        return ee.Feature(element).set(name, index)

    featlist = enumerated.map(over_list)
    return ee.FeatureCollection(featlist)


def get_projection(filename):
    """ Get EPSG from a shapefile using ogr

    :param filename: an ESRI shapefile (.shp)
    :type filename: str
    """
    try:
        from osgeo import ogr
    except:
        import ogr

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(filename)

    # from Layer
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()

    return spatialRef.GetAttrValue("AUTHORITY", 1)


def fromShapefile(filename, start=None, end=None):
    """ Convert an ESRI file (.shp and .dbf must be present) to a
    ee.FeatureCollection

    At the moment only works for shapes with less than 1000 records and doesn't
    handle complex shapes.

    :param filename: the name of the filename. If the shape is not in the
        same path than the script, specify a path instead.
    :type filename: str
    :param start:
    :return: the FeatureCollection
    :rtype: ee.FeatureCollection
    """
    wgs84 = ee.Projection('EPSG:4326')
    # read the filename
    reader = shapefile.Reader(filename)
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]
    field_types = [field[1] for field in fields]
    types = dict(zip(field_names, field_types))
    features = []

    projection = get_projection(filename)

    # filter records with start and end
    start = start if start else 0
    if not end:
        records = reader.shapeRecords()
        end = len(records)
    else:
        end = end + 1

    if (end-start)>1000:
        msg = "Can't process more than 1000 records at a time. Found {}"
        raise ValueError(msg.format(end-start))

    for i in range(start, end):
        # atr = dict(zip(field_names, sr.record))
        sr = reader.shapeRecord(i)
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
        geometry = ee.Geometry(geom, 'EPSG:' + projection) \
            .transform(wgs84, 1)
        feat = ee.Feature(geometry, atr)
        features.append(feat)

    return ee.FeatureCollection(features)


def fromGeoJSON(filename, crs=None):
    """ Create a FeatureCollection from a GeoJSON file

    :param filename:
    :type filename: str
    :param crs: a coordinate reference system in EPSG format. If not specified
        it will try to get it from the geoJSON, and if not there it will rise
        an error
    :type: crs: str
    :return:
    """
    with open(filename, 'r') as geojson:
        content = geojson.read()
        geodict = json.loads(content)
        features = []
        # Get crs from GeoJSON
        if not crs:
            filecrs = geodict.get('crs')
            if filecrs:
                name = filecrs.get('properties').get('name')
                splitcrs = name.split(':')
                cleancrs = [part for part in splitcrs if part]
                try:
                    if cleancrs[-1] == 'CRS84':
                        crs = 'EPSG:4326'
                    elif cleancrs[-2] == 'EPSG':
                        crs = '{}:{}'.format(cleancrs[-2], cleancrs[-1])
                    else:
                        raise ValueError('{} not recognized'.format(name))
                except IndexError:
                    raise ValueError('{} not recognized'.format(name))
            else:
                crs = 'EPSG:4326'

        for n, feat in enumerate(geodict.get('features')):
            properties = feat.get('properties')
            geom = feat.get('geometry')
            ty = geom.get('type')
            coords = geom.get('coordinates')
            if ty == 'GeometryCollection':
                ee_geom = GEOMETRY_TYPES.get(ty)(geom, opt_proj=crs)
            else:
                ee_geom = GEOMETRY_TYPES.get(ty)(coords, proj=ee.Projection(crs))
            ee_feat = ee.feature.Feature(ee_geom, properties)
            features.append(ee_feat)

    return ee.FeatureCollection(features)