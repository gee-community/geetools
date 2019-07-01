# coding=utf-8
import ee
import os
from . import utils
from .. import tools


def toLocal(image, name=None, path=None, scale=None, region=None,
            dimensions=None, toFolder=True):
    """ Download an Image to your hard drive

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
    except:
        raise ValueError(
            'zipfile module not found, install it using '
            '`pip install zipfile`')

    name = name if name else image.id().getInfo()

    scale = scale if scale else int(tools.image.minscale(image).getInfo())

    if region:
        region = tools.geometry.getRegion(region)
    else:
        region = tools.geometry.getRegion(image)

    params = {'region': region,
              'scale': scale}

    if dimensions:
        params = params.update({'dimensions': dimensions})

    url = image.getDownloadURL(params)

    ext = 'zip'

    utils.downloadFile(url, name, ext)

    filename = '{}.{}'.format(name, ext)

    original_filepath = os.path.join(os.getcwd(), filename)

    if path:
        filepath = os.path.join(path, filename)
        os.rename(original_filepath, filepath)
    else:
        path = os.getcwd()
        filepath = os.path.join(path, filename)

    try:
        zip_ref = zipfile.ZipFile(filepath, 'r')

        if toFolder:
            finalpath = os.path.join(path, name)
        else:
            finalpath = path

        zip_ref.extractall(finalpath)
        zip_ref.close()
    except:
        raise


def toAsset(image, assetPath, name=None, to='Folder', scale=None,
            region=None, create=True, dataType='float', **kwargs):
    """ This function can create folders and ImageCollections on the fly.
    The rest is the same to Export.image.toAsset. You can pass the same
    params as the original function

    :param image: the image to upload
    :type image: ee.Image
    :param assetPath: path to upload the image (only PATH, without
        filename)
    :type assetPath: str
    :param name: filename for the image (AssetID will be assetPath + name)
    :type name: str
    :param to: where to save the image. Options: 'Folder' or
        'ImageCollection'
    :param region: area to upload. Defualt to the footprint of the first
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
    image = utils.convertDataType(dataType)(image)

    # Check if the user is specified in the asset path
    is_user = (assetPath.split('/')[0] == 'users')
    if not is_user:
        user = ee.batch.data.getAssetRoots()[0]['id']
        assetPath = "{}/{}".format(user, assetPath)

    # description = kwargs.get('description', image.id().getInfo())
    # Set scale
    scale = scale if scale else int(tools.image.minscale(image).getInfo())

    if create:
        # Recrusive create path
        path2create = assetPath #  '/'.join(assetPath.split('/')[:-1])
        utils.createAssets([path2create], to, True)

    # Region
    region = tools.geometry.getRegion(region)
    # Name
    name = name if name else image.id().getInfo()
    # Asset ID (Path + name)
    assetId = '/'.join([assetPath, name])
    # Description
    description = name.replace('/','_')
    # Init task
    task = ee.batch.Export.image.toAsset(image, assetId=assetId,
                                         region=region, scale=scale,
                                         description=description,
                                         **kwargs)
    task.start()

    return task


def toDriveByFeature(image, collection, property, folder, name=None,
                     scale=1000, dataType="float", **kwargs):
    """ Export an image clipped by features (Polygons). You can use the
    same arguments as the original function ee.batch.export.image.toDrive

    :Parameters:
    :param image: image to clip
    :type image: ee.Image
    :param collection: feature collection
    :type collection: ee.FeatureCollection
    :param property: name of the property of the features to paste in
    the image
    :type property: str
    :param folder: same as ee.Export
    :type folder: str
    :param name: name (suffix) of the resulting image
    :type name: str
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
    featlist = collection.getInfo()["features"]
    if not name:
        iid = image.id().getInfo()
        if iid:
            name = iid.split("/")[-1]
        else:
            name = 'unknown_image'

    # convert data type
    image = utils.convertDataType(dataType)(image)

    def unpack(thelist):
        unpacked = []
        for i in thelist:
            unpacked.append(i[0])
            unpacked.append(i[1])
        return unpacked

    tasklist = []

    for f in featlist:
        geomlist = unpack(f["geometry"]["coordinates"][0])
        geom = ee.Geometry.Polygon(geomlist)

        feat = ee.Feature(geom)
        dis = f["properties"][property]

        if type(dis) is float:
            disS = str(int(dis))
        elif type(dis) is int:
            disS = str(dis)
        elif type(dis) is str:
            disS = dis
        else:
            print("unknown property's type")
            break

        finalname = "{0}_{1}_{2}".format(name, property, disS)

        task = ee.batch.Export.image.toDrive(
            image=image,
            description=finalname,
            folder=folder,
            fileNamePrefix=finalname,
            region=feat.geometry().bounds().getInfo()["coordinates"],
            scale=scale, **kwargs)

        task.start()
        print("exporting", finalname)
        tasklist.append(task)

    return tasklist