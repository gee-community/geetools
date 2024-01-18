"""Missing docstring."""
import ee

from . import featurecollection, imagecollection
from . import image as batchimage


class Export(ee.batch.Export):
    """Missing docstring."""

    class table(ee.batch.Export.table):
        """TODO missing docstring."""

        toAsset = featurecollection.toAsset
        toDriveShapefile = featurecollection.toDriveShapefile

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

        toGeoJSON = featurecollection.toGeoJSON
        toCSV = featurecollection.toCSV
        toLocal = featurecollection.toLocal

    class imagecollection(object):
        """TODO missing docstring."""

        toQGIS = imagecollection.toQGIS

    class image(object):
        """TODO missing docstring."""

        toLocal = batchimage.toLocal
        toQGIS = batchimage.toQGIS


class Convert(object):
    """TODO missing docstring."""

    class table(object):
        """TODO missing docstring."""

        toDict = featurecollection.toDict

    class imagecollection(object):
        """TODO missing docstring."""

        pass

    class image(object):
        """TODO missing docstring."""

        pass


class Import(object):
    """TODO missing docstring."""

    class table(object):
        """TODO missing docstring."""

        fromGeoJSON = featurecollection.fromGeoJSON
        fromShapefile = featurecollection.fromShapefile
        fromKML = featurecollection.fromKML

    class imagecollection(object):
        """TODO missing docstring."""

        pass

    class image(object):
        """TODO missing docstring."""

        pass
