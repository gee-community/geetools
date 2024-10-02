"""Missing docstring."""
import ee

from . import featurecollection, imagecollection
from . import image as batchimage


class Export(ee.batch.Export):
    """Missing docstring."""

    class imagecollection(object):
        """TODO missing docstring."""

        toDrive = imagecollection.toDrive
        toAsset = imagecollection.toAsset
        toCloudStorage = imagecollection.toCloudStorage

    class image(ee.batch.Export.image):
        """TODO missing docstring."""

        toAsset = batchimage.toAsset  # overwrite original
        toDriveByFeature = batchimage.toDriveByFeature


class Download(object):
    """TODO missing docstring."""

    class table(object):
        """TODO missing docstring."""

        toLocal = featurecollection.toLocal

    class image(object):
        """TODO missing docstring."""

        toLocal = batchimage.toLocal


class Import(object):
    """TODO missing docstring."""

    class table(object):
        """TODO missing docstring."""

        fromGeoJSON = featurecollection.fromGeoJSON
        fromShapefile = featurecollection.fromShapefile
        fromKML = featurecollection.fromKML
