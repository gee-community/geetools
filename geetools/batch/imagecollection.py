# coding=utf-8
import ee
import os
from . import utils
from ..utils import makeName
from .. import tools


def toDrive(collection, folder, namePattern='{id}', scale=30,
            dataType="float", region=None, datePattern=None,
            extra=None, verbose=False, **kwargs):
    """ Upload all images from one collection to Google Drive. You can use
    the same arguments as the original function
    ee.batch.export.image.toDrive

    :param collection: Collection to upload
    :type collection: ee.ImageCollection
    :param folder: Google Drive folder to export the images to
    :type folder: str
    :param namePattern: pattern for the name. See make_name function
    :type namePattern: str
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
        (Landsat resolution)
    :type scale: int
    :param maxImgs: maximum number of images inside the collection
    :type maxImgs: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :param datePattern: pattern for date if specified in namePattern.
        Defaults to 'yyyyMMdd'
    :type datePattern: str
    :return: list of tasks
    :rtype: list
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

            task = ee.batch.Export.image.toDrive(image=img,
                                                 description=description,
                                                 folder=folder,
                                                 fileNamePrefix=name,
                                                 region=region,
                                                 scale=scale, **kwargs)
            task.start()
            if verbose:
                print("exporting {} to folder '{}' in GDrive".format(name, folder))

            tasklist.append(task)
            n += 1
        except Exception as e:
            error = str(e).split(':')
            if error[0] == 'List.get':
                break
            else:
                raise e


def toCloudStorage(collection, bucket, folder=None, namePattern='{id}',
                   region=None, scale=30, dataType="float", datePattern=None,
                   verbose=False, extra=None, **kwargs):
    """ Upload all images from one collection to Google Cloud Storage. You can
    use the same arguments as the original function
    ee.batch.export.image.toCloudStorage

    :param collection: Collection to upload
    :type collection: ee.ImageCollection
    :param bucket: Google Cloud Storage bucket name
    :type folder: str
    :param folder: Google Cloud Storage prefix to export the images to
    :type folder: str
    :param namePattern: pattern for the name. See make_name function
    :type namePattern: str
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
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

            task = ee.batch.Export.image.toCloudStorage(image=img,
                                                 description=description,
                                                 bucket=bucket,
                                                 path=path,
                                                 region=region,
                                                 scale=scale,
                                                 **kwargs)
            task.start()
            tasklist.append(task)
            if verbose:
                print("adding task {} to list".format(name))
            n += 1

        except Exception as e:
            error = str(e).split(':')
            if error[0] == 'List.get':
                break
            else:
                raise e


def toAsset(col, assetPath, scale=30, region=None, create=True,
            verbose=False, **kwargs):
    """ Upload all images from one collection to a Earth Engine Asset.
    You can use the same arguments as the original function
    ee.batch.export.image.toDrive

    :param col: Collection to upload
    :type col: ee.ImageCollection
    :param assetPath: path of the asset where images will go
    :type assetPath: str
    :param region: area to upload. Defualt to the footprint of the first
        image in the collection
    :type region: ee.Geometry.Rectangle or ee.Feature
    :param scale: scale of the image (side of one pixel). Defults to 30
        (Landsat resolution)
    :type scale: int
    :param maxImgs: maximum number of images inside the collection
    :type maxImgs: int
    :param dataType: as downloaded images **must** have the same data type
        in all bands, you have to set it here. Can be one of: "float",
        "double", "int", "Uint8", "Int8" or a casting function like
        *ee.Image.toFloat*
    :type dataType: str
    :return: list of tasks
    :rtype: list
    """
    size = col.size().getInfo()
    alist = col.toList(size)
    tasklist = []

    if create:
        utils.createAssets([assetPath], 'ImageCollection', True)

    if region is None:
        first_img = ee.Image(alist.get(0))
        region = tools.geometry.getRegion(first_img)
    else:
        region = tools.geometry.getRegion(region)

    for idx in range(0, size):
        img = alist.get(idx)
        img = ee.Image(img)
        name = img.id().getInfo().split("/")[-1]
        description = utils.matchDescription(name)

        assetId = assetPath+"/"+name

        task = ee.batch.Export.image.toAsset(image=img,
                                             assetId=assetId,
                                             description=description,
                                             region=region,
                                             scale=scale, **kwargs)
        task.start()

        if verbose:
            print('Exporting {} to {}'.format(name, assetId))

        tasklist.append(task)

    return tasklist


def qgisCode(collection, visParams=None, name=None, datePattern=None,
             verbose=False):
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
    name = name or '{id}'
    names = []
    urls = []
    i = 0
    collist = collection.toList(collection.size())
    while True:
        try:
            img = ee.Image(collist.get(i))
            n = makeName(img, name, datePattern).getInfo()
            if verbose:
                print('processing {}'.format(n))
            url = tools.image.getTileURL(img, visParams)
            names.append(n)
            urls.append(url)
            i += 1
        except Exception as e:
            break

    return QGIS_COL_CODE.format(names=names, urls=urls)


def toQGIS(collection, visParams=None, name=None, filename=None, path=None,
           datePattern=None, replace=True, verbose=False):
    """ Download a python file to import from QGIS """
    code = qgisCode(collection, visParams, name, datePattern, verbose)
    path = path or os.getcwd()
    # Check extension
    if filename:
        ext = filename.split('.')[-1]
        if ext != 'py':
            filename += '.py'
    else:
        filename = 'qgis2ee'
    # add _qgis_ to filename
    splitted = filename.split('.')[:-1]
    noext = '.'.join(splitted)
    filename = '{}_qgis_'.format(noext)
    # process
    finalpath = os.path.join(path, filename)
    finalpath = '{}.py'.format(finalpath)
    if not os.path.exists(finalpath) or replace:
        with open(finalpath, 'w+') as thefile:
            thefile.write(code)
        return thefile
    else:
        return None
