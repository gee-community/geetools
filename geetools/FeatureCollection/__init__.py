"""Toolbox for the `ee.FeatureCollection` class."""
from __future__ import annotations

from typing import Tuple, Union

import ee
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from geetools.accessors import register_class_accessor
from geetools.types import ee_int, ee_str


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

        Note:
            This function is a client-side function.
        """
        # Get the features and properties
        fc = self._obj
        yproperties = yProperties if yProperties else fc.first().propertyNames().getInfo()
        xProperty not in yproperties or yproperties.remove(xProperty)

        # initialize the plot
        fig, ax = plt.subplots()

        # get all the data and add them to the plot
        x = fc.aggregate_array(xProperty).getInfo()
        ax.set_xlabel(f"Features (labeled by {xProperty})")
        for yProperty in yproperties:
            y = fc.aggregate_array(yProperty).getInfo()
            ax.plot(x, y, label=yProperty, **kwargs)

        # we use the name of the property as y axis only if there is 1 property
        # else we use "Properties values"
        ax.set_ylabel(yproperties[0] if len(yProperties) == 1 else "Properties values")

        # add the legend to the graph
        ax.legend()

        return fig, ax
