Layout of the extensions
========================

Overview
--------

This section is a glossary of all the methods that are added to ``ee`` objects by the extension.
They are gathered by sections and link to the API reference for detailed examples but give a good overview of what can be done.

If you search for a method in the package, note that we decided to use names that are meaningful for python users so if you know what you are looking for in ``rasterio``, ``pandas`` or ``numpy`` you should be able to find it here under the same name.

.. warning::

    Method that were replaced during refactoring or that are still not reimplemented are not listed here.
    They remain fully accecible in the geetools package. If they raise a deprecation warning, it means that they are still available but will be removed in the future by their extension equivalent.

Earth Engine classes
--------------------

ee.Array
^^^^^^^^

constructor
###########
- :docstring:`ee.Array.geetools.full`


data manipulation
#################

- :docstring:`ee.Array.geetools.set`

ee.Authenticate
^^^^^^^^^^^^^^^

- :docstring:`ee.Authenticate.geetools.new_user`
- :docstring:`ee.Authenticate.geetools.delete_user`
- :docstring:`ee.Authenticate.geetools.list_user`
- :docstring:`ee.Authenticate.geetools.rename_user`


ee.ComputedObject
^^^^^^^^^^^^^^^^^

The ``ee.ComputedObject`` is the base object of all API object. The methods added here can thus be used in every object of the API.
That's also the only Object where the methods are directly added as members without the need to call `geetools` before.

Types management
################

- :docstring:`ee.ComputedObject.isInstance`

save json representations
#########################

- :docstring:`ee.ComputedObject.save`
- :docstring:`ee.ComputedObject.open`

ee.Date
^^^^^^^

Constructors
############

- :docstring:`ee.Date.geetools.fromEpoch`
- :docstring:`ee.Date.geetools.fromDOY`

Extra operations
################

- :docstring:`ee.Date.geetools.getUnitSinceEpoch`
- :docstring:`ee.Date.geetools.isLeap`

Exportation
###########

.. warning::

    As the snake case suggests, this method is client side.

- :docstring:`ee.Date.geetools.to_datetime`

helper
######

- :docstring:`ee.Date.geetools.check_unit`

ee.DateRange
^^^^^^^^^^^^

Extra operations
################

- :docstring:`ee.DateRange.geetools.split`

Helper
######

- :docstring:`ee.DateRange.geetools.check_unit`
- :docstring:`ee.DateRange.geetools.unitMillis`

ee.Dictionary
^^^^^^^^^^^^^

Constructors
############

- :docstring:`ee.Dictionary.geetools.fromPairs`

Extra operations
################

- :docstring:`ee.Dictionary.geetools.sort`
- :docstring:`ee.Dictionary.geetools.getMany`

ee.Feature
^^^^^^^^^^

- :docstring:`ee.Feature.geetools.toFeatureCollection`
- :docstring:`ee.Feature.geetools.removeProperties`

ee.FeatureCollection
^^^^^^^^^^^^^^^^^^^^

Properties management
#####################

- :docstring:`ee.FeatureCollection.geetools.addId`

Geometry management
###################

- :docstring:`ee.FeatureCollection.geetools.mergeGeometries`
- :docstring:`ee.FeatureCollection.geetools.toPolygons`

Converter
#########

- :docstring:`ee.FeatureCollection.geetools.toImage`
- :docstring:`ee.FeatureCollection.geetools.byFeatures`
- :docstring:`ee.FeatureCollection.geetools.byProperties`

Plotting
########

- :docstring:`ee.FeatureCollection.geetools.plot_by_features`
- :docstring:`ee.FeatureCollection.geetools.plot_by_properties`
- :docstring:`ee.FeatureCollection.geetools.plot_hist`

ee.Filter
^^^^^^^^^

- :docstring:`ee.Filter.geetools.dateRange`


ee.Geometry
^^^^^^^^^^^

- :docstring:`ee.Geometry.geetools.keepType`

ee.Image
^^^^^^^^

Constructor
###########

- :docstring:`ee.Image.geetools.full`
- :docstring:`ee.Image.geetools.fullLike`

Band manipulation
#################

- :docstring:`ee.Image.geetools.addDate`
- :docstring:`ee.Image.geetools.addSuffix`
- :docstring:`ee.Image.geetools.addPrefix`
- :docstring:`ee.Image.geetools.rename`
- :docstring:`ee.Image.geetools.remove`
- :docstring:`ee.Image.geetools.doyToDate`
- :docstring:`ee.Image.geetools.negativeClip`
- :docstring:`ee.Image.geetools.gauss`
- :docstring:`ee.Image.geetools.repeat`

Data extraction
###############

- :docstring:`ee.Image.geetools.getValues`
- :docstring:`ee.Image.geetools.minScale`
- :docstring:`ee.Image.geetools.reduceBands`
- :docstring:`ee.Image.geetools.format`
- :docstring:`ee.Image.geetools.index_list`
- :docstring:`ee.Image.geetools.spectralIndices`
- :docstring:`ee.Image.geetools.getScaleParams`
- :docstring:`ee.Image.geetools.getOffsetParams`
- :docstring:`ee.Image.geetools.getSTAC`
- :docstring:`ee.Image.geetools.getDOI`
- :docstring:`ee.Image.geetools.getCitation`


Data manipulation
#################

- :docstring:`ee.Image.geetools.doyToDate`
- :docstring:`ee.Image.geetools.clipOnCollection`
- :docstring:`ee.Image.geetools.bufferMask`
- :docstring:`ee.Image.geetools.removeZeros`
- :docstring:`ee.Image.geetools.interpolateBands`
- :docstring:`ee.Image.geetools.isletMask`
- :docstring:`ee.Image.geetools.scaleAndOffset`
- :docstring:`ee.Image.geetools.preprocess`
- :docstring:`ee.Image.geetools.panSharpen`
- :docstring:`ee.Image.geetools.tasseledCap`
- :docstring:`ee.Image.geetools.matchHistogram`
- :docstring:`ee.Image.geetools.maskClouds`

Converter
#########

- :docstring:`ee.Image.geetools.toGrid`

Properties
##########

- :docstring:`ee.Image.geetools.removeProperties`

ee.ImageCollection
^^^^^^^^^^^^^^^^^^

Data manipulation
#################

- :docstring:`ee.ImageCollection.geetools.maskClouds`
- :docstring:`ee.ImageCollection.geetools.closest`
- :docstring:`ee.ImageCollection.geetools.scaleAndOffset`
- :docstring:`ee.ImageCollection.geetools.preprocess`
- :docstring:`ee.ImageCollection.geetools.panSharpen`
- :docstring:`ee.ImageCollection.geetools.tasseledCap`
- :docstring:`ee.ImageCollection.geetools.append`
- :docstring:`ee.ImageCollection.geetools.outliers`

Data extraction
###############

- :docstring:`ee.ImageCollection.geetools.spectralIndices`
- :docstring:`ee.ImageCollection.geetools.getScaleParams`
- :docstring:`ee.ImageCollection.geetools.getOffsetParams`
- :docstring:`ee.ImageCollection.geetools.getDOI`
- :docstring:`ee.ImageCollection.geetools.getCitation`
- :docstring:`ee.ImageCollection.geetools.getSTAC`
-  :docstring:`ee.ImageCollection.geetools.collectionMask`
- :docstring:`ee.ImageCollection.geetools.iloc`
- :docstring:`ee.ImageCollection.geetools.integral`
- :docstring:`ee.ImageCollection.geetools.aggregateArray`
- :docstring:`ee.ImageCollection.geetools.validPixel`

Filter
######

- :docstring:`ee.ImageCollection.geetools.containsBandNames`
- :docstring:`ee.ImageCollection.geetools.containsAllBands`
- :docstring:`ee.ImageCollection.geetools.containsAnyBands`

Converter
#########

- :docstring:`ee.ImageCollection.geetools.to_xarray`

ee.Initialize
^^^^^^^^^^^^^

- :docstring:`ee.Initialize.geetools.from_user`
- :docstring:`ee.Initialize.geetools.project_id`

ee.Join
^^^^^^^

- :docstring:`ee.Join.geetools.byProperty`

ee.List
^^^^^^^

Constructor
###########

- :docstring:`ee.List.geetools.sequence`
- :docstring:`ee.List.geetools.zip`

operations
##########

- :docstring:`ee.List.geetools.product`
- :docstring:`ee.List.geetools.complement`
- :docstring:`ee.List.geetools.intersection`
- :docstring:`ee.List.geetools.union`
- :docstring:`ee.List.geetools.delete`
- :docstring:`ee.List.geetools.replaceMany`

Converter
#########

- :docstring:`ee.List.geetools.join`
- :docstring:`ee.List.geetools.toStrings`

ee.Number
^^^^^^^^^

- :docstring:`ee.Number.geetools.truncate`

ee.String
^^^^^^^^^

- :docstring:`ee.String.geetools.eq`
- :docstring:`ee.String.geetools.format`

Added classes
-------------

ee.Float
^^^^^^^^

.. note::

    This object does not exist in the original API. It is a custom Placeholder Float class to be used in the :py:meth:`ee.ComputedObject.isInstance` method.

ee.Integer
^^^^^^^^^^

.. note::

    This object does not exist in the original API. It is a custom Placeholder Float class to be used in the :py:meth:`ee.ComputedObject.isInstance` method.

ee.Asset
^^^^^^^^

.. note::

    This object is overriding most of the pathlib methods. We are simply gathering them here for convenience.

Constructor
###########

- :docstring:`ee.Asset.home`

Operation
#########

- :docstring:`ee.Asset.as_posix`
- :docstring:`ee.Asset.as_uri`
- :docstring:`ee.Asset.is_absolute`
- :docstring:`ee.Asset.is_user_project`
- :docstring:`ee.Asset.expanduser`
- :docstring:`ee.Asset.exists`
- :docstring:`ee.Asset.is_relative_to`
- :docstring:`ee.Asset.joinpath`
- :docstring:`ee.Asset.match`
- :docstring:`ee.Asset.with_name`
- :docstring:`ee.Asset.is_image`
- :docstring:`ee.Asset.is_image_collection`
- :docstring:`ee.Asset.is_feature_collection`
- :docstring:`ee.Asset.is_folder`
- :docstring:`ee.Asset.is_project`
- :docstring:`ee.Asset.is_type`
- :docstring:`ee.Asset.iterdir`
- :docstring:`ee.Asset.mkdir`
- :docstring:`ee.Asset.move`
- :docstring:`ee.Asset.rmdir`
- :docstring:`ee.Asset.unlink`
- :docstring:`ee.Asset.delete`
- :docstring:`ee.Asset.copy`
- :docstring:`ee.Asset.glob`
- :docstring:`ee.Asset.rglob`
- :docstring:`ee.Asset.setProperties`

Property
########

- :docstring:`ee.Asset.parts`
- :docstring:`ee.Asset.parent`
- :docstring:`ee.Asset.parents`
- :docstring:`ee.Asset.name`
- :docstring:`ee.Asset.st_size`
- :docstring:`ee.Asset.type`
- :docstring:`ee.Asset.owner`

