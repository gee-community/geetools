"""TODO missing docstring."""
import os

import ee

from .. import tools
from .._deprecated_utils import makeName
from . import utils


def toDrive(
    collection,
    folder,
    namePattern="{id}",
    scale=30,
    dataType="float",
    region=None,
    datePattern=None,
    extra=None,
    verbose=False,
    **kwargs
):
    """Upload all images from one collection to Google Drive. You can use.

    the same arguments as the original function
    ee.batch.export.image.toDrive.

    :param collection: Collection to upload
    :type collection: ee.ImageCollection
    :param folder: Google Drive folder to export the images to
    :type folder: str
    :param namePattern: pattern for the name.
        See geetools.tools.image.make_name function and also
        geetools.tools.string.format function
    :type namePattern: str
    :param scale: scale of the image (side of one pixel). Defaults to 30
        (Landsat resolution)
    :type scale: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :param region: area to upload. Default to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param datePattern: pattern for date if specified in namePattern.
        Defaults to 'yyyyMMdd'. See ee.Date.format for more details
    :type datePattern: str
    :param extra: extra parameters to parse to the name formatter
    :type extra: str
    :param verbose: print name of each exporting task
    :type verbose: bool
    :return: list of tasks
    :rtype: list
    """
    # empty tasks list
    tasklist = []
    # get region
    if region:
        region = tools.geometry.getRegion(region)

    # Make a list of images
    img_list = collection.toList(collection.size())

    n = 0
    while True:
        try:
            img = ee.Image(img_list.get(n))

            name = makeName(img, namePattern, datePattern, extra)
            name = name.getInfo()
            description = utils.matchDescription(name)

            # convert data type
            img = utils.convertDataType(dataType)(img)

            if region is None:
                region = tools.geometry.getRegion(img)

            task = ee.batch.Export.image.toDrive(
                image=img,
                description=description,
                folder=folder,
                fileNamePrefix=name,
                region=region,
                scale=scale,
                **kwargs
            )
            task.start()
            if verbose:
                print("exporting {} to folder '{}' in GDrive".format(name, folder))

            tasklist.append(task)
            n += 1
        except Exception as e:
            error = str(e).split(":")
            if error[0] == "List.get":
                break
            else:
                raise e

    return tasklist


def toCloudStorage(
    collection,
    bucket,
    folder=None,
    namePattern="{id}",
    region=None,
    scale=30,
    dataType="float",
    datePattern=None,
    verbose=False,
    extra=None,
    **kwargs
):
    """Upload all images from one collection to Google Cloud Storage. You can.

    use the same arguments as the original function
    ee.batch.export.image.toCloudStorage.

    :param collection: Collection to upload
    :type collection: ee.ImageCollection
    :param bucket: Google Cloud Storage bucket name
    :type folder: str
    :param folder: Google Cloud Storage prefix to export the images to
    :type folder: str
    :param namePattern: pattern for the name. See make_name function
    :type namePattern: str
    :param region: area to upload. default to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defaults to 30
        (Landsat resolution)
    :type scale: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :param datePattern: pattern for date if specified in namePattern.
        Defaults to 'yyyyMMdd'
    :type datePattern: str
    """
    # empty tasks list
    tasklist = []
    # get region
    region = tools.geometry.getRegion(region)
    # Make a list of images
    img_list = collection.toList(collection.size())

    n = 0
    while True:
        try:
            img = ee.Image(img_list.get(n))

            name = makeName(img, namePattern, datePattern, extra)
            name = name.getInfo()
            description = utils.matchDescription(name)

            # convert data type
            img = utils.convertDataType(dataType)(img)

            if folder is not None:
                path = folder + "/" + name
            else:
                path = name

            task = ee.batch.Export.image.toCloudStorage(
                image=img,
                description=description,
                bucket=bucket,
                path=path,
                region=region,
                scale=scale,
                **kwargs
            )
            task.start()
            tasklist.append(task)
            if verbose:
                print("adding task {} to list".format(name))
            n += 1

        except Exception as e:
            error = str(e).split(":")
            if error[0] == "List.get":
                break
            else:
                raise e

    return tasklist


def toAsset(
    collection,
    assetPath,
    namePattern=None,
    scale=30,
    region=None,
    create=True,
    verbose=False,
    datePattern="yyyyMMdd",
    extra=None,
    **kwargs
):
    """Upload all images from one collection to a Earth Engine Asset.

    You can use the same arguments as the original function
    ee.batch.export.image.toDrive.

    :param collection: Collection to upload
    :type collection: ee.ImageCollection
    :param assetPath: path of the asset where images will go
    :type assetPath: str
    :param namePattern: pattern for the name. If None, it uses the position
        of the image in the image collection as the name. Otherwise see
        geetools.tools.image.make_name function and also
        geetools.tools.string.format function
    :type namePattern: str
    :param region: area to upload. default to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defaults to 30
        (Landsat resolution)
    :type scale: int
    :return: list of tasks
    :rtype: list
    """
    tasklist = []

    if create:
        utils.createAssets([assetPath], "ImageCollection", True)

    if region:
        region = tools.geometry.getRegion(region)

    added = False
    if namePattern:
        imlist = collection.toList(collection.size())
        idx = 0
        while True:
            try:
                img = imlist.get(idx)
                img = ee.Image(img)
                if isinstance(extra, dict):
                    if added:
                        extra.pop("position")
                    if "position" not in extra:
                        extra["position"] = idx
                else:
                    extra = dict(position=idx)
                    added = True
                name = makeName(img, namePattern, datePattern, extra)
                name = name.getInfo()
                description = utils.matchDescription(name)
                assetId = assetPath + "/" + name

                params = dict(image=img, assetId=assetId, description=description, scale=scale)
                if region:
                    params["region"] = region
                if kwargs:
                    params.update(kwargs)

                task = ee.batch.Export.image.toAsset(**params)
                task.start()

                if verbose:
                    print("Exporting {} to {}".format(name, assetId))

                tasklist.append(task)
                idx += 1
            except Exception as e:
                error = str(e).split(":")
                if error[0] == "List.get":
                    break
                else:
                    raise e

    else:
        size = collection.size().getInfo()
        imlist = collection.toList(size)
        for idx in range(0, size + 1):
            img = imlist.get(idx)
            img = ee.Image(img)
            name = str(idx)
            description = name
            assetId = assetPath + "/" + name

            if region is None:
                region = tools.geometry.getRegion(img)

            task = ee.batch.Export.image.toAsset(
                image=img,
                assetId=assetId,
                description=description,
                region=region,
                scale=scale,
                **kwargs
            )
            task.start()

            if verbose:
                print("Exporting {} to {}".format(name, assetId))

            tasklist.append(task)

    return tasklist


def qgisCode(collection, visParams=None, name=None, datePattern=None, verbose=False):
    """Missing docstring."""
    QGIS_COL_CODE = """names={names}
urls={urls}
for name, url in zip(names, urls):
    urlWithParams = "type=xyz&url={{}}".format(url)
    rlayer = QgsRasterLayer(urlWithParams, name, "wms")
    if rlayer.isValid():
        QgsProject.instance().addMapLayer(rlayer)
    else:
        print("invalid layer")
"""
    name = name or "{id}"
    names = []
    urls = []
    i = 0
    collist = collection.toList(collection.size())
    catch = "List.get: List index must be between"
    while True:
        try:
            img = ee.Image(collist.get(i))
            n = makeName(img, name, datePattern).getInfo()
            if verbose:
                print("processing {}".format(n))
            url = tools.image.getTileURL(img, visParams)
            names.append(n)
            urls.append(url)
            i += 1
        except Exception as e:
            if catch in str(e):
                break
            else:
                raise e

    return QGIS_COL_CODE.format(names=names, urls=urls)


def toQGIS(
    collection,
    visParams=None,
    name=None,
    filename=None,
    path=None,
    datePattern=None,
    replace=True,
    verbose=True,
):
    """Download a python file to import from QGIS."""
    code = qgisCode(collection, visParams, name, datePattern, verbose)
    path = path or os.getcwd()
    # Check extension
    if filename:
        ext = filename.split(".")[-1]
        if ext != "py":
            filename += ".py"
    else:
        filename = "qgis2ee"
    # add _qgis_ to filename
    split = filename.split(".")[:-1]
    noext = ".".join(split)
    filename = "{}_qgis_".format(noext)
    # process
    finalpath = os.path.join(path, filename)
    finalpath = "{}.py".format(finalpath)
    if not os.path.exists(finalpath) or replace:
        with open(finalpath, "w+") as thefile:
            thefile.write(code)
        return thefile
    else:
        return None
