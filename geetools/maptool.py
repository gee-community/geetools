# coding=utf-8

''' This module is designed to use in the Jupyter Notebook. It uses folium and
branca, and is inspired in https://github.com/mccarthyryanc/folium_gee '''

import folium
import ee
from copy import copy

if not ee.data._initialized: ee.Initialize()

class Map(folium.Map):
    def __init__(self, **kwargs):
        super(Map, self).__init__(**kwargs)

    def show(self):
        LC = folium.LayerControl()
        self.add_child(LC)
        return self

    def addLayer(self, eeObject, visParams=None, name=None, show=True,
                 opacity=None):
        """
        Adds a given EE object to the map as a layer.

        Returns the new map layer.

        Arguments:
        eeObject (Collection|Feature|Image|MapId):
        The object to add to the map.

        visParams (FeatureVisualizationParameters|ImageVisualizationParameters, optional):
        The visualization parameters. For Images and ImageCollection, see ee.data.getMapId for valid parameters. For Features and FeatureCollections, the only supported key is "color", as a CSS 3.0 color string or a hex string in "RRGGBB" format.

        name (String, optional):
        The name of the layer. Defaults to "Layer N".

        shown (Boolean, optional):
        A flag indicating whether the layer should be on by default.

        opacity (Number, optional):
        The layer's opacity represented as a number between 0 and 1. Defaults to 1.

        Returns: ui.Map.Layer
        """
        if not isinstance(eeObject, ee.Image):
            raise ValueError('addLayer currently supports ee.Image as eeObject argument')

        image = eeObject

        name = name if name else image.id().getInfo()

        # Default parameters
        default = get_default_vis(image)
        default.update(visParams)

        # Take away bands from parameters
        newVisParams = {}
        for key, val in default.iteritems():
            if key == 'bands': continue
            newVisParams[key] = val

        # Get the MapID and Token after applying parameters
        image_info = image.select(visParams['bands']).getMapId(newVisParams)
        mapid = image_info['mapid']
        token = image_info['token']

        tiles = "https://earthengine.googleapis.com/map/%s/{z}/{x}/{y}?token=%s"%(mapid,token)
        folium_kwargs = {'attr': 'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a> ',
                         'tiles': tiles,
                         'name': name,
                         'overlay': True,
                         # 'show': show
                         }

        layer = folium.TileLayer(**folium_kwargs)
        layer.add_to(self)

        return self

    def centerObject(self, object, zoom=None):
        """
        Centers the map view on a given object.

        Returns the map.

        Arguments:
        object (Element|Geometry):
        An object to center on - a geometry, image or feature.

        zoom (Number, optional):
        The zoom level, from 1 to 24. If unspecified, computed based on the object's bounding box.
        :return:
        """
        if not isinstance(object, ee.Image):
            raise ValueError('centerObject currently supports ee.Image as object argument')

        bounds = object.geometry().bounds(1).getInfo()['coordinates']
        bounds = inverse_coordinates(bounds)
        self.fit_bounds([bounds[0], bounds[2]], max_zoom=zoom)

        return self

def get_default_vis(image, stretch=0.8):
    bandnames = image.bandNames().getInfo()

    if len(bandnames) < 3:
        selected = image.select([0]).getInfo()
        bandnames = bandnames[0]
    else:
        selected = image.select([0, 1, 2]).getInfo()
        bandnames = [bandnames[0], bandnames[1], bandnames[2]]

    bands = selected['bands']
    # bandnames = [bands[0]['id'], bands[1]['id'], bands[2]['id']]
    types = bands[0]['data_type']

    maxs = {'float':1,
            'int8': 127, 'uint8': 255,
            'int16': 32767, 'uint16': 65535,
            'int32': 2147483647, 'uint32': 4294967295,
            'int64': 9223372036854776000}

    if types['precision'] == 'float':
        btype = 'float'
    else:
        max = types['max']
        maxsi = dict((val, key) for key, val in maxs.iteritems())
        btype = maxsi[int(max)]

    limits = {'float': 0.8}

    for key, val in maxs.iteritems():
        limits[key] = val*stretch

    min = 0
    max = limits[btype]
    return {'bands':bandnames, 'min':min, 'max':max}

def inverse_coordinates(coords):
    proxy = copy(coords)
    if isinstance(proxy, list):
        nest = -1
        ty = type(proxy)
        while ty == list:
            proxy = proxy[0]
            ty = type(proxy)
            nest += 1
    else:
        raise ValueError('coords must be at least a list of points')

    # Unnest
    if nest > 1:
        for n in range(nest-1):
            coords = coords[0]

    newcoords = []
    for coord in coords:
        newcoord = [coord[1], coord[0]]
        newcoords.append(newcoord)

    # Nest again? NO

    return newcoords