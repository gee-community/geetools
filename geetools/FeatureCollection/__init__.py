"""Toolbox for the `ee.FeatureCollection` class."""
from __future__ import annotations

import json
from typing import Tuple, Union

import ee
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from geetools.accessors import register_class_accessor
from geetools.types import ee_int, ee_list, ee_str


@register_class_accessor(ee.FeatureCollection, "geetools")
class FeatureCollectionAccessor:
    """Toolbox for the `ee.FeatureCollection` class."""

    def __init__(self, obj: ee.FeatureCollection):
        """Initialize the FeatureCollection class."""
        self._obj = obj

    def toImage(
        self,
        color: Union[ee_str, ee_int] = 0,
        width: Union[ee_str, ee_int] = "",
    ) -> ee.Image:
        """Paint the current FeatureCollection to an Image.

        It's simply a wrapper on Image.paint() method

        Args:
            color: The pixel value to paint into every band of the input image, either as a number which will be used for all features, or the name of a numeric property to take from each feature in the collection.
            width: Line width, either as a number which will be the line width for all geometries, or the name of a numeric property to take from each feature in the collection. If unspecified, the geometries will be filled instead of outlined.
        """
        params = {"color": color}
        width == "" or params.update(width=width)
        return ee.Image().paint(self._obj, **params)

    def addId(self, name: ee_str = "id", start: ee_int = 1) -> ee.FeatureCollection:
        """Add a unique numeric identifier, starting from parameter ``start``.

        Returns:
            The parsed collection with a new id property

        Example:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                fc = ee.FeatureCollection('FAO/GAUL/2015/level0')
                fc = fc.geetools.addId()
                print(fc.first().get('id').getInfo())
        """
        start, name = ee.Number(start).toInt(), ee.String(name)

        indexes = ee.List(self._obj.aggregate_array("system:index"))
        ids = ee.List.sequence(start, start.add(self._obj.size()).subtract(1))
        idByIndex = ee.Dictionary.fromLists(indexes, ids)
        return self._obj.map(lambda f: f.set(name, idByIndex.get(f.get("system:index"))))

    def mergeGeometries(self) -> ee.Geometry:
        """Merge the geometries the included features.

        Returns:
            the dissolved geometry

        Example:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                fc = ee.FeatureCollection("FAO/GAUL/2015/level0")
                fc =fc.filter(ee.Filter.inList("ADM0_CODE", [122, 237, 85]))
                geom = fc.geetools.mergeGeometries()
                print(geom.getInfo())
        """
        first = self._obj.first().geometry()
        union = self._obj.iterate(lambda f, g: f.geometry().union(g), first)
        return ee.Geometry(union).dissolve()

    def toPolygons(self) -> ee.FeatureCollection:
        """Drop any geometry that is not a Polygon or a multipolygon.

        This method is made to avoid errors when performing zonal statistics and/or other surfaces operations. These operations won't work on geometries that are Lines or points. The methods remove these geometry types from GEometryCollections and rremove features that don't have any polygon geometry

        Returns:
            The parsed collection with only polygon/MultiPolygon geometries

        Example:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                point0 = ee.Geometry.Point([0,0], proj="EPSG:4326")
                point1 = ee.Geometry.Point([0,1], proj="EPSG:4326")
                poly0 = point0.buffer(1, proj="EPSG:4326")
                poly1 = point1.buffer(1, proj="EPSG:4326").bounds(proj="EPSG:4326")
                line = ee.Geometry.LineString([point1, point0], proj="EPSG:4326")
                multiPoly = ee.Geometry.MultiPolygon([poly0, poly1], proj="EPSG:4326")
                geometryCol = ee.Algorithms.GeometryConstructors.MultiGeometry([multiPoly, poly0, poly1, point0, line], crs="EPSG:4326", geodesic=True, maxError=1)

                fc = ee.FeatureCollection([geometryCol])
                fc = fc.geetools.toPolygons()
                print(fc.getInfo())
        """

        def filterGeom(geom):
            geom = ee.Geometry(geom)
            return ee.Algorithms.If(geom.type().compareTo("Polygon"), None, geom)

        def removeNonPoly(feat):
            filteredGeoms = feat.geometry().geometries().map(filterGeom, True)
            proj = feat.geometry().projection()
            return feat.setGeometry(ee.Geometry.MultiPolygon(filteredGeoms, proj))

        return self._obj.map(removeNonPoly)

    def byProperties(self, properties: ee_list = []) -> ee.Dictionary:
        """Get a dictionary with all feature values for each properties.

        This method is returning a dictionary with all the properties as keys and their values in each feaure as a list.

        .. code-block::

            {
                "property1": [value1, value2, value3, ...],
                "property2": [value1, value2, value3, ...],
                ...
            }

        The output remain server side and can be used to create a client side plot.

        Args:
            properties: A list of properties to get the values from.

        Returns:
            A dictionary with all the properties as keys and their values in each feaure as a list.

        Example:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                d = fc.geetools.byProperties(["ADM1_CODE", "ADM2_CODE"])
                d.getInfo()
        """
        properties = ee.List(properties) if properties else self._obj.first().propertyNames()
        values = properties.map(lambda p: self._obj.aggregate_array(p))

        return ee.Dictionary.fromLists(properties, values)

    def byFeatures(
        self, featureId: ee_str = "system:index", properties: ee_list = []
    ) -> ee.Dictionary:
        """Get a dictionary with all property values for each feature.

        This method is returning a dictionary with all the feature ids as keys and their properties as a dictionary.

        .. code-block::

            {
                "feature1": {
                    "property1": value1,
                    "property2": value2,
                    ...
                },
                "feature2": {
                    "property1": value1,
                    "property2": value2,
                    ...
                },
                ...
            }

        The output remain server side and can be used to create a client side plot.

        We are waiting for the resolution of: https://issuetracker.google.com/issues/329106322 to allow non string feature ids.

        Args:
            featureId: The property to use as the feature id. Defaults to "system:index". This property needs to be a string property.
            properties: A list of properties to get the values from.

        Returns:
            A dictionary with all the feature ids as keys and their properties as a dictionary.

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                d = fc.geetools.byFeature(featureId="ADM2_CODE", properties=["ADM0_CODE"])
                d.getInfo()
        """
        # gather the parameters
        featureId = ee.String(featureId)
        properties = ee.List(properties) if properties else self._obj.first().propertyNames()
        properties = properties.remove(featureId)

        # create a function to get the properties of a feature
        # we need to map the featureCollection into a list as it's not possible to return something else than a
        # featureCollection mapping a FeatureCollection. We know it's a very expensive process but we don't have any
        # other choice.
        fc_list = self._obj.toList(self._obj.size())
        values = fc_list.map(lambda f: ee.Feature(f).toDictionary(properties))

        # get all the id values, they must be string so we are forced to cast them manually
        ids = self._obj.aggregate_array(featureId)
        ids = ids.map(lambda i: ee.String(i))

        return ee.Dictionary.fromLists(ids.map(lambda i: ee.String(i)), values)

    def plot_by_features(
        self, xProperty: str = "system:index", yProperties: list = [], **kwargs
    ) -> Tuple[Figure, Axes]:
        """Plot the values of a FeatureCollection by feature.

        Each feature property selected in yProperties will be plotted using the xProperty as the x-axis.
        If no yProperties are provided, all properties will be plotted.
        If no xProperty is provided, the system:index property will be used.

        Args:
            xProperty: The property to use as the x-axis. Defaults to "system:index".
            yProperties: A list of properties to plot. Defaults to all properties.
            kwargs: Additional arguments from the ``pyplot.plot`` function.

        Returns:
            The matplotlib objects as in a ``pyplot.subplot`` method.

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_features(yProperties=["ADM1_CODE", "ADM2_CODE"])

        Note:
            This function is a client-side function.
        """
        # Get the features and properties
        fc = self._obj
        yProperties = yProperties if yProperties else fc.first().propertyNames().getInfo()
        xProperty not in yProperties or yProperties.remove(xProperty)

        # initialize the plot
        fig, ax = plt.subplots()

        # get all the data and add them to the plot
        x = fc.aggregate_array(xProperty).getInfo()
        ax.set_xlabel(f"Features (labeled by {xProperty})")
        for yProperty in yProperties:
            y = fc.aggregate_array(yProperty).getInfo()
            ax.plot(x, y, label=yProperty, **kwargs)

        # we use the name of the property as y axis only if there is 1 property
        # else we use "Properties values"
        ax.set_ylabel(yProperties[0] if len(yProperties) == 1 else "Properties values")

        # add the legend to the graph
        ax.legend()

        return fig, ax

    def plot_by_property(
        self, xProperties: ee_list = [], seriesProperty: ee_str = "system:index", **kwargs
    ) -> Tuple[Figure, Axes]:
        """Plot the values of a FeatureCollection by property.

        Each features will be represented by a color and each property will a bar of the bar chart.

        Args:
            xProperties: A list of properties to plot. Defaults to all properties.
            seriesProperty: The property to use as the series label. Defaults to "system:index".
            kwargs: Additional arguments from the ``pyplot.bar`` function.

        Returns:
            The matplotlib objects as in a ``pyplot.subplot`` method.

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_property(xProperties=["ADM1_CODE", "ADM2_CODE"])

        Note:
            This function is a client-side function.
        """
        # Get the features and properties
        fc = self._obj
        xProperties = ee.List(xProperties) if xProperties else fc.first().propertyNames()
        xProperties = xProperties.remove(seriesProperty)

        # get the name of each feature label
        seriesLabels = fc.aggregate_array(seriesProperty).getInfo()

        # get the aggregate values for each property and affect them to series
        # the "to_dictionary" method cannot be used as it relies on the fc properties
        # this is often missing when datasets are created from a reducer.
        # I hope GEE team will change it in the future.
        values = xProperties.map(lambda p: fc.aggregate_array(p))
        properties = ee.Dictionary.fromLists(xProperties, values).getInfo()
        series = {k: [v[i] for v in properties.values()] for i, k in enumerate(seriesLabels)}

        print(json.dumps(series))

        # initialize the plot
        fig, ax = plt.subplots()

        # display the series
        x = np.arange(len(properties))  # the label locations
        width = kwargs.get("width", 0.1)  # the width of the bars

        multiplier = 0
        for id_, value in series.items():
            offset = width * multiplier
            ax.bar(x + offset, value, width, label=id_, **kwargs)
            multiplier += 1

        # add meaningful ticks to the x axis
        tick_offset = (len(series) - 1) / 2 * width
        ax.set_xticks(x + tick_offset, properties.keys())

        # add a legend
        ax.legend()

        return fig, ax
