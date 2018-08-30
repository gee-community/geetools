# coding=utf-8
""" Module holding batch processing for Earth Engine """
import ee
import ee.data
from . import tools_image
import os

if not ee.data._initialized:
    ee.Initialize()


def recrusive_delete_asset(assetId):
    try:
        content = ee.data.getList({'id':assetId})
    except Exception as e:
        print(str(e))
        return

    if content == 0:
        # delete empty colletion and/or folder
        ee.data.deleteAsset(assetId)
    else:
        for asset in content:
            path = asset['id']
            ty = asset['type']
            if ty == 'Image':
                # print('deleting {}'.format(path))
                ee.data.deleteAsset(path)
            else:
                recrusive_delete_asset(path)
        # delete empty collection and/or folder
        ee.data.deleteAsset(assetId)


def convert_data_type(newtype):
    """ Convert an image to the specified data type

    :param newtype: the data type. One of 'float', 'int', 'byte', 'double',
        'Uint8','int8','Uint16', 'int16', 'Uint32','int32'
    :type newtype: str
    :return: a function to map over a collection
    :rtype: function
    """
    def wrap(image):
        TYPES = {'float': image.toFloat,
                 'int': image.toInt,
                 'byte': image.toByte,
                 'double': image.toDouble,
                 'Uint8': image.toUint8,
                 'int8': image.toInt8,
                 'Uint16': image.toUint16,
                 'int16': image.toInt16,
                 'Uint32': image.toUint32,
                 'int32': image.toInt32}
        return TYPES[newtype]()
    return wrap


def create_assets(asset_ids, asset_type, mk_parents):
    """Creates the specified assets if they do not exist.
    This is a fork of the original function in 'ee.data' module with the
    difference that

    - If the asset already exists but the type is different that the one we
      want, raise an error
    - Starts the creation of folders since 'user/username/'

    Will be here until I can pull requests to the original repo

    :param asset_ids: list of paths
    :type asset_ids: list
    :param asset_type: the type of the assets. Options: "ImageCollection" or
        "Folder"
    :type asset_type: str
    :param mk_parents: make the parents?
    :type mk_parents: bool
    :return: A description of the saved asset, including a generated ID

    """
    for asset_id in asset_ids:
        already = ee.data.getInfo(asset_id)
        if already:
            ty = already['type']
            if ty != asset_type:
                raise ValueError("{} is a {}. Can't create asset".format(asset_id, ty))
            print('Asset %s already exists' % asset_id)
            continue
        if mk_parents:
            parts = asset_id.split('/')
            root = "/".join(parts[:2])
            root += "/"
            for part in parts[2:-1]:
                root += part
                if ee.data.getInfo(root) is None:
                    ee.data.createAsset({'type': 'Folder'}, root)
                root += '/'
        return ee.data.createAsset({'type': asset_type}, asset_id)


def downloadFile(url, name, ext):
    """ Download a file from a given url

    :param url: full url
    :type url: str
    :param name: name for the file (can contain a path)
    :type name: str
    :param ext: extension for the file
    :type ext: str
    :return: the created file (closed)
    :rtype: file
    """
    import requests
    response = requests.get(url, stream=True)
    code = response.status_code

    while code != 200:
        if code == 400:
            return None
        response = requests.get(url, stream=True)
        code = response.status_code
        size = response.headers.get('content-length',0)
        if size: print('size:', size)

    with open(name + "." + ext, "wb") as handle:
        for data in response.iter_content():
            handle.write(data)

    return handle


class Image(object):

    @staticmethod
    def toLocal(image, name=None, path=None, scale=None, region=None,
                dimensions=None, toFolder=True, checkExist=True):
        """ Download an Image to your hard drive

        :param image: the image to download
        :type image: ee.Image
        :param path: the path to download the image. If None, it will be downloaded
            to the same folder as the script is
        :type path: str
        :param name: name of the file
        :type name: str
        :param scale: scale of the image to download. If None, tries to get it.
        :type scale: int
        :param region: region to from where to download the image. If None, will be
            the image region
        :type region: ee.Geometry
        :param
        """
        # TODO: checkExist
        # make some imports
        import glob
        from . import tools

        try:
            import zipfile
        except:
            raise ValueError(
                'zipfile module not found, install it using `pip install zipfile`')

        try:
            from osgeo import gdal
        except ImportError:
            try:
                import gdal
            except:
                raise

        # Reproject image
        # image = image.reproject(ee.Projection('EPSG:4326'))

        name = name if name else image.id().getInfo()

        scale = scale if scale else int(tools_image.minscale(image).getInfo())

        if region:
            region = tools.getRegion(region)
        else:
            region = tools.getRegion(image)

        params = {'region': region,
                  'scale': scale}

        params = params.update({'dimensions': dimensions}) if dimensions else params

        url = image.getDownloadURL(params)

        ext = 'zip'

        downloadFile(url, name, ext)

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

        # Merge TIFF
        # alltif = glob.glob(os.path.join(finalpath, '.tif'))
        # outvrt = '/vsimem/stacked.vrt' #/vsimem is special in-memory virtual "directory"
        # outtif = os.path.join(finalpath, name+'.tif')
        #
        # outds = gdal.BuildVRT(outvrt, alltif, separate=True)
        # gdal.Translate(outtif, outds)

    @staticmethod
    def toAsset(image, assetPath, name=None, to='Folder', scale=None,
                    region=None, create=True, dataType='float', **kwargs):
        """ This function can create folders and ImageCollections on the fly.
        The rest is the same to Export.image.toAsset. You can pass the same
        params as the original function

        :param image: the image to upload
        :type image: ee.Image
        :param assetPath: path to upload the image (only PATH, without filename)
        :type assetPath: str
        :param name: filename for the image (AssetID will be assetPath + name)
        :type name: str
        :param to: where to save the image. Options: 'Folder' or 'ImageCollection'
        :param region: area to upload. Defualt to the footprint of the first
            image in the collection
        :type region: ee.Geometry.Rectangle or ee.Feature
        :param scale: scale of the image (side of one pixel)
            (Landsat resolution)
        :type scale: int
        :param dataType: as downloaded images **must** have the same data type in all
            bands, you have to set it here. Can be one of: "float", "double", "int",
            "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
        :type dataType: str
        :return: the tasks
        :rtype: ee.batch.Task
        """
        from . import tools
        # Convert data type
        image = convert_data_type(dataType)(image)

        # Check if the user is specified in the asset path
        is_user = (assetPath.split('/')[0] == 'users')
        if not is_user:
            user = ee.batch.data.getAssetRoots()[0]['id']
            assetPath = "{}/{}".format(user, assetPath)

        # description = kwargs.get('description', image.id().getInfo())
        # Set scale
        scale = scale if scale else int(tools_image.minscale(image).getInfo())

        if create:
            # Recrusive create path
            path2create = assetPath #  '/'.join(assetPath.split('/')[:-1])
            create_assets([path2create], to, True)

        # Region
        region = tools.getRegion(region)
        # Name
        name = name if name else image.id().getInfo()
        # Asset ID (Path + name)
        assetId = '/'.join([assetPath, name])
        # Init task
        task = ee.batch.Export.image.toAsset(image, assetId=assetId,
                                             region=region, scale=scale,
                                             description=name,
                                             **kwargs)
        task.start()
        return task

    @staticmethod
    def toDriveByFeat(image, fc, prop, folder, scale=1000, dataType="float",
                     **kwargs):
        """ Export an image clipped by features (Polygons). You can use the
        same arguments as the original function ee.batch.export.image.toDrive

        :Parameters:
        :param image: image to clip
        :type image: ee.Image
        :param fc: feature collection
        :type fc: ee.FeatureCollection
        :param prop: name of the property of the features to paste in the image
        :type prop: str
        :param folder: same as ee.Export
        :type folder: str
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
        from . import tools

        featlist = fc.getInfo()["features"]
        name = image.getInfo()["id"].split("/")[-1]

        # convert data type
        convert_data_type(dataType)

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
            dis = f["properties"][prop]

            if type(dis) is float:
                disS = str(int(dis))
            elif type(dis) is int:
                disS = str(dis)
            elif type(dis) is str:
                disS = dis
            else:
                print("unknown property's type")
                break

            finalname = "{0}_{1}_{2}".format(name, prop, disS)

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


class Collection(object):

    @staticmethod
    def toDrive(col, folder, scale=30, dataType="float", region=None,
                **kwargs):
        """ Upload all images from one collection to Google Drive. You can use the
        same arguments as the original function ee.batch.export.image.toDrive

        :param col: Collection to upload
        :type col: ee.ImageCollection
        :param region: area to upload. Defualt to the footprint of the first
            image in the collection
        :type region: ee.Geometry.Rectangle or ee.Feature
        :param scale: scale of the image (side of one pixel). Defults to 30
            (Landsat resolution)
        :type scale: int
        :param maxImgs: maximum number of images inside the collection
        :type maxImgs: int
        :param dataType: as downloaded images **must** have the same data type in all
            bands, you have to set it here. Can be one of: "float", "double", "int",
            "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
        :type dataType: str
        :return: list of tasks
        :rtype: list
        """
        from . import tools
        size = col.size().getInfo()
        alist = col.toList(size)
        tasklist = []

        if region is None:
            region = ee.Image(alist.get(0)).geometry().getInfo()["coordinates"]
        else:
            region = tools.getRegion(region)

        for idx in range(0, size):
            img = alist.get(idx)
            img = ee.Image(img)
            name = img.id().getInfo().split("/")[-1]

            # convert data type
            convert_data_type(dataType)

            task = ee.batch.Export.image.toDrive(image=img,
                                                 description=name,
                                                 folder=folder,
                                                 fileNamePrefix=name,
                                                 region=region,
                                                 scale=scale, **kwargs)
            task.start()
            tasklist.append(task)

        return tasklist

    @staticmethod
    def toAsset(col, assetPath, scale=30, region=None, create=True, **kwargs):
        """ Upload all images from one collection to a Earth Engine Asset. You can
        use the same arguments as the original function ee.batch.export.image.toDrive

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
        :param dataType: as downloaded images **must** have the same data type in all
            bands, you have to set it here. Can be one of: "float", "double", "int",
            "Uint8", "Int8" or a casting function like *ee.Image.toFloat*
        :type dataType: str
        :return: list of tasks
        :rtype: list
        """
        from . import tools
        size = col.size().getInfo()
        alist = col.toList(size)
        tasklist = []

        if create:
            create_assets([assetPath], 'ImageCollection', True)

        if region is None:
            first_img = ee.Image(alist.get(0))
            region = tools.getRegion(first_img)
            # print(region)
            # region = ee.Image(alist.get(0)).geometry().getInfo()["coordinates"]
        else:
            region = tools.getRegion(region)

        for idx in range(0, size):
            img = alist.get(idx)
            img = ee.Image(img)
            name = img.id().getInfo().split("/")[-1]

            assetId = assetPath+"/"+name

            task = ee.batch.Export.image.toAsset(image=img,
                                                 assetId=assetId,
                                                 description=name,
                                                 region=region,
                                                 scale=scale, **kwargs)
            task.start()
            tasklist.append(task)

        return tasklist