"""TODO missing docstring."""

import ee

from .. import tools
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

            name = makeName(img, namePattern, datePattern, extra)  # noqa: F821
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

            name = makeName(img, namePattern, datePattern, extra)  # noqa: F821
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
