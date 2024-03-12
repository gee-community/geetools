"""Toolbox for the `ee.FeatureCollection` class."""
from __future__ import annotations

from typing import Optional, Union

import ee
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba

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

    def byProperties(
        self, properties: ee_list = [], featureId: ee_str = "system:index"
    ) -> ee.Dictionary:
        """Get a dictionary with all feature values for each properties.

        This method is returning a dictionary with all the properties as keys and their values in each feaure as a list.

        .. code-block::

            {
                "property1": {"feature1": value1, "feature2": value2, ...},
                "property2": {"feature1": value1, "feature2": value2, ...},
                ...
            }

        The output remain server side and can be used to create a client side plot.

        Args:
            featureId: The property to use as the feature id. Defaults to "system:index".
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
        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = self._obj.aggregate_array(featureId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))

        # retrieve properties for each feature
        properties = ee.List(properties) if properties else self._obj.first().propertyNames()
        properties = properties.remove(featureId)
        values = properties.map(
            lambda p: ee.Dictionary.fromLists(features, self._obj.aggregate_array(p))
        )

        return ee.Dictionary.fromLists(properties, values)

    def byFeatures(
        self, featureId: ee_str = "system:index", properties: ee_list = []
    ) -> ee.Dictionary:
        """Get a dictionary with all property values for each feature.

        This method is returning a dictionary with all the feature ids as keys and their properties as a dictionary.

        .. code-block::

            {
                "feature1": {"property1": value1, "property2": value2, ...},
                "feature2": {"property1": value1, "property2": value2, ...},
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
        # create a function to get the properties of a feature
        # we need to map the featureCollection into a list as it's not possible to return something else than a
        # featureCollection mapping a FeatureCollection.
        # We know it's a very expensive process but we don't have any other choice.
        properties = ee.List(properties) if properties else self._obj.first().propertyNames()
        properties = properties.remove(featureId)
        fc_list = self._obj.toList(self._obj.size())
        values = fc_list.map(lambda f: ee.Feature(f).toDictionary(properties))

        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = self._obj.aggregate_array(featureId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))

        return ee.Dictionary.fromLists(features, values)

    def plot_by_features(
        self,
        type: str = "bar",
        xProperty: str = "system:index",
        yProperties: list = [],
        ax: Optional[Axes] = None,
        colors: list = [],
        **kwargs,
    ):
        """Plot the values of a FeatureCollection by feature.

        Each feature property selected in yProperties will be plotted using the xProperty as the x-axis.
        If no yProperties are provided, all properties will be plotted.
        If no xProperty is provided, the system:index property will be used.

        Args:
            xProperty: The property to use as the x-axis. Defaults to "system:index".
            yProperties: A list of properties to plot. Defaults to all properties.
            type: The type of plot to use. Defaults to "bar". can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
            ax: The matplotlib axes to use. If not provided, the plot will be send to the current axes (``plt.gca()``)
            colors: A list of colors to use for the plot. If not provided, the default colors from the matplotlib library will be used. It need to be consistent with the size of the plotted data which is type dependent.
            kwargs: Additional arguments from the ``pyplot.plot`` function.

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_features(yProperties=["ADM1_CODE", "ADM2_CODE"])

        Note:
            This function is a client-side function.
        """
        # Get the features and properties
        yProperties = yProperties if yProperties else self._obj.first().propertyNames().getInfo()
        xProperty not in yProperties or yProperties.remove(xProperty)  # type: ignore

        # get the data from server
        data = self.byProperties(yProperties).getInfo()

        self._plot(data, xProperty, type, ax=ax, colors=colors, **kwargs)

    def plot_by_properties(
        self,
        type: str = "bar",
        xProperties: ee_list = [],
        seriesProperty: ee_str = "system:index",
        ax: Optional[Axes] = None,
        colors: list = [],
        **kwargs,
    ):
        """Plot the values of a FeatureCollection by property.

        Each features will be represented by a color and each property will be a bar of the bar chart.

        Args:
            xProperties: A list of properties to plot. Defaults to all properties.
            seriesProperty: The property to use as the series label. Defaults to "system:index".
            type: The type of plot to use. Defaults to "bar". can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
            ax: The matplotlib axes to use. If not provided, the plot will be send to the current axes (``plt.gca()``)
            colors: A list of colors to use for the plot. If not provided, the default colors from the matplotlib library will be used. It need to be consistent with the size of the plotted data which is type dependent.
            kwargs: Additional arguments from the ``pyplot.bar`` function.

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_properties(xProperties=["ADM1_CODE", "ADM2_CODE"])

        Note:
            This function is a client-side function.
        """
        # Get the features and properties
        fc = self._obj
        xProperties = ee.List(xProperties) if xProperties else fc.first().propertyNames()
        xProperties = xProperties.remove(seriesProperty)

        # get the name of each properties
        xProperties.getInfo()

        # get the data from server
        data = self.byFeatures(seriesProperty, xProperties).getInfo()

        self._plot(data, seriesProperty, type, ax=ax, colors=colors, **kwargs)

    def plot_hist(self, property: ee_str, ax: Optional[Axes] = None, color=None, **kwargs):
        """Plot the histogram of a specific property.

        Args:
            property: The property to display
            ax: The matplotlib axes to use. If not provided, the plot will be send to the current axes (``plt.gca()``)
            color: The color to use for the plot. If not provided, the default colors from the matplotlib library will be used.
            kwargs: Additional arguments from the ``pyplot.hist`` function.

        Examples:
            .. code-block:: python

                import ee, geetools

                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm81m').toBands()
                region = ee.Geometry.Rectangle(-123.41, 40.43, -116.38, 45.14)
                climSamp = normClim.sample(region, 5000)
                climSamp.geetools.plot_hist("07_ppt")
        """
        # gather the data from parameters
        properties = ee.List([property])
        colors = [] if color is None else [color]

        # get the data from the server
        data = self.byProperties(properties).getInfo()

        self._plot(data, property, "hist", ax=ax, colors=colors, **kwargs)

    @staticmethod
    def _plot(
        data: dict,
        label_prop: str,
        type: str = "plot",
        ax: Optional[Axes] = None,
        colors: list = [],
        **kwargs,
    ):
        """Plotting mechanism used in all the plotting functions.

        It binds the matplotlib capabilities with the data aggregated either by feature or by properties.
        the shape of the data should as follows:

        .. code-block::

            {
                "label1": {"property1": value1, "property2": value2, ...}
                "label2": {"property1": value1, "property2": value2, ...},
                ...
            }

        Args:
            data: the data to use as inputs of the graph
            label_prop: The property that twas used to generate the labels
            type: The type of plot to use. Defaults to "bar". can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
            ax: The matplotlib axes to use. If not provided, the plot will be send to the current axes (``plt.gca()``)
            colors: A list of colors to use for the plot. If not provided, the default colors from the matplotlib library will be used. It need to be consistent with the size of the plotted data which is type dependent.
            kwargs: Additional arguments from the ``pyplot`` chat type selected.
        """
        # define the ax if not provided by the user
        if ax is None:
            fig, ax = plt.subplots()

        # gather the data from parameters
        labels = list(data.keys())
        properties = list(data[labels[0]].keys())
        colors = colors if colors else plt.cm.get_cmap("tab10").colors

        # draw the chart based on the type
        if type == "plot":
            for i, label in enumerate(labels):
                kwargs["color"] = colors[i]
                name = properties[0] if len(properties) == 1 else "Properties values"
                ax.plot(properties, list(data[label].values()), label=label, **kwargs)
                ax.set_ylabel(name)
                ax.set_xlabel(f"Features (labeled by {label_prop})")
            ax.legend()

        elif type == "scatter":
            for i, label in enumerate(labels):
                kwargs["color"] = colors[i]
                name = properties[0] if len(properties) == 1 else "Properties values"
                ax.scatter(properties, list(data[label].values()), label=label, **kwargs)
                ax.set_ylabel(properties[0])
                ax.set_xlabel(f"Features (labeled by {label_prop})")
            ax.legend()

        elif type == "fill_between":
            for i, label in enumerate(labels):
                kwargs["facecolor"] = to_rgba(colors[i], 0.2)
                kwargs["edgecolor"] = to_rgba(colors[i], 1)
                name = properties[0] if len(properties) == 1 else "Properties values"
                ax.fill_between(properties, list(data[label].values()), label=label, **kwargs)
                ax.set_ylabel(name)
                ax.set_xlabel(f"Features (labeled by {label_prop})")
            ax.legend()

        elif type == "bar":
            x = np.arange(len(properties))
            width = 1 / (len(labels) + 0.5)
            margin = width / 10
            kwargs["width"] = width - margin
            ax.set_xticks(x + width, properties)
            for i, (id_, value) in enumerate(data.items()):
                kwargs["color"] = colors[i]
                ax.bar(x + width * i, list(value.values()), label=id_, **kwargs)
            ax.legend()

        elif type == "stacked":
            x = np.arange(len(properties))
            bottom = np.zeros(len(properties))
            for i, (id_, value) in enumerate(data.items()):
                kwargs.update(color=colors[i], bottom=bottom)
                ax.bar(x, list(value.values()), label=id_, **kwargs)
                bottom += list(value.values())
            ax.legend()

        elif type == "pie":
            if len(labels) != 1:
                raise ValueError("Pie chart can only be used with one property")
            kwargs["autopct"] = kwargs.get("autopct", "%1.1f%%")
            kwargs["normalize"] = kwargs.get("normalize", True)
            kwargs["labeldistance"] = kwargs.get("labeldistance", None)
            kwargs["wedgeprops"] = kwargs.get("wedgeprops", {"edgecolor": "w"})
            kwargs["textprops"] = kwargs.get("textprops", {"color": "w"})
            kwargs.update(autopct="%1.1f%%", colors=colors)
            ax.pie(list(data[labels[0]].values()), labels=properties, **kwargs)
            ax.legend()

        elif type == "donut":
            if len(labels) != 1:
                raise ValueError("Pie chart can only be used with one property")
            kwargs["autopct"] = kwargs.get("autopct", "%1.1f%%")
            kwargs["normalize"] = kwargs.get("normalize", True)
            kwargs["labeldistance"] = kwargs.get("labeldistance", None)
            kwargs["wedgeprops"] = kwargs.get("wedgeprops", {"width": 0.6, "edgecolor": "w"})
            kwargs["textprops"] = kwargs.get("textprops", {"color": "w"})
            kwargs["pctdistance"] = kwargs.get("pctdistance", 0.7)
            kwargs.update(autopct="%1.1f%%", colors=colors)
            ax.pie(list(data[labels[0]].values()), labels=properties, **kwargs)
            ax.legend()

        elif type == "hist":
            if len(labels) != 1:
                raise ValueError("Pie chart can only be used with one property")
            kwargs["rwidth"] = kwargs.get("rwidth", 0.9)
            kwargs["color"] = colors[0]
            ax.hist(list(data[labels[0]].values()), **kwargs)
            ax.set_xlabel(f"{labels[0]} values")
            ax.set_ylabel("frequency")

        else:
            raise ValueError(f"Type {type} is not (yet?) supported")

        # customize the layout of the axis
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # make sure the canvas is only rendered once.
        ax.figure.canvas.draw_idle()
