# coding=utf-8
""" Module holding tools for ee.FeatueCollections """
import ee
import ee.data
import shapefile

if not ee.data._initialized:
    ee.Initialize()


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