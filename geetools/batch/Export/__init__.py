"""Toolbox for the ``ee.Export`` class."""
from __future__ import annotations

from typing import List, Optional

import ee

from geetools.accessors import register_class_accessor
from geetools.batch import utils


@register_class_accessor(ee.batch.Export, "geetools")
class ExportAccessor:
    """Toolbox for the ``ee.batch.Export`` class."""

    def __init__(self, obj: ee.batch.Export):
        """Initialize the ExportAccessor class."""
        self._obj = obj

    # this pattern is not pythonic but I mimic the content of the Export class from GEE
    # I know as a namespace it should be a module.
    class imagecollection:
        """A static class with methods to start imagecollection export tasks."""

        def __init__(self):
            """Forbids class instantiation."""
            raise AssertionError("This class cannot be instantiated.")

        @staticmethod
        def toAsset(
            imagecollection: ee.ImageCollection,
            index_property: str = "system:id",
            description: Optional[str] = None,
            assetId: Optional[str] = None,
            **kwargs,
        ) -> List[ee.batch.Task]:
            """Creates a task to export an EE ImageCollection to an EE Asset.

            The method will create the imagecollection asset beforehand and launching the task will
            Populate the said image collection with the exported images. Each image in the Collection
            Will be named using the index_property value of the image.
            If no asset Id is provided the asset will be created at the root of the current project assets.

            Parameters:
                imagecollection: The image collection to export.
                index_property: The property of the image to use as name. Default is "system:id".
                description: The description of the task.
                assetId: The asset id where to export the image collection.
                **kwargs: every paramet that you would use for a vanilla ee.batch.Export.image.toAsset

            Returns:
                The task created.

            Examples:
                .. code-block:: python

                    import ee
                    import geetools

                    ee.Initialize()

                    # create a test image collection
                    collection = ee.ImageCollection("COPERNICUS/S2").limit(5)

                    # export the collection
                    tasks = geetools.batch.Export.imagecollection.toAsset(collection, "system:index", "test export")
                ```
            """
            # sanity check on parameters
            description = description or ee.Asset(assetId).name
            assetId = ee.Asset(assetId) or ee.Asset("~").expanduser() / description

            # create the ImageCollection asset
            ee.data.createAsset({"type": "IMAGE_COLLECTION"}, assetId.as_posix())

            # loop over the collection and export each image
            nb_images = imagecollection.size().getInfo()
            imageList = imagecollection.toList(nb_images)
            task_list = []
            for i in range(nb_images):
                # extract image information
                locImage = ee.Image(imageList.get(i))
                loc_id = locImage.get(index_property).getInfo()

                # override the parameters related to the image itself
                kwargs["image"] = locImage
                kwargs["description"] = utils.format_description(f"{description}_{loc_id}")
                kwargs["assetId"] = (assetId / utils.format_asset_id(loc_id)).as_posix()

                # create the task
                task_list.append(ee.batch.Export.image.toAsset(**kwargs))

            return task_list
