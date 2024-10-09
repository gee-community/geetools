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

- :py:meth:`ee.Array.geetools.full <geetools.Array.ArrayAccessor.full>`: Create an array with the given dimensions, initialized to the given value. **Manually loaded**

data manipulation
#################

- :py:meth:`ee.Array.geetools.set <geetools.Array.ArrayAccessor.set>`: Set the value of a cell in an array. **Manually be loaded**

ee.Authenticate
^^^^^^^^^^^^^^^

- :py:meth:`ee.Authenticate.geetools.new_user <geetools.Authenticate.AuthenticateAccessor.new_user>`: :docstring:`geetools.AuthenticateAccessor.new_user`
- :py:meth:`ee.Authenticate.geetools.delete_user <geetools.Authenticate.AuthenticateAccessor.delete_user>`: :docstring:`geetools.AuthenticateAccessor.delete_user`
- :py:meth:`ee.Authenticate.geetools.list_user <geetools.Authenticate.AuthenticateAccessor.list_user>`: :docstring:`geetools.AuthenticateAccessor.list_user`
- :py:meth:`ee.Authenticate.geetools.rename_user <geetools.Authenticate.AuthenticateAccessor.rename_user>`: :docstring:`geetools.AuthenticateAccessor.rename_user`


ee.ComputedObject
^^^^^^^^^^^^^^^^^

The ``ee.ComputedObject`` is the base object of all API object. The methods added here can thus be used in every object of the API.
That's also the only Object where the methods are directly added as members without the need to call `geetools` before.

Types management
################

- :py:meth:`ee.ComputedObject.isInstance <geetools.ComputedObject.isInstance>`: :docstring:`geetools.ComputedObject.isInstance`

save json representations
#########################

- :py:meth:`ee.ComputedObject.save <geetools.ComputedObject.save>`: :docstring:`geetools.ComputedObject.save`
- :py:meth:`ee.ComputedObject.open <geetools.ComputedObject.open>`: :docstring:`geetools.ComputedObject.open`

ee.Date
^^^^^^^

Constructors
############

- :py:meth:`ee.Date.geetools.fromEpoch <geetools.Date.DateAccessor.fromEpoch>`: :docstring:`geetools.DateAccessor.fromEpoch`
- :py:meth:`ee.Date.geetools.fromDOY <geetools.Date.DateAccessor.fromDOY>`: :docstring:`geetools.DateAccessor.fromDOY`

Extra operations
################

- :py:meth:`ee.Date.geetools.getUnitSinceEpoch <geetools.Date.DateAccessor.getUnitSinceEpoch>`: :docstring:`geetools.DateAccessor.getUnitSinceEpoch`
- :py:meth:`ee.Date.geetools.isLeap <geetools.Date.DateAccessor.isLeap>`: :docstring:`geetools.DateAccessor.isLeap`

Exportation
###########

.. warning::

    As the snake case suggests, this method is client side.

- :py:meth:`ee.Date.geetools.to_datetime <geetools.Date.DateAccessor.to_datetime>`: :docstring:`geetools.DateAccessor.to_datetime`

helper
######

- :py:meth:`ee.Date.geetools.check_unit <geetools.Date.DateAccessor.check_unit>`: :docstring:`geetools.DateAccessor.check_unit`

ee.DateRange
^^^^^^^^^^^^

Extra operations
################

- :py:meth:`ee.DateRange.geetools.split <geetools.DateRange.DateRangeAccessor.split>`: Convert a ``ee.DateRange`` to a list of ``ee.DateRange``.`

Helper
######

- :py:meth:`ee.DateRange.geetools.check_unit <geetools.DateRange.DateRangeAccessor.check_unit>`: Check if the unit is valid.
- :py:meth:`ee.DateRange.geetools.unitMillis <geetools.DateRange.DateRangeAccessor.unitMillis>`: Get the milliseconds of a unit.

ee.Dictionary
^^^^^^^^^^^^^

Constructors
############

- :py:meth:`ee.Dictionary.geetools.fromPairs <geetools.Dictionary.DictionaryAccessor.fromPairs>`: :docstring:`geetools.DictionaryAccessor.fromPairs`

Extra operations
################

- :py:meth:`ee.Dictionary.geetools.sort <geetools.Dictionary.DictionaryAccessor.sort>`: :docstring:`geetools.DictionaryAccessor.sort`
- :py:meth:`ee.Dictionary.geetools.getMany <geetools.Dictionary.DictionaryAccessor.getMany>`: :docstring:`geetools.DictionaryAccessor.getMany`

ee.Feature
^^^^^^^^^^

- :py:meth:`ee.Feature.geetools.toFeatureCollection <geetools.Feature.FeatureAccessor.toFeatureCollection>`: :docstring:`geetools.FeatureAccessor.toFeatureCollection`
- :py:meth:`ee.Feature.geetools.removeProperties <geetools.Feature.FeatureAccessor.removeProperties>`: :docstring:`geetools.FeatureAccessor.removeProperties`

ee.FeatureCollection
^^^^^^^^^^^^^^^^^^^^

Properties management
#####################

- :py:meth:`ee.FeatureCollection.geetools.addId <geetools.FeatureCollection.FeatureCollectionAccessor.addId>`: :docstring:`geetools.FeatureCollectionAccessor.addId`

Geometry management
###################

- :py:meth:`ee.FeatureCollection.geetools.mergeGeometries <geetools.FeatureCollection.FeatureCollectionAccessor.mergeGeometries>`: :docstring:`geetools.FeatureCollectionAccessor.mergeGeometries`
- :py:meth:`ee.FeatureCollection.geetools.toPolygons <geetools.FeatureCollection.FeatureCollectionAccessor.toPolygons>`: :docstring:`geetools.FeatureCollectionAccessor.toPolygons`

Converter
#########

- :py:meth:`ee.FeatureCollection.geetools.toImage <geetools.FeatureCollection.FeatureCollectionAccessor.toImage>`: :docstring:`geetools.FeatureCollectionAccessor.toImage`
- :py:meth:`ee.FeatureCollection.geetools.byFeatures <geetools.FeatureCollection.FeatureCollectionAccessor.byFeatures>`: :docstring:`geetools.FeatureCollectionAccessor.byFeatures`
- :py:meth:`ee.FeatureCollection.geetools.byProperties <geetools.FeatureCollection.FeatureCollectionAccessor.byProperties>`: :docstring:`geetools.FeatureCollectionAccessor.byProperties`

Plotting
########

- :py:meth:`ee.FeatureCollection.geetools.plot_by_features <geetools.FeatureCollection.FeatureCollectionAccessor.plot_by_features>`: :docstring:`geetools.FeatureCollectionAccessor.plot_by_features`
- :py:meth:`ee.FeatureCollection.geetools.plot_by_properties <geetools.FeatureCollection.FeatureCollectionAccessor.plot_by_properties>`: :docstring:`geetools.FeatureCollectionAccessor.plot_by_properties`
- :py:meth:`ee.FeatureCollection.geetools.plot_hist <geetools.FeatureCollection.FeatureCollectionAccessor.plot_hist>`: :docstring:`geetools.FeatureCollectionAccessor.plot_hist`

ee.Filter
^^^^^^^^^

- :py:meth:`ee.Filter.geetools.dateRange <geetools.Filter.FilterAccessor.dateRange>`: :docstring:`geetools.FilterAccessor.dateRange`


ee.Geometry
^^^^^^^^^^^

- :py:meth:`ee.Geometry.geetools.keepType <geetools.Geometry.GeometryAccessor.keepType>`: :docstring:`geetools.GeometryAccessor.keepType`

ee.Image
^^^^^^^^

Constructor
###########

- :py:meth:`ee.Image.geetools.full <geetools.Image.ImageAccessor.full>`: :docstring:`geetools.ImageAccessor.full`
- :py:meth:`ee.Image.geetools.fullLike <geetools.Image.ImageAccessor.fullLike>`: :docstring:`geetools.ImageAccessor.fullLike`

Band manipulation
#################

- :py:meth:`ee.Image.geetools.addDate <geetools.Image.ImageAccessor.addDate>`: :docstring:`geetools.ImageAccessor.addDate`
- :py:meth:`ee.Image.geetools.addSuffix <geetools.Image.ImageAccessor.addSuffix>`: :docstring:`geetools.ImageAccessor.addSuffix`
- :py:meth:`ee.Image.geetools.addPrefix <geetools.Image.ImageAccessor.addPrefix>`: :docstring:`geetools.ImageAccessor.addPrefix`
- :py:meth:`ee.Image.geetools.rename <geetools.Image.ImageAccessor.rename>`: :docstring:`geetools.ImageAccessor.rename`
- :py:meth:`ee.Image.geetools.remove <geetools.Image.ImageAccessor.remove>`: :docstring:`geetools.ImageAccessor.remove`
- :py:meth:`ee.Image.geetools.doyToDate <geetools.Image.ImageAccessor.doyToDate>`: :docstring:`geetools.ImageAccessor.doyToDate`
- :py:meth:`ee.Image.geetools.negativeClip <geetools.Image.ImageAccessor.negativeClip>`: :docstring:`geetools.ImageAccessor.negativeClip`
- :py:meth:`ee.Image.geetools.gauss <geetools.Image.ImageAccessor.gauss>`: :docstring:`geetools.ImageAccessor.gauss`
- :py:meth:`ee.Image.geetools.repeat <geetools.Image.ImageAccessor.repeat>`: :docstring:`geetools.ImageAccessor.repeat`

Data extraction
###############

- :py:meth:`ee.Image.geetools.getValues <geetools.Image.ImageAccessor.getValues>`: :docstring:`geetools.ImageAccessor.getValues`
- :py:meth:`ee.Image.geetools.minScale <geetools.Image.ImageAccessor.minScale>`: :docstring:`geetools.ImageAccessor.minScale`
- :py:meth:`ee.Image.geetools.reduceBands <geetools.Image.ImageAccessor.reduceBands>`: :docstring:`geetools.ImageAccessor.reduceBands`
- :py:meth:`ee.Image.geetools.format <geetools.Image.ImageAccessor.format>`: :docstring:`geetools.ImageAccessor.format`
- :py:meth:`ee.Image.geetools.index_list <geetools.Image.ImageAccessor.index_list>`: :docstring:`geetools.ImageAccessor.index_list`
- :py:meth:`ee.Image.geetools.spectralIndices <geetools.Image.ImageAccessor.spectralIndices>`: :docstring:`geetools.ImageAccessor.spectralIndices`
- :py:meth:`ee.Image.geetools.getScaleParams <geetools.Image.ImageAccessor.getScaleParams>`: :docstring:`geetools.ImageAccessor.getScaleParams`
- :py:meth:`ee.Image.geetools.getOffsetParams <geetools.Image.ImageAccessor.getOffsetParams>`: :docstring:`geetools.ImageAccessor.getOffsetParams`
- :py:meth:`ee.Image.geetools.getSTAC <geetools.Image.ImageAccessor.getSTAC>`: :docstring:`geetools.ImageAccessor.getSTAC`
- :py:meth:`ee.Image.geetools.getDOI <geetools.Image.ImageAccessor.getDOI>`: :docstring:`geetools.ImageAccessor.getDOI`
- :py:meth:`ee.Image.geetools.getCitation <geetools.Image.ImageAccessor.getCitation>`: :docstring:`geetools.ImageAccessor.getCitation`


Data manipulation
#################

- :py:meth:`ee.Image.geetools.doyToDate <geetools.Image.ImageAccessor.doyToDate>`: :docstring:`geetools.ImageAccessor.doyToDate`
- :py:meth:`ee.Image.geetools.clipOnCollection <geetools.Image.ImageAccessor.clipOnCollection>`: :docstring:`geetools.ImageAccessor.clipOnCollection`
- :py:meth:`ee.Image.geetools.bufferMask <geetools.Image.ImageAccessor.bufferMask>`: :docstring:`geetools.ImageAccessor.bufferMask`
- :py:meth:`ee.Image.geetools.removeZeros <geetools.Image.ImageAccessor.removeZeros>`: :docstring:`geetools.ImageAccessor.removeZeros`
- :py:meth:`ee.Image.geetools.interpolateBands <geetools.Image.ImageAccessor.interpolateBands>`: :docstring:`geetools.ImageAccessor.interpolateBands`
- :py:meth:`ee.Image.geetools.isletMask <geetools.Image.ImageAccessor.isletMask>`: :docstring:`geetools.ImageAccessor.isletMask`
- :py:meth:`ee.Image.geetools.scaleAndOffset <geetools.Image.ImageAccessor.scaleAndOffset>`: :docstring:`geetools.ImageAccessor.scaleAndOffset`
- :py:meth:`ee.Image.geetools.preprocess <geetools.Image.ImageAccessor.preprocess>`: :docstring:`geetools.ImageAccessor.preprocess`
- :py:meth:`ee.Image.geetools.panSharpen <geetools.Image.ImageAccessor.panSharpen>`: :docstring:`geetools.ImageAccessor.panSharpen`
- :py:meth:`ee.Image.geetools.tasseledCap <geetools.Image.ImageAccessor.tasseledCap>`: :docstring:`geetools.ImageAccessor.tasseledCap`
- :py:meth:`ee.Image.geetools.matchHistogram <geetools.Image.ImageAccessor.matchHistogram>`: :docstring:`geetools.ImageAccessor.matchHistogram`
- :py:meth:`ee.Image.geetools.maskClouds <geetools.Image.ImageAccessor.maskClouds>`: :docstring:`geetools.ImageAccessor.maskClouds`

Converter
#########

- :py:meth:`ee.Image.geetools.toGrid <geetools.Image.ImageAccessor.toGrid>`: :docstring:`geetools.ImageAccessor.toGrid`

Properties
##########

- :py:meth:`ee.Image.geetools.removeProperties <geetools.Image.ImageAccessor.removeProperties>`: :docstring:`geetools.ImageAccessor.removeProperties`

ee.ImageCollection
^^^^^^^^^^^^^^^^^^

Data manipulation
#################

- :py:meth:`ee.ImageCollection.geetools.maskClouds <geetools.ImageCollection.ImageCollectionAccessor.maskClouds>`: :docstring:`geetools.ImageCollectionAccessor.maskClouds`
- :py:meth:`ee.ImageCollection.geetools.closest <geetools.ImageCollection.ImageCollectionAccessor.closest>`: :docstring:`geetools.ImageCollectionAccessor.closest`
- :py:meth:`ee.ImageCollection.geetools.scaleAndOffset <geetools.ImageCollection.ImageCollectionAccessor.scaleAndOffset>`: :docstring:`geetools.ImageCollectionAccessor.scaleAndOffset`
- :py:meth:`ee.ImageCollection.geetools.preprocess <geetools.ImageCollection.ImageCollectionAccessor.preprocess>`: :docstring:`geetools.ImageCollectionAccessor.preprocess`
- :py:meth:`ee.ImageCollection.geetools.panSharpen <geetools.ImageCollection.ImageCollectionAccessor.panSharpen>`: :docstring:`geetools.ImageCollectionAccessor.panSharpen`
- :py:meth:`ee.ImageCollection.geetools.tasseledCap <geetools.ImageCollection.ImageCollectionAccessor.tasseledCap>`: :docstring:`geetools.ImageCollectionAccessor.tasseledCap`
- :py:meth:`ee.ImageCollection.geetools.append <geetools.ImageCollection.ImageCollectionAccessor.append>`: :docstring:`geetools.ImageCollectionAccessor.append`
- :py:meth:`ee.ImageCollection.geetools.outliers <geetools.ImageCollection.ImageCollectionAccessor.outliers>`: :docstring:`geetools.ImageCollectionAccessor.outliers`

Data extraction
###############

- :py:meth:`ee.ImageCollection.geetools.spectralIndices <geetools.ImageCollection.ImageCollectionAccessor.spectralIndices>`: :docstring:`geetools.ImageCollectionAccessor.spectralIndices`
- :py:meth:`ee.ImageCollection.geetools.getScaleParams <geetools.ImageCollection.ImageCollectionAccessor.getScaleParams>`: :docstring:`geetools.ImageCollectionAccessor.getScaleParams`
- :py:meth:`ee.ImageCollection.geetools.getOffsetParams <geetools.ImageCollection.ImageCollectionAccessor.getOffsetParams>`: :docstring:`geetools.ImageCollectionAccessor.getOffsetParams`
- :py:meth:`ee.ImageCollection.geetools.getDOI <geetools.ImageCollection.ImageCollectionAccessor.getDOI>`: :docstring:`geetools.ImageCollectionAccessor.getDOI`
- :py:meth:`ee.ImageCollection.geetools.getCitation <geetools.ImageCollection.ImageCollectionAccessor.getCitation>`: :docstring:`geetools.ImageCollectionAccessor.getCitation`
- :py:meth:`ee.ImageCollection.geetools.getSTAC <geetools.ImageCollection.ImageCollectionAccessor.getSTAC>`: :docstring:`geetools.ImageCollectionAccessor.getSTAC`
-  :py:meth:`ee.ImageCollection.geetools.collectionMask <geetools.ImageCollection.ImageCollectionAccessor.collectionMask>`: :docstring:`geetools.ImageCollectionAccessor.collectionMask`
- :py:meth:`ee.ImageCollection.geetools.iloc <geetools.ImageCollection.ImageCollectionAccessor.iloc>`: :docstring:`geetools.ImageCollectionAccessor.iloc`
- :py:meth:`ee.ImageCollection.geetools.integral <geetools.ImageCollection.ImageCollectionAccessor.integral>`: :docstring:`geetools.ImageCollectionAccessor.integral`
- :py:meth:`ee.ImageCollection.geetools.aggregateArray <geetools.ImageCollection.ImageCollectionAccessor.aggregateArray>`: :docstring:`geetools.ImageCollectionAccessor.aggregateArray`
- :py:meth:`ee.ImageCollection.geetools.validPixel <geetools.ImageCollection.ImageCollectionAccessor.validPixel>`: :docstring:`geetools.ImageCollectionAccessor.validPixel`

Filter
######

- :py:meth:`ee.ImageCollection.geetools.containsBandNames <geetools.ImageCollection.ImageCollectionAccessor.containsBandNames>`: :docstring:`geetools.ImageCollectionAccessor.containsBandNames`
- :py:meth:`ee.ImageCollection.geetools.containsAllBands <geetools.ImageCollection.ImageCollectionAccessor.containsAllBands>`: :docstring:`geetools.ImageCollectionAccessor.containsAllBands`
- :py:meth:`ee.ImageCollection.geetools.containsAnyBands <geetools.ImageCollection.ImageCollectionAccessor.containsAnyBands>`: :docstring:`geetools.ImageCollectionAccessor.containsAnyBands`

Converter
#########

- :py:meth:`ee.ImageCollection.geetools.to_xarray <geetools.ImageCollection.ImageCollectionAccessor.to_xarray>`: :docstring:`geetools.ImageCollectionAccessor.to_xarray`

ee.Initialize
^^^^^^^^^^^^^

- :py:meth:`ee.Initialize.geetools.from_user <geetools.Initialize.InitializeAccessor.from_user>`: :docstring:`geetools.InitializeAccessor.from_user`
- :py:meth:`ee.Initialize.geetools.project_id <geetools.Initialize.InitializeAccessor.project_id>`: :docstring:`geetools.InitializeAccessor.project_id`

ee.Join
^^^^^^^

- :py:meth:`ee.Join.geetools.byProperty <geetools.Join.JoinAccessor.byProperty>`: :docstring:`geetools.JoinAccessor.byProperty`

ee.List
^^^^^^^

Constructor
###########

- :py:meth:`ee.List.geetools.sequence <geetools.List.ListAccessor.sequence>`: :docstring:`geetools.ListAccessor.sequence`
- :py:meth:`ee.List.geetools.zip <geetools.List.ListAccessor.zip>`: :docstring:`geetools.ListAccessor.zip`

operations
##########

- :py:meth:`ee.List.geetools.product <geetools.List.ListAccessor.product>`: :docstring:`geetools.ListAccessor.product`
- :py:meth:`ee.List.geetools.complement <geetools.List.ListAccessor.complement>`: :docstring:`geetools.ListAccessor.complement`
- :py:meth:`ee.List.geetools.intersection <geetools.List.ListAccessor.intersection>`: :docstring:`geetools.ListAccessor.intersection`
- :py:meth:`ee.List.geetools.union <geetools.List.ListAccessor.union>`: :docstring:`geetools.ListAccessor.union`
- :py:meth:`ee.List.geetools.delete <geetools.List.ListAccessor.delete>`: :docstring:`geetools.ListAccessor.delete`
- :py:meth:`ee.List.geetools.replaceMany <geetools.List.ListAccessor.replaceMany>`: :docstring:`geetools.ListAccessor.replaceMany`

Converter
#########

- :py:meth:`ee.List.geetools.join <geetools.List.ListAccessor.join>`: :docstring:`geetools.ListAccessor.join`
- :py:meth:`ee.List.geetools.toStrings <geetools.List.ListAccessor.toStrings>`: :docstring:`geetools.ListAccessor.toStrings`

ee.Number
^^^^^^^^^

- :py:meth:`ee.Number.geetools.truncate <geetools.Number.NumberAccessor.truncate>`: :docstring:`geetools.NumberAccessor.truncate`

ee.String
^^^^^^^^^

- :py:meth:`ee.String.geetools.eq <geetools.String.StringAccessor.eq>`: :docstring:`geetools.StringAccessor.eq`
- :py:meth:`ee.String.geetools.format <geetools.String.StringAccessor.format>`: :docstring:`geetools.StringAccessor.format`

Added classes
-------------

ee.Float
^^^^^^^^

.. note::

    This object does not exist in the original API. It is a custom Placeholder Float class to be used in the :py:meth:`ee.ComputedObject.isInstance <geetools.ComputedObjectAccessor.isInstance>` method.

ee.Integer
^^^^^^^^^^

.. note::

    This object does not exist in the original API. It is a custom Placeholder Float class to be used in the :py:meth:`ee.ComputedObject.isInstance <geetools.ComputedObjectAccessor.isInstance>` method.

ee.Asset
^^^^^^^^

.. note::

    This object is overriding most of the pathlib methods. We are simply gathering them here for convenience.

Constructor
###########

- :py:meth:`ee.Asset.home <geetools.Asset.Asset.home>`: :docstring:`geetools.Asset.home`

Operation
#########

- :py:meth:`ee.Asset.as_posix <geetools.Asset.Asset.as_posix>`: :docstring:`geetools.Asset.as_posix`
- :py:meth:`ee.Asset.as_uri <geetools.Asset.Asset.as_uri>`: :docstring:`geetools.Asset.as_uri`
- :py:meth:`ee.Asset.is_absolute <geetools.Asset.Asset.is_absolute>`: :docstring:`geetools.Asset.is_absolute`
- :py:meth:`ee.Asset.is_user_project <geetools.Asset.Asset.is_user_project>`: :docstring:`geetools.Asset.is_user_project`
- :py:meth:`ee.Asset.expanduser <geetools.Asset.Asset.expanduser>`: :docstring:`geetools.Asset.expanduser`
- :py:meth:`ee.Asset.exists <geetools.Asset.Asset.exists>`: :docstring:`geetools.Asset.exists`
- :py:meth:`ee.Asset.is_relative_to <geetools.Asset.Asset.is_relative_to>`: :docstring:`geetools.Asset.is_relative_to`
- :py:meth:`ee.Asset.joinpath <geetools.Asset.Asset.joinpath>`: :docstring:`geetools.Asset.joinpath`
- :py:meth:`ee.Asset.match <geetools.Asset.Asset.match>`: :docstring:`geetools.Asset.match`
- :py:meth:`ee.Asset.with_name <geetools.Asset.Asset.with_name>`: :docstring:`geetools.Asset.with_name`
- :py:meth:`ee.Asset.is_image <geetools.Asset.Asset.is_image>`: :docstring:`geetools.Asset.is_image`
- :py:meth:`ee.Asset.is_image_collection <geetools.Asset.Asset.is_image_collection>`: :docstring:`geetools.Asset.is_image_collection`
- :py:meth:`ee.Asset.is_feature_collection <geetools.Asset.Asset.is_feature_collection>`: :docstring:`geetools.Asset.is_feature_collection`
- :py:meth:`ee.Asset.is_folder <geetools.Asset.Asset.is_folder>`: :docstring:`geetools.Asset.is_folder`
- :py:meth:`ee.Asset.is_project <geetools.Asset.Asset.is_project>`: :docstring:`geetools.Asset.is_project`
- :py:meth:`ee.Asset.is_type <geetools.Asset.Asset.is_type>`: :docstring:`geetools.Asset.is_type`
- :py:meth:`ee.Asset.iterdir <geetools.Asset.Asset.iterdir>`: :docstring:`geetools.Asset.iterdir`
- :py:meth:`ee.Asset.mkdir <geetools.Asset.Asset.mkdir>`: :docstring:`geetools.Asset.mkdir`
- :py:meth:`ee.Asset.move <geetools.Asset.Asset.move>`: :docstring:`geetools.Asset.move`
- :py:meth:`ee.Asset.rmdir <geetools.Asset.Asset.rmdir>`: :docstring:`geetools.Asset.rmdir`
- :py:meth:`ee.Asset.unlink <geetools.Asset.Asset.unlink>`: :docstring:`geetools.Asset.unlink`
- :py:meth:`ee.Asset.delete <geetools.Asset.Asset.delete>`: :docstring:`geetools.Asset.delete`
- :py:meth:`ee.Asset.copy <geetools.Asset.Asset.copy>`: :docstring:`geetools.Asset.copy`
- :py:meth:`ee.Asset.glob <geetools.Asset.Asset.glob>`: :docstring:`geetools.Asset.glob`
- :py:meth:`ee.Asset.rglob <geetools.Asset.Asset.rglob>`: :docstring:`geetools.Asset.rglob`
- :py:meth:`ee.Asset.setProperties <geetools.Asset.Asset.setProperties>`: :docstring:`geetools.Asset.setProperties`

Property
########

- :py:meth:`ee.Asset.parts <geetools.Asset.Asset.parts>`: :docstring:`geetools.Asset.parts`
- :py:meth:`ee.Asset.parent <geetools.Asset.Asset.parent>`: :docstring:`geetools.Asset.parent`
- :py:meth:`ee.Asset.parents <geetools.Asset.Asset.parents>`: :docstring:`geetools.Asset.parents`
- :py:meth:`ee.Asset.name <geetools.Asset.Asset.name>`: :docstring:`geetools.Asset.name`
- :py:meth:`ee.Asset.st_size <geetools.Asset.Asset.st_size>`: :docstring:`geetools.Asset.st_size`
- :py:meth:`ee.Asset.type <geetools.Asset.Asset.type>`: :docstring:`geetools.Asset.type`
- :py:meth:`ee.Asset.owner <geetools.Asset.Asset.owner>`: :docstring:`geetools.Asset.owner`

