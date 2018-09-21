# coding=utf-8
""" Module holding tools for ee.FeatueCollections """
import ee
import ee.data
import shapefile
import json

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
}


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
            filecrs = geodict.get('crs').get('properties').get('name')
            splitcrs = filecrs.split(':')
            cleancrs = [part for part in splitcrs if part]
            try:
                if cleancrs[-1] == 'CRS84':
                    crs = 'EPSG:4326'
                elif cleancrs[-2] == 'EPSG':
                    crs = '{}:{}'.format(cleancrs[-2], cleancrs[-1])
                else:
                    raise ValueError('{} not recognized'.format(filecrs))
            except IndexError:
                raise ValueError('{} not recognized'.format(filecrs))

        for n, feat in enumerate(geodict.get('features')):
            properties = feat.get('properties')
            geom = feat.get('geometry')
            ty = geom.get('type')
            coords = geom.get('coordinates')
            ee_geom = GEOMETRY_TYPES.get(ty)(coords, proj=ee.Projection(crs))
            ee_feat = ee.feature.Feature(ee_geom, properties)
            features.append(ee_feat)

    return ee.FeatureCollection(features)