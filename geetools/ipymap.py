# coding=utf-8

''' This module is designed to use ONLY in the Jupyter Notebook. It is
 inspired on Tyler Erickson's contribution on
https://github.com/gee-community/ee-jupyter-contrib/blob/master/examples/getting-started/display-interactive-map.ipynb'''

import ipyleaflet
from ipywidgets import HTML
from IPython.display import display
import ee
from . import tools
from .maptool import get_default_vis, inverse_coordinates, get_data,\
                     get_image_tile, get_geojson_tile, get_bounds, get_zoom
import json

if not ee.data._initialized: ee.Initialize()

class Map(ipyleaflet.Map):
    def __init__(self, **kwargs):
        # Change defaults
        kwargs.setdefault('center', [0, 0])
        kwargs.setdefault('zoom', 2)
        super(Map, self).__init__(**kwargs)
        self.added_geometries = 0
        self.is_shown = False

    def show(self):
        if not self.is_shown:
            lc = ipyleaflet.LayersControl()
            self.add_control(lc)
            self.is_shown = True
        display(self)

    def addLayer(self, eeObject, visParams=None, name=None, show=True,
                 opacity=None, inspect={'data':None, 'reducer':None, 'scale':None}):
        thename = name

        def addImage(image):
            params = get_image_tile(image, visParams, name, show, opacity)
            layer = ipyleaflet.TileLayer(url=params['url'],
                                         attribution=params['attribution'],
                                         name=params['name'])
            self.add_layer(layer)

        def addGeoJson(geometry):
            params = get_geojson_tile(self, geometry, name, inspect)
            layer = ipyleaflet.GeoJSON(data=params['geojson'],
                                       name=params['name'],
                                       popup=HTML(params['pop']))
            self.added_geometries += 1
            self.add_layer(layer)

        # CASE: ee.Image
        if isinstance(eeObject, ee.Image):
            addImage(eeObject)

        elif isinstance(eeObject, ee.Geometry):
            addGeoJson(eeObject)

        elif isinstance(eeObject, ee.Feature):
            geom = eeObject.geometry()
            addGeoJson(geom)

        elif isinstance(eeObject, ee.ImageCollection):
            print('`addLayer` currently supports to add only ee.Image,\
                   ee.Geometry and ee.Feature')
            pass
        else:
            raise ValueError('addLayer currently supports ee.Image as eeObject\
                              argument')

    def centerObject(self, eeObject, zoom=None, method=1):
        """ Center an eeObject

        :param eeObject:
        :param zoom:
        :param method: experimetal methods to estimate zoom for fitting bounds
            Currently: 1 or 2
        :type: int
        """
        bounds = get_bounds(eeObject)
        if isinstance(eeObject, ee.Geometry):
            centroid = eeObject.centroid().getInfo()['coordinates']
        else:
            centroid = eeObject.geometry().centroid().getInfo()['coordinates']

        self.center = inverse_coordinates(centroid)
        if zoom:
            self.zoom = zoom
        else:
            self.zoom = get_zoom(bounds, method)

    def getCenter(self):
        """ Returns the coordinates at the center of the map.

        No arguments.
        Returns: Geometry.Point

        :return:
        """
        center = self.center
        coords = inverse_coordinates(center)
        return ee.Geometry.Point(coords)