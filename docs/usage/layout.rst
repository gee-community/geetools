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

As reported in https://github.com/gee-community/gee_tools/issues/173, this object cannot be extended before the API of Earth Enfine is initialized. So to use the following methods, you will be forced to manually import the following:

.. code-block:: python

    from geetools.Array import Array

constructor
###########

- :py:meth:`ee.Array.geetools.full <geetools.Array.Array.full>`: Create an array with the given dimensions, initialized to the given value. **Manually loaded**

data manipulation
#################

- :py:meth:`ee.Array.geetools.set <geetools.Array.Array.set>`: Set the value of a cell in an array. **Manually be loaded**

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

- :py:meth:`ee.Date.geetools.fromEpoch <geetools.Date.Date.fromEpoch>`: :docstring:`geetools.Date.fromEpoch`
- :py:meth:`ee.Date.geetools.fromDOY <geetools.Date.Date.fromDOY>`: :docstring:`geetools.Date.fromDOY`

Extra operations
################

- :py:meth:`ee.Date.geetools.getUnitSinceEpoch <geetools.Date.Date.getUnitSinceEpoch>`: :docstring:`geetools.Date.getUnitSinceEpoch`
- :py:meth:`ee.Date.geetools.isLeap <geetools.Date.Date.isLeap>`: :docstring:`geetools.Date.isLeap`

Exportation
###########

.. warning::

    As the snake case suggests, this method is client side.

- :py:meth:`ee.Date.geetools.to_datetime <geetools.Date.Date.to_datetime>`: :docstring:`geetools.Date.to_datetime`

helper
######

- :py:meth:`ee.Date.geetools.check_unit <geetools.Date.Date.check_unit>`: :docstring:`geetools.Date.check_unit`

ee.DateRange
^^^^^^^^^^^^

Extra operations
################

- :py:meth:`ee.DateRange.geetools.getRange <geetools.DateRange.DateRange.split>`: :docstring:`geetools.DateRange.split`

Helper
######

- :py:meth:`ee.DateRange.geetools.check_unit <geetools.DateRange.DateRange.check_unit>`: :docstring:`geetools.DateRange.check_unit`
- :py:meth:`ee.DateRange.geetools.unitMillis <geetools.DateRange.DateRange.unitMillis>`: :docstring:`geetools.DateRange.unitMillis`

ee.Dictionary
^^^^^^^^^^^^^

Constructors
############

- :py:meth:`ee.Dictionary.geetools.fromPairs <geetools.Dictionary.Dictionary.fromPairs>`: :docstring:`geetools.Dictionary.fromPairs`

Extra operations
################

- :py:meth:`ee.Dictionary.geetools.sort <geetools.Dictionary.Dictionary.sort>`: :docstring:`geetools.Dictionary.sort`
- :py:meth:`ee.Dictionary.geetools.getMany <geetools.Dictionary.Dictionary.getMany>`: :docstring:`geetools.Dictionary.getMany`

Feature
^^^^^^^

- :py:meth:`ee.Feature.geetools.toFeatureCollection <geetools.Feature.Feature.toFeatureCollection>`: :docstring:`geetools.Feature.toFeatureCollection`

FeatureCollection
^^^^^^^^^^^^^^^^^

Properties management
#####################

- :py:meth:`ee.FeatureCollection.geetools.addId <geetools.FeatureCollection.FeatureCollection.addId>`: :docstring:`geetools.FeatureCollection.addId`

Geometry management
###################

- :py:meth:`ee.FeatureCollection.geetools.mergeGeometries <geetools.FeatureCollection.FeatureCollection.mergeGeometries>`: :docstring:`geetools.FeatureCollection.mergeGeometries`
- :py:meth:`ee.FeatureCollection.geetools.toPolygons <geetools.FeatureCollection.FeatureCollection.toPolygons>`: :docstring:`geetools.FeatureCollection.toPolygons`

Converter
#########

- :py:meth:`ee.FeatureCollection.geetools.toImage <geetools.FeatureCollection.FeatureCollection.toImage>`: :docstring:`geetools.FeatureCollection.toImage`

ee.Filter
^^^^^^^^^

- :py:meth:`ee.Filter.geetools.dateRange <geetools.Filter.Filter.dateRange>`: :docstring:`geetools.Filter.dateRange`


ee.Geometry
^^^^^^^^^^^

- :py:meth:`ee.Geometry.geetools.keepType <geetools.Geometry.Geometry.keepType>`: :docstring:`geetools.Geometry.keepType`

ee.Image
^^^^^^^^

Constructor
###########

- :py:meth:`ee.Image.geetools.full <geetools.Image.Image.full>`: :docstring:`geetools.Image.full`
- :py:meth:`ee.Image.geetools.fullLike <geetools.Image.Image.fullLike>`: :docstring:`geetools.Image.fullLike`

Band manipulation
#################

- :py:meth:`ee.Image.geetools.addDate <geetools.Image.Image.addDate>`: :docstring:`geetools.Image.addDate`
- :py:meth:`ee.Image.geetools.addSuffix <geetools.Image.Image.addSuffix>`: :docstring:`geetools.Image.addSuffix`
- :py:meth:`ee.Image.geetools.addPrefix <geetools.Image.Image.addPrefix>`: :docstring:`geetools.Image.addPrefix`
- :py:meth:`ee.Image.geetools.rename <geetools.Image.Image.rename>`: :docstring:`geetools.Image.rename`
- :py:meth:`ee.Image.geetools.remove <geetools.Image.Image.remove>`: :docstring:`geetools.Image.remove`
- :py:meth:`ee.Image.geetools.doyToDate <geetools.Image.Image.doyToDate>`: :docstring:`geetools.Image.doyToDate`
- :py:meth:`ee.Image.geetools.negativeClip <geetools.Image.Image.negativeClip>`: :docstring:`geetools.Image.negativeClip`
- :py:meth:`ee.Image.geetools.gauss <geetools.Image.Image.gauss>`: :docstring:`geetools.Image.gauss`
- :py:meth:`ee.Image.geetools.repeat <geetools.Image.Image.repeat>`: :docstring:`geetools.Image.repeat`

Data extraction
###############

- :py:meth:`ee.Image.geetools.getValues <geetools.Image.Image.getValues>`: :docstring:`geetools.Image.getValues`
- :py:meth:`ee.Image.geetools.minScale <geetools.Image.Image.minScale>`: :docstring:`geetools.Image.minScale`
- :py:meth:`ee.Image.geetools.reduceBands <geetools.Image.Image.reduceBands>`: :docstring:`geetools.Image.reduceBands`
- :py:meth:`ee.Image.geetools.format <geetools.Image.Image.format>`: :docstring:`geetools.Image.format`
- :py:meth:`ee.Image.geetools.index_list <geetools.Image.Image.index_list>`: :docstring:`geetools.Image.index_list`
- :py:meth:`ee.Image.geetools.spectralIndices <geetools.Image.Image.spectralIndices>`: :docstring:`geetools.Image.spectralIndices`
- :py:meth:`ee.Image.geetools.getScaleParams <geetools.Image.Image.getScaleParams>`: :docstring:`geetools.Image.getScaleParams`
- :py:meth:`ee.Image.geetools.getOffsetParams <geetools.Image.Image.getOffsetParams>`: :docstring:`geetools.Image.getOffsetParams`
- :py:meth:`ee.Image.geetools.getSTAC <geetools.Image.Image.getSTAC>`: :docstring:`geetools.Image.getSTAC`
- :py:meth:`ee.Image.geetools.getDOI <geetools.Image.Image.getDOI>`: :docstring:`geetools.Image.getDOI`
- :py:meth:`ee.Image.geetools.getCitation <geetools.Image.Image.getCitation>`: :docstring:`geetools.Image.getCitation`


Data manipulation
#################

- :py:meth:`ee.Image.geetools.doyToDate <geetools.Image.Image.doyToDate>`: :docstring:`geetools.Image.doyToDate`
- :py:meth:`ee.Image.geetools.clipOnCollection <geetools.Image.Image.clipOnCollection>`: :docstring:`geetools.Image.clipOnCollection`
- :py:meth:`ee.Image.geetools.bufferMask <geetools.Image.Image.bufferMask>`: :docstring:`geetools.Image.bufferMask`
- :py:meth:`ee.Image.geetools.removeZeros <geetools.Image.Image.removeZeros>`: :docstring:`geetools.Image.removeZeros`
- :py:meth:`ee.Image.geetools.interpolateBands <geetools.Image.Image.interpolateBands>`: :docstring:`geetools.Image.interpolateBands`
- :py:meth:`ee.Image.geetools.isletMask <geetools.Image.Image.isletMask>`: :docstring:`geetools.Image.isletMask`
- :py:meth:`ee.Image.geetools.scaleAndOffset <geetools.Image.Image.scaleAndOffset>`: :docstring:`geetools.Image.scaleAndOffset`
- :py:meth:`ee.Image.geetools.preprocess <geetools.Image.Image.preprocess>`: :docstring:`geetools.Image.preprocess`
- :py:meth:`ee.Image.geetools.panSharpen <geetools.Image.Image.panSharpen>`: :docstring:`geetools.Image.panSharpen`
- :py:meth:`ee.Image.geetools.tasseledCap <geetools.Image.Image.tasseledCap>`: :docstring:`geetools.Image.tasseledCap`
- :py:meth:`ee.Image.geetools.matchHistogram <geetools.Image.Image.matchHistogram>`: :docstring:`geetools.Image.matchHistogram`
- :py:meth:`ee.Image.geetools.maskClouds <geetools.Image.Image.maskClouds>`: :docstring:`geetools.Image.maskClouds`

Converter
#########

- :py:meth:`ee.Image.geetools.toGrid <geetools.Image.Image.toGrid>`: :docstring:`geetools.Image.toGrid`

ee.ImageCollection
^^^^^^^^^^^^^^^^^^

Data manipulation
#################

- :py:meth:`ee.ImageCollection.geetools.maskClouds <geetools.ImageCollection.ImageCollection.maskClouds>`: :docstring:`geetools.ImageCollection.maskClouds`
- :py:meth:`ee.ImageCollection.geetools.closest <geetools.ImageCollection.ImageCollection.closest>`: :docstring:`geetools.ImageCollection.closest`
- :py:meth:`ee.ImageCollection.geetools.scaleAndOffset <geetools.ImageCollection.ImageCollection.scaleAndOffset>`: :docstring:`geetools.ImageCollection.scaleAndOffset`
- :py:meth:`ee.ImageCollection.geetools.preprocess <geetools.ImageCollection.ImageCollection.preprocess>`: :docstring:`geetools.ImageCollection.preprocess`
- :py:meth:`ee.ImageCollection.geetools.panSharpen <geetools.ImageCollection.ImageCollection.panSharpen>`: :docstring:`geetools.ImageCollection.panSharpen`
- :py:meth:`ee.ImageCollection.geetools.tasseledCap <geetools.ImageCollection.ImageCollection.tasseledCap>`: :docstring:`geetools.ImageCollection.tasseledCap`
- :py:meth:`ee.ImageCollection.geetools.append <geetools.ImageCollection.ImageCollection.append>`: :docstring:`geetools.ImageCollection.append`
- :py:meth:`ee.ImageCollection.geetools.outliers <geetools.ImageCollection.ImageCollection.outliers>`: :docstring:`geetools.ImageCollection.outliers`

Data extraction
###############

- :py:meth:`ee.ImageCollection.geetools.spectralIndices <geetools.ImageCollection.ImageCollection.spectralIndices>`: :docstring:`geetools.ImageCollection.spectralIndices`
- :py:meth:`ee.ImageCollection.geetools.getScaleParams <geetools.ImageCollection.ImageCollection.getScaleParams>`: :docstring:`geetools.ImageCollection.getScaleParams`
- :py:meth:`ee.ImageCollection.geetools.getOffsetParams <geetools.ImageCollection.ImageCollection.getOffsetParams>`: :docstring:`geetools.ImageCollection.getOffsetParams`
- :py:meth:`ee.ImageCollection.geetools.getDOI <geetools.ImageCollection.ImageCollection.getDOI>`: :docstring:`geetools.ImageCollection.getDOI`
- :py:meth:`ee.ImageCollection.geetools.getCitation <geetools.ImageCollection.ImageCollection.getCitation>`: :docstring:`geetools.ImageCollection.getCitation`
- :py:meth:`ee.ImageCollection.geetools.getSTAC <geetools.ImageCollection.ImageCollection.getSTAC>`: :docstring:`geetools.ImageCollection.getSTAC`
-  :py:meth:`ee.ImageCollection.geetools.collectionMask <geetools.ImageCollection.ImageCollection.collectionMask>`: :docstring:`geetools.ImageCollection.collectionMask`
- :py:meth:`ee.ImageCollection.geetools.iloc <geetools.ImageCollection.ImageCollection.iloc>`: :docstring:`geetools.ImageCollection.iloc`
- :py:meth:`ee.ImageCollection.geetools.integral <geetools.ImageCollection.ImageCollection.integral>`: :docstring:`geetools.ImageCollection.integral`

ee.Join
^^^^^^^

- :py:meth:`ee.Join.geetools.byProperty <geetools.Join.Join.byProperty>`: :docstring:`geetools.Join.byProperty`

ee.List
^^^^^^^

Constructor
###########

- :py:meth:`ee.List.geetools.sequence <geetools.List.List.sequence>`: :docstring:`geetools.List.sequence`
- :py:meth:`ee.List.geetools.zip <geetools.List.List.zip>`: :docstring:`geetools.List.zip`

operations
##########

- :py:meth:`ee.List.geetools.product <geetools.List.List.product>`: :docstring:`geetools.List.product`
- :py:meth:`ee.List.geetools.complement <geetools.List.List.complement>`: :docstring:`geetools.List.complement`
- :py:meth:`ee.List.geetools.intersection <geetools.List.List.intersection>`: :docstring:`geetools.List.intersection`
- :py:meth:`ee.List.geetools.union <geetools.List.List.union>`: :docstring:`geetools.List.union`
- :py:meth:`ee.List.geetools.delete <geetools.List.List.delete>`: :docstring:`geetools.List.delete`
- :py:meth:`ee.List.geetools.replaceMany <geetools.List.List.replaceMany>`: :docstring:`geetools.List.replaceMany`

Converter
#########

- :py:meth:`ee.List.geetools.join <geetools.List.List.join>`: :docstring:`geetools.List.join`
- :py:meth:`ee.List.geetools.toStrings <geetools.List.List.toStrings>`: :docstring:`geetools.List.toStrings`

ee.Number
^^^^^^^^^

- :py:meth:`ee.Number.geetools.truncate <geetools.Number.Number.truncate>`: :docstring:`geetools.Number.truncate`

ee.String
^^^^^^^^^

- :py:meth:`ee.String.geetools.eq <geetools.String.String.eq>`: :docstring:`geetools.String.eq`
- :py:meth:`ee.String.geetools.format <geetools.String.String.format>`: :docstring:`geetools.String.format`

Added classes
-------------

ee.Float
^^^^^^^^

.. note::

    This object does not exist in the original API. It is a custom Placeholder Float class to be used in the :py:meth:`ee.ComputedObject.isInstance <geetools.ComputedObject.isInstance>` method.

ee.Integer
^^^^^^^^^^

.. note::

    This object does not exist in the original API. It is a custom Placeholder Float class to be used in the :py:meth:`ee.ComputedObject.isInstance <geetools.ComputedObject.isInstance>` method.


