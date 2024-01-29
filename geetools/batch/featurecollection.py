"""TODO missing docstring."""
import csv
import json

import ee

from .. import tools
from . import utils


def fromShapefile(filename, crs=None, start=None, end=None):
    """Convert an ESRI file (.shp and .dbf must be present) to a.

    ee.FeatureCollection.

    At the moment only works for shapes with less than 1000 records and doesn't
    handle complex shapes.

    :param filename: the name of the filename. If the shape is not in the
        same path than the script, specify a path instead.
    :type filename: str
    :param start:
    :return: the FeatureCollection
    :rtype: ee.FeatureCollection
    """
    import shapefile

    wgs84 = ee.Projection("EPSG:4326")
    # read the filename
    reader = shapefile.Reader(filename)
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]
    field_types = [field[1] for field in fields]
    types = dict(zip(field_names, field_types))
    features = []

    projection = utils.getProjection(filename) if not crs else crs
    # catch a string with format "EPSG:XXX"
    if isinstance(projection, str):
        if "EPSG:" in projection:
            projection = projection.split(":")[1]
    projection = "EPSG:{}".format(projection)

    # filter records with start and end
    start = start if start else 0
    if not end:
        records = reader.shapeRecords()
        end = len(records)
    else:
        end = end + 1

    if (end - start) > 1000:
        msg = "Can't process more than 1000 records at a time. Found {}"
        raise ValueError(msg.format(end - start))

    for i in range(start, end):
        # atr = dict(zip(field_names, sr.record))
        sr = reader.shapeRecord(i)
        atr = {}
        for fld, rec in zip(field_names, sr.record):
            if rec is None:
                atr[fld] = None
                continue
            fld_type = types[fld]
            if fld_type == "D":
                value = ee.Date(rec.isoformat()).millis().getInfo()
            elif fld_type in ["C", "N", "F"]:
                value = rec
            else:
                continue
            atr[fld] = value
        geom = sr.shape.__geo_interface__
        if projection is not None:
            geometry = ee.Geometry(geom, projection).transform(wgs84, 1)
        else:
            geometry = ee.Geometry(geom)
        feat = ee.Feature(geometry, atr)
        features.append(feat)

    return ee.FeatureCollection(features)


def fromGeoJSON(filename=None, data=None, crs=None):
    """Create a list of Features from a GeoJSON file. Return a python tuple.

    with ee.Feature inside. This is due to failing when attempting to create a
    FeatureCollection (Broken Pipe ERROR) out of the list. You can try creating
    it yourself casting the result of this function to a ee.List or using it
    directly as a FeatureCollection argument.

    :param filename: the name of the file to load
    :type filename: str
    :param crs: a coordinate reference system in EPSG format. If not specified
        it will try to get it from the geoJSON, and if not there it will rise
        an error
    :type: crs: str
    :return: a tuple of features.
    """
    if filename:
        with open(filename, "r") as geoj:
            content = geoj.read()
            geodict = json.loads(content)
    else:
        geodict = data

    features = []
    # Get crs from GeoJSON
    if not crs:
        filecrs = geodict.get("crs")
        if filecrs:
            name = filecrs.get("properties").get("name")
            splitcrs = name.split(":")
            cleancrs = [part for part in splitcrs if part]
            try:
                if cleancrs[-1] == "CRS84":
                    crs = "EPSG:4326"
                elif cleancrs[-2] == "EPSG":
                    crs = "{}:{}".format(cleancrs[-2], cleancrs[-1])
                else:
                    raise ValueError("{} not recognized".format(name))
            except IndexError:
                raise ValueError("{} not recognized".format(name))
        else:
            crs = "EPSG:4326"

    for n, feat in enumerate(geodict.get("features")):
        properties = feat.get("properties")
        geom = feat.get("geometry")
        ty = geom.get("type")
        coords = geom.get("coordinates")
        if ty == "GeometryCollection":
            ee_geom = utils.GEOMETRY_TYPES.get(ty)(geom, opt_proj=crs)
        else:
            if ty == "Polygon":
                coords = utils.removeZ(coords) if utils.hasZ(coords) else coords
            ee_geom = utils.GEOMETRY_TYPES.get(ty)(coords, proj=ee.Projection(crs))
        ee_feat = ee.feature.Feature(ee_geom, properties)
        features.append(ee_feat)

    return tuple(features)


def fromKML(filename=None, data=None, crs=None, encoding=None):
    """Create a list of Features from a KML file. Return a python tuple.

    with ee.Feature inside. This is due to failing when attempting to create a
    FeatureCollection (Broken Pipe ERROR) out of the list. You can try creating
    it yourself casting the result of this function to a ee.List or using it
    directly as a FeatureCollection argument.

    :param filename: the name of the file to load
    :type filename: str
    :param crs: a coordinate reference system in EPSG format. If not specified
        it will try to get it from the geoJSON, and if not there it will rise
        an error
    :type: crs: str
    :return: a tuple of features.
    """
    geojsondict = utils.kmlToGeoJsonDict(filename, data, encoding)
    features = geojsondict["features"]

    for feat in features:
        # remove styleUrl
        prop = feat["properties"]
        if "styleUrl" in prop:
            prop.pop("styleUrl")

        # remove Z value if needed
        geom = feat["geometry"]
        ty = geom["type"]
        if ty == "GeometryCollection":
            geometries = geom["geometries"]
            for g in geometries:
                c = g["coordinates"]
                utils.removeZ(c)
        else:
            coords = geom["coordinates"]
            utils.removeZ(coords)

    return fromGeoJSON(data=geojsondict, crs=crs)


def toDict(collection, split_at=4000):
    """Get the FeatureCollection as a dict object."""
    size = collection.size()
    condition = size.gte(4999)

    def greater():
        size = collection.size()
        seq = tools.ee_list.sequence(0, size, split_at)
        limits = ee.List.zip(seq.slice(1), seq)

        def over_limits(n):
            n = ee.List(n)
            ini = ee.Number(n.get(0))
            end = ee.Number(n.get(1))
            return ee.FeatureCollection(collection.toList(ini, end))

        return limits.map(over_limits)

    collections = ee.List(ee.Algorithms.If(condition, greater(), ee.List([collection])))

    collections_size = collections.size().getInfo()

    col = ee.FeatureCollection(collections.get(0))
    content = col.getInfo()
    feats = content["features"]

    for i in range(0, collections_size):
        c = ee.FeatureCollection(collections.get(i))
        content_c = c.getInfo()
        feats_c = content_c["features"]
        feats = feats + feats_c

    content["features"] = feats

    return content


def toGeoJSON(collection, name, path=None, split_at=4000):
    """Export a FeatureCollection to a GeoJSON file.

    :param collection: The collection to export
    :type collection: ee.FeatureCollection
    :param name: name of the resulting file
    :type name: str
    :param path: The path where to save the file. If None, will be saved
        in the current folder
    :type path: str
    :param split_at: limit to avoid an EE Exception
    :type split_at: int
    :return: A GeoJSON (.geojson) file.
    :rtype: file
    """
    import json
    import os

    if not path:
        path = os.getcwd()

    # name
    if name[-8:-1] != ".geojson":
        fname = name + ".geojson"

    content = toDict(collection, split_at)

    with open(os.path.join(path, fname), "w") as thefile:
        thefile.write(json.dumps(content))

    return thefile


def toCSV(collection, filename, split_at=4000):
    """Alternative to download a FeatureCollection as a CSV."""
    d = toDict(collection, split_at)

    fields = list(d["columns"].keys())
    fields.append("geometry")

    features = d["features"]

    ext = filename[-4:]
    if ext != ".csv":
        filename += ".csv"

    with open(filename, "w") as thecsv:
        writer = csv.DictWriter(thecsv, fields)

        writer.writeheader()
        # write rows
        for feature in features:
            properties = feature["properties"]
            fid = feature["id"]
            geom = feature["geometry"]["type"]

            # match fields
            properties["system:index"] = fid
            properties["geometry"] = geom

            # write row
            writer.writerow(properties)

        return thecsv


def toLocal(collection, filename, filetype=None, selectors=None, path=None):
    """Download a FeatureCollection to a local file a CSV or geoJSON file.

    This uses a different method than `toGeoJSON` and `toCSV`.

    :param filetype: The filetype of download, either CSV or JSON.
        Defaults to CSV.
    :param selectors: The selectors that should be used to determine which
        attributes will be downloaded.
    :param filename: The name of the file to be downloaded
    """
    if not filetype:
        filetype = "CSV"

    url = collection.getDownloadURL(filetype, selectors, filename)
    thefile = utils.downloadFile(url, filename, filetype, path)
    return thefile


def toAsset(table, assetPath, name=None, create=True, verbose=False, **kwargs):
    """This function can create folders and ImageCollections on the fly.

    The rest is the same to Export.image.toAsset. You can pass the same
    params as the original function.

    :param table: the feature collection to upload
    :type table: ee.FeatureCollection
    :param assetPath: path to upload the image (only PATH, without
        filename)
    :type assetPath: str
    :param name: filename for the image (AssetID will be assetPath + name)
    :type name: str
    :return: the tasks
    :rtype: ee.batch.Task
    """
    # Check if the user is specified in the asset path
    is_user = assetPath.split("/")[0] == "users"
    if not is_user:
        user = ee.batch.data.getAssetRoots()[0]["id"]
        assetPath = "{}/{}".format(user, assetPath)

    if create:
        # Recursive create path
        path2create = assetPath  #  '/'.join(assetPath.split('/')[:-1])
        utils.createAssets([path2create], "Folder", True)

    # Asset ID (Path + name)
    assetId = "/".join([assetPath, name])
    # Description
    description = utils.matchDescription(name)
    # Init task
    task = ee.batch.Export.table.toAsset(table, assetId=assetId, description=description, **kwargs)
    task.start()
    if verbose:
        print("Exporting {} to {}".format(name, assetPath))

    return task


def _toDriveShapefile(
    collection,
    description="myExportTableTask",
    folder=None,
    fileNamePrefix=None,
    selectors=None,
    types=None,
    verbose=True,
    **kwargs
):
    """Export a FeatureCollection to a SHP in Google Drive. The advantage of.

    this over the one provided by GEE is that this function takes care of the
    geometries and exports one shapefile per geometry, so at the end you could
    get many shapefiles
    .
    """
    gtypes = utils.GEOMETRY_TYPES
    types = types or list(gtypes.keys())
    for gtype, _ in gtypes.items():
        if gtype not in types or gtype == "GeometryCollection":
            continue
        collection = collection.map(lambda feat: feat.set("GTYPE", feat.geometry().type()))
        onlytype = collection.filter(ee.Filter.eq("GTYPE", gtype))
        size = onlytype.size().getInfo()
        if size == 0:
            continue
        name = "{}_{}".format(fileNamePrefix, gtype)
        desc = "{}_{}".format(description, gtype)
        task = ee.batch.Export.table.toDrive(
            onlytype, desc, folder, name, "SHP", selectors, **kwargs
        )
        if verbose:
            print("Exporting {} to {}".format(name, folder))
        task.start()


def _toDriveShapefileGeomCol(
    collection,
    description="myExportTableTask",
    folder=None,
    fileNamePrefix=None,
    selectors=None,
    types=None,
    verbose=True,
    **kwargs
):
    """Export a FeatureCollection to a SHP in Google Drive. The advantage of.

    this over the one provided by GEE is that this function takes care of the
    geometries and exports one shapefile per geometry, so at the end you could
    get many shapefiles
    .
    """
    ids = collection.aggregate_array("system:index").getInfo()
    multipol = ee.FeatureCollection([])
    multils = ee.FeatureCollection([])
    multip = ee.FeatureCollection([])
    for iid in ids:
        feat = ee.Feature(collection.filter(ee.Filter.eq("system:index", iid)).first())
        fc = tools.feature.GeometryCollection_to_FeatureCollection(feat)
        fc = fc.map(lambda feat: feat.set("GTYPE", feat.geometry().type()))
        multipol = multipol.merge(fc.filter(ee.Filter.eq("GTYPE", "MultiPolygon")))
        multils = multils.merge(fc.filter(ee.Filter.eq("GTYPE", "MultiLineString]")))
        multip = multip.merge(fc.filter(ee.Filter.eq("GTYPE", "MultiPoint")))

    name = "{}_GC".format(fileNamePrefix)
    _toDriveShapefile(multipol, description, folder, name, selectors, types, verbose, **kwargs)
    _toDriveShapefile(multils, description, folder, name, selectors, types, verbose, **kwargs)
    _toDriveShapefile(multip, description, folder, name, selectors, types, verbose, **kwargs)


def toDriveShapefile(
    collection,
    description="myExportTableTask",
    folder=None,
    fileNamePrefix=None,
    selectors=None,
    types=None,
    verbose=True,
    **kwargs
):
    """Export a FeatureCollection to a SHP in Google Drive. The advantage of.

    this over the one provided by GEE is that this function takes care of the
    geometries and exports one shapefile per geometry, so at the end you could
    get many shapefiles
    .
    """
    collection = collection.map(lambda feat: feat.set("GTYPE", feat.geometry().type()))
    notGeomCol = collection.filter(ee.Filter.neq("GTYPE", "GeometryCollection"))
    GeomCol = collection.filter(ee.Filter.eq("GTYPE", "GeometryCollection"))
    _toDriveShapefile(
        notGeomCol, description, folder, fileNamePrefix, selectors, types, verbose, **kwargs
    )
    _toDriveShapefileGeomCol(
        GeomCol, description, folder, fileNamePrefix, selectors, types, verbose, **kwargs
    )
