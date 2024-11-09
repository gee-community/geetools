"""Toolbox for the `ee.FeatureCollection` class."""
from __future__ import annotations

import ee
import geopandas as gpd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from .accessors import register_class_accessor
from .utils import plot_data


@register_class_accessor(ee.FeatureCollection, "geetools")
class FeatureCollectionAccessor:
    """Toolbox for the `ee.FeatureCollection` class."""

    def __init__(self, obj: ee.FeatureCollection):
        """Initialize the FeatureCollection class."""
        self._obj = obj

    def toImage(
        self,
        color: str | ee.String | int | ee.Number = 0,
        width: str | ee.String | int | ee.Number = "",
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

    def toDictionary(
        self, keyColumn: str | ee.String = "system:index", selectors: list | ee.List = []
    ) -> ee.Dictionary:
        """Convert to Dictionary.

        Parameters:
            keyColumn: the column to use as keys. Must contain unique values, if not it will fail.
            selectors: a list of properties to add in the output. If the list is empty all properties will be added.

        Returns:
            a ee.Dictionary with values of keyColumn as keys and ee.Dictionary as
            values. The output will look like:

            {
             '00000000000000000010': {'ADM0_CODE': 74578, 'ADM0_NAME': 'Azores Islands'},
             '00000000000000000011': {'ADM0_CODE': 7, 'ADM0_NAME': 'Andorra'}
            }
        """
        uniqueIds = self._obj.aggregate_array(keyColumn)
        selectors = ee.List(selectors) if selectors else self._obj.first().propertyNames()
        keyColumn = ee.String(keyColumn)

        features = self._obj.toList(self._obj.size())
        values = features.map(lambda feat: ee.Feature(feat).toDictionary(selectors))
        keys = uniqueIds.map(lambda uid: ee.String(ee.Algorithms.String(uid)))
        return ee.Dictionary.fromLists(keys, values)

    def addId(
        self, name: str | ee.String = "id", start: int | ee.Number = 1
    ) -> ee.FeatureCollection:
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
        self,
        featureId: str | ee.String = "system:index",
        properties: list | ee.List = [],
        labels: list = [],
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
            featureId: The property used to label features. Defaults to "system:index".
            properties: A list of properties to get the values from.
            labels: A list of names to replace properties names. Default to the properties names.

        Returns:
            A dictionary with all the properties as keys and their values in each feaure as a list.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.byFeatures`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_properties`

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

        # get the label to use in the dictionary if requested
        labels = ee.List(labels) if labels else properties

        return ee.Dictionary.fromLists(labels, values)

    def byFeatures(
        self,
        featureId: str | ee.String = "system:index",
        properties: list | ee.List = [],
        labels: list = [],
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

        Args:
            featureId: The property to use as the feature id. Defaults to "system:index". This property needs to be a string property.
            properties: A list of properties to get the values from.
            labels: A list of names to replace properties names. Default to the properties names.

        Returns:
            A dictionary with all the feature ids as keys and their properties as a dictionary.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.byProperties`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_features`

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                d = fc.geetools.byFeature(featureId="ADM2_CODE", properties=["ADM0_CODE"])
                d.getInfo()
        """
        # compute the properties and their labels
        props = ee.List(properties) if properties else self._obj.first().propertyNames()
        props = props.remove(featureId)
        labels = ee.List(labels) if labels else props

        # create a function to get the properties of a feature
        # we need to map the featureCollection into a list as it's not possible to return something else than a
        # featureCollection mapping a FeatureCollection. very expensive process but we don't have any other choice.
        fc = self._obj.select(propertySelectors=props, newProperties=props)
        fc_list = fc.toList(self._obj.size())
        values = fc_list.map(lambda f: ee.Feature(f).select(props, labels).toDictionary(labels))

        # get all the id values, they must be string so we are forced to cast them manually
        # the default casting is broken from Python side: https://issuetracker.google.com/issues/329106322
        features = self._obj.aggregate_array(featureId)
        isString = lambda i: ee.Algorithms.ObjectType(i).compareTo("String").eq(0)  # noqa: E731
        features = features.map(lambda i: ee.Algorithms.If(isString(i), i, ee.Number(i).format()))

        return ee.Dictionary.fromLists(features, values)

    def plot_by_features(
        self,
        type: str = "bar",
        featureId: str = "system:index",
        properties: list = [],
        labels: list = [],
        colors: list = [],
        ax: Axes | None = None,
        **kwargs,
    ) -> Axes:
        """Plot the values of a ``ee.FeatureCollection`` by feature.

        Each feature property selected in properties will be plotted using the ``featureId`` as the x-axis.
        If no ``properties`` are provided, all properties will be plotted.
        If no ``featureId`` is provided, the "system:index" property will be used.

        Warning:
            This function is a client-side function.

        Args:
            type: The type of plot to use. Defaults to "bar". can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
            featureId: The property to use as the x-axis (name the features). Defaults to "system:index".
            properties: A list of properties to plot. Defaults to all properties.
            labels: A list of labels to use for plotting the properties. If not provided, the default labels will be used. It needs to match the properties length.
            colors: A list of colors to use for plotting the properties. If not provided, the default colors from the matplotlib library will be used.
            ax: The matplotlib axes to use. If not provided, the plot will be send to a new figure.
            kwargs: Additional arguments from the ``pyplot`` function.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.byFeatures`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_properties`
            - :docstring:`ee.FeatureCollection.geetools.plot_hist`
            - :docstring:`ee.FeatureCollection.geetools.plot`

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_features(properties=["ADM1_CODE", "ADM2_CODE"])
        """
        # Get the features and properties
        props = ee.List(properties) if properties else self._obj.first().propertyNames().getInfo()
        props = props.remove(featureId)

        # get the data from server
        data = self.byProperties(featureId, props, labels).getInfo()

        # reorder the data according to the labels or properties set by the user
        labels = labels if labels else props.getInfo()
        data = {k: data[k] for k in labels}

        return plot_data(type=type, data=data, label_name=featureId, colors=colors, ax=ax, **kwargs)

    def plot_by_properties(
        self,
        type: str = "bar",
        featureId: str = "system:index",
        properties: list | ee.List = [],
        labels: list = [],
        colors: list = [],
        ax: Axes | None = None,
        **kwargs,
    ) -> Axes:
        """Plot the values of a FeatureCollection by property.

        Each features will be represented by a color and each property will be a bar of the bar chart.

        Warning:
            This function is a client-side function.

        Args:
            type: The type of plot to use. Defaults to "bar". can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
            featureId: The property to use as the y-axis (name the features). Defaults to "system:index".
            properties: A list of properties to plot. Defaults to all properties.
            labels: A list of labels to use for plotting the properties. If not provided, the default labels will be used. It needs to match the properties length.
            colors: A list of colors to use for plotting the properties. If not provided, the default colors from the matplotlib library will be used.
            ax: The matplotlib axes to use. If not provided, the plot will be send to a new figure.
            kwargs: Additional arguments from the ``pyplot`` function.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.byProperties`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_features`
            - :docstring:`ee.FeatureCollection.geetools.plot_hist`
            - :docstring:`ee.FeatureCollection.geetools.plot`

        Examples:
            .. code-block:: python

                import ee, geetools

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fc.geetools.plot_by_properties(xProperties=["ADM1_CODE", "ADM2_CODE"])
        """
        # Get the features and properties
        fc = self._obj
        props = ee.List(properties) if properties else fc.first().propertyNames()
        props = props.remove(featureId)

        # get the data from server
        data = self.byFeatures(featureId, props, labels).getInfo()

        # reorder the data according to the lapbes or properties set by the user
        labels = labels if labels else props.getInfo()
        data = {f: {k: data[f][k] for k in labels} for f in data.keys()}

        return plot_data(type=type, data=data, label_name=featureId, colors=colors, ax=ax, **kwargs)

    def plot_hist(
        self,
        property: str | ee.String,
        label: str = "",
        ax: Axes | None = None,
        color=None,
        **kwargs,
    ) -> Axes:
        """Plot the histogram of a specific property.

        Warning:
            This function is a client-side function.

        Args:
            property: The property to display
            label: The label to use for the property. If not provided, the property name will be used.
            ax: The matplotlib axes to use. If not provided, the plot will be send to the current axes (``plt.gca()``)
            color: The color to use for the plot. If not provided, the default colors from the matplotlib library will be used.
            kwargs: Additional arguments from the ``pyplot.hist`` function.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.plot_by_features`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_properties`
            - :docstring:`ee.FeatureCollection.geetools.plot`

        Examples:
            .. code-block:: python

                import ee, geetools

                normClim = ee.ImageCollection('OREGONSTATE/PRISM/Norm81m').toBands()
                region = ee.Geometry.Rectangle(-123.41, 40.43, -116.38, 45.14)
                climSamp = normClim.sample(region, 5000)
                climSamp.geetools.plot_hist("07_ppt")
        """
        # gather the data from parameters
        properties, labels = ee.List([property]), ee.List([label])

        # get the data from the server
        data = self.byProperties(properties=properties, labels=labels).getInfo()

        # define the ax if not provided by the user
        if ax is None:
            fig, ax = plt.subplots()

        # gather the data from the data variable
        labels = list(data.keys())
        if len(labels) != 1:
            raise ValueError("Pie chart can only be used with one property")

        kwargs["rwidth"] = kwargs.get("rwidth", 0.9)
        kwargs["color"] = color or plt.get_cmap("tab10").colors[0]
        ax.hist(list(data[labels[0]].values()), **kwargs)
        ax.set_xlabel(labels[0])
        ax.set_ylabel("frequency")

        # customize the layout of the axis
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # make sure the canvas is only rendered once.
        ax.figure.canvas.draw_idle()

        return ax

    def plot(
        self,
        ax: Axes | None = None,
        property: str = "",
        crs: str = "EPSG:4326",
        cmap: str = "viridis",
        boundaries: bool = False,
        color: str = "k",
    ):
        """Plot the featureCollection on a map using the provided property.

        Warning:
            This function is a client-side function.

        Parameters:
            property: The property to use to color the features.
            ax: The axes to plot the map on.
            crs: The CRS to use for the map.
            cmap: The colormap to use for the colors.
            boundaries: Whether to plot the features values or only the boundaries.
            color: The color to use for the boundaries.

        See Also:
            - :docstring:`ee.FeatureCollection.geetools.plot_by_features`
            - :docstring:`ee.FeatureCollection.geetools.plot_by_properties`
            - :docstring:`ee.FeatureCollection.geetools.plot_hist`

        Examples:
            .. code-block:: python

                import ee
                import geetools

                ee.Initialize()

                fc = ee.FeatureCollection("FAO/GAUL/2015/level2").limit(10)
                fig, ax = plt.subplots()
                fc.geetools.plot("ADM2_CODE", ax)
        """
        if ax is None:
            fig, ax = plt.subplots()

        # get the data from the server
        names = self._obj.first().propertyNames()
        names = names.filter(ee.Filter.stringStartsWith("item", "system:").Not())
        property = property if property != "" else names.get(0).getInfo()
        data = self._obj.select([property]).getInfo()

        # transform the data to a geodataframe and reproject it to the destination crs
        gdf = gpd.GeoDataFrame.from_features(data["features"]).set_crs(4326).to_crs(crs)

        # plot the data on the map either as contours or a valued features
        if boundaries is True:
            gdf.boundary.plot(ax=ax, color=color)
        else:
            gdf.plot(column=property, ax=ax, cmap=cmap)
