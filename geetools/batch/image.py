"""TODO missing docstring."""
import os

import ee

from .. import tools
from .._deprecated_utils import makeName
from . import utils


def toLocal(image, name=None, path=None, scale=None, region=None, dimensions=None, toFolder=True):
    """Download an Image to your hard drive.

    :param image: the image to download
    :type image: ee.Image
    :param path: the path to download the image. If None, it will be
        downloaded to the same folder as the script is
    :type path: str
    :param name: name of the file
    :type name: str
    :param scale: scale of the image to download. If None, tries to get it.
    :type scale: int
    :param region: region to from where to download the image. If None,
        will be the image region
    :type region: ee.Geometry
    :param
    """
    # TODO: checkExist
    try:
        import zipfile
    except Exception:
        raise ValueError("zipfile module not found, install it using " "`pip install zipfile`")

    name = name if name else image.id().getInfo()

    scale = scale if scale else int(tools.image.minscale(image).getInfo())

    if region:
        region = tools.geometry.getRegion(region)
    else:
        region = tools.geometry.getRegion(image)

    params = {"region": region, "scale": scale}

    if dimensions:
        params = params.update({"dimensions": dimensions})

    url = image.getDownloadURL(params)

    ext = "zip"

    utils.downloadFile(url, name, ext)

    filename = "{}.{}".format(name, ext)

    original_filepath = os.path.join(os.getcwd(), filename)

    if path:
        filepath = os.path.join(path, filename)
        os.rename(original_filepath, filepath)
    else:
        path = os.getcwd()
        filepath = os.path.join(path, filename)

    try:
        zip_ref = zipfile.ZipFile(filepath, "r")

        if toFolder:
            finalpath = os.path.join(path, name)
        else:
            finalpath = path

        zip_ref.extractall(finalpath)
        zip_ref.close()
    except:
        raise


def toAsset(
    image,
    assetPath,
    name=None,
    to="Folder",
    scale=None,
    region=None,
    create=True,
    verbose=False,
    **kwargs
):
    """This function can create folders and ImageCollections on the fly.

    The rest is the same to Export.image.toAsset. You can pass the same
    params as the original function.

    :param image: the image to upload
    :type image: ee.Image
    :param assetPath: path to upload the image (only PATH, without
        filename)
    :type assetPath: str
    :param name: filename for the image (AssetID will be assetPath + name)
    :type name: str
    :param to: where to save the image. Options: 'Folder' or
        'ImageCollection'
    :param region: area to upload. default to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel)
        (Landsat resolution)
    :type scale: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :param notebook: display a jupyter notebook widget to monitor the task
    :type notebook: bool
    :return: the tasks
    :rtype: ee.batch.Task
    """
    # Convert data type
    # image = utils.convertDataType(dataType)(image)

    # Check if the user is specified in the asset path
    is_user = assetPath.split("/")[0] == "users"
    if not is_user:
        user = ee.batch.data.getAssetRoots()[0]["id"]
        assetPath = "{}/{}".format(user, assetPath)

    # description = kwargs.get('description', image.id().getInfo())
    # Set scale
    scale = scale if scale else int(tools.image.minscale(image).getInfo())

    if create:
        # Recursive create path
        path2create = assetPath  #  '/'.join(assetPath.split('/')[:-1])
        utils.createAssets([path2create], to, True)

    # Region
    region = tools.geometry.getRegion(region)
    # Name
    name = name if name else image.id().getInfo()
    # Asset ID (Path + name)
    assetId = "/".join([assetPath, name])
    # Description
    description = utils.matchDescription(name)
    # Init task
    task = ee.batch.Export.image.toAsset(
        image, assetId=assetId, region=region, scale=scale, description=description, **kwargs
    )
    task.start()
    if verbose:
        print("Exporting {} to {}".format(name, assetPath))

    return task


def toDriveByFeature(
    image,
    collection,
    folder,
    namePattern,
    datePattern=None,
    scale=1000,
    dataType="float",
    verbose=False,
    **kwargs
):
    """Export an image clipped by features (Polygons). You can use the.

    same arguments as the original function ee.batch.export.image.toDrive.

    :Parameters:
    :param image: image to clip
    :type image: ee.Image
    :param collection: feature collection
    :type collection: ee.FeatureCollection
    :param folder: same as ee.Export
    :type folder: str
    :param namePattern: a name pattern using image and/or feature properties between
        brackets. Example: '{ID} {a_feat_prop} {an_image_prop}'
    :type namePattern: str
    :param datePattern: a date pattern to use for {system_date} pattern in name
    :type datePattern: str
    :param scale: same as ee.Export. Default to 1000
    :type scale: int
    :param dataType: as downloaded images **must** have the same data
    type in all
        bands, you have to set it here. Can be one of: "float",
        "double", "int",
        "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
    :type dataType: str

    :return: a list of all tasks (for further processing/checking)
    :rtype: list
    """
    collist = collection.toList(collection.size())
    tasklist = []
    i = 0
    while True:
        try:
            feat = ee.Feature(collist.get(i))
            props = feat.toDictionary()

            n = makeName(image, namePattern, datePattern)
            n = tools.string.format(n, props)
            n = n.getInfo()
            n = n.replace("{", "").replace("}", "")
            desc = utils.matchDescription(n)

            # convert data type
            image = utils.convertDataType(dataType)(image)

            region = tools.geometry.getRegion(feat)

            task = ee.batch.Export.image.toDrive(
                image=image,
                description=desc,
                folder=folder,
                fileNamePrefix=n,
                region=region,
                scale=scale,
                **kwargs
            )

            task.start()
            if verbose:
                print("exporting '{}' to '{}' folder in GDrive".format(n, folder))
            tasklist.append(task)

            i += 1
        except Exception as e:
            error = str(e).split(":")
            if error[0] == "List.get":
                break
            else:
                raise e


def qgisCode(image, visParams=None, name=None, namePattern=None, datePattern=None):
    """Missing docstring."""
    QGIS_IMG_CODE = """name = '{name}'
url = '{url}'
urlWithParams = "type=xyz&url={{}}".format(url)
rlayer = QgsRasterLayer(urlWithParams, name, "wms")
if rlayer.isValid():
    QgsProject.instance().addMapLayer(rlayer)
else:
    print("invalid layer")
"""
    url = tools.image.getTileURL(image, visParams)
    if namePattern:
        name = makeName(image, namePattern, datePattern)
    else:
        name = name or "no_name_img"
    return QGIS_IMG_CODE.format(name=name, url=url)


def toQGIS(
    image,
    visParams=None,
    name=None,
    filename=None,
    path=None,
    replace=True,
    verbose=False,
):
    """Download a python file to import from QGIS."""
    code = qgisCode(image, visParams, name)
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
