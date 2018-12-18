# coding=utf-8
""" This module is designed to use ONLY in the Jupyter Notebook. It is
 inspired on Tyler Erickson's contribution on
https://github.com/gee-community/ee-jupyter-contrib/blob/master/examples/getting-started/display-interactive-map.ipynb
"""
import ipyleaflet
from ipywidgets import HTML, Tab, Accordion, HBox, SelectMultiple, Select,\
                       Button, VBox, RadioButtons, Dropdown, Layout, \
                       FloatRangeSlider
from IPython.display import display
from traitlets import Dict, observe
import ee
if not ee.data._initialized: ee.Initialize()
from collections import OrderedDict
from .. import tools
from .maptool import inverse_coordinates, get_image_tile, get_geojson_tile, \
                     get_bounds, get_zoom, feature_properties_output
from . import maptool, ipytools
import threading
from copy import copy
import traceback
import sys

ZOOM_SCALE = {
    0: 156543, 1: 78271, 2: 39135, 3: 19567, 4: 9783, 5: 4891, 6: 2445,
    7: 1222, 8: 611, 9: 305, 10: 152, 11: 76, 12: 38, 13: 19, 14: 9, 15: 5,
    16: 2, 17: 1, 18: 0.5, 19: 0.3, 20: 0.15, 21: 0.07, 22: 0.03,
}


class Map(ipyleaflet.Map):
    tab_children_dict = Dict()
    EELayers = Dict()
    def __init__(self, tabs=('Inspector', 'Layers', 'Assets', 'Tasks'),
                 **kwargs):
        # Change defaults
        kwargs.setdefault('center', [0, 0])
        kwargs.setdefault('zoom', 2)
        kwargs.setdefault('scroll_wheel_zoom', True)
        kwargs.setdefault('max_zoom', 22)
        super(Map, self).__init__(**kwargs)
        self.is_shown = False

        # Width and Height
        self.width = kwargs.get('width', None)
        self.height = kwargs.get('height', None)
        self.set_dimensions(self.width, self.height)

        # Correct base layer name
        baselayer = self.layers[0]
        baselayer.name = 'OpenStreetMap'
        self.layers = (baselayer,)

        # Dictionary of map's handlers
        self.handlers = {}

        # Dictonary to hold tab's widgets
        # (tab's name:widget)
        self.tab_names = []
        self.tab_children = []
        self.tab_children_dict = OrderedDict(zip(self.tab_names,
                                                 self.tab_children))

        # TABS
        # Tab widget
        self.tab_widget = Tab()
        # Handler for Tab
        self.tab_widget.observe(self.handle_change_tab)

        self.tabs = tabs
        if len(tabs) > 0:
            # TODO: create widgets only if are in tuple
            # Inspector Widget (Accordion)
            self.inspector_wid = CustomInspector()
            self.inspector_wid.main.selected_index = None # this will unselect all

            # Task Manager Widget
            task_manager = ipytools.TaskManager()

            # Asset Manager Widget
            asset_manager = ipytools.AssetManager(self)

            # Layers
            self.layers_widget = LayersWidget(map=self)

            widgets = {'Inspector': self.inspector_wid,
                       'Layers': self.layers_widget,
                       'Assets': asset_manager,
                       'Tasks': task_manager,
                       }
            handlers = {'Inspector': self.handle_inspector,
                        'Layers': None,
                        'Assets': None,
                        'Tasks': None,
                        }

            # Add tabs and handlers
            for tab in tabs:
                if tab in widgets.keys():
                    widget = widgets[tab]
                    handler = handlers[tab]
                    self.addTab(tab, handler, widget)
                else:
                    raise ValueError('Tab {} is not recognized. Choose one of {}'.format(tab, widgets.keys()))

            # First handler: Inspector
            self.on_interaction(self.handlers[tabs[0]])

        # As I cannot create a Geometry with a GeoJSON string I do a workaround
        self.draw_types = {'Polygon': ee.Geometry.Polygon,
                           'Point': ee.Geometry.Point,
                           'LineString': ee.Geometry.LineString,
                           }
        # create EELayers
        self.EELayers = OrderedDict()

    def _add_EELayer(self, name, data):
        ''' add a pair of name, data to EELayers '''
        copyEELayers = copy(self.EELayers)
        copyEELayers[name] = data
        self.EELayers = copyEELayers

    def _remove_EELayer(self, name):
        ''' remove layer from EELayers '''
        copyEELayers = copy(self.EELayers)
        if name in copyEELayers:
            copyEELayers.pop(name)
        self.EELayers = copyEELayers

    def set_dimensions(self, width=None, height=None):
        """ Set the dimensions for the map

        :param width:
        :param height:
        :return:
        """
        self.layout = Layout(width=width, height=height)

    def move_layer(self, layer_name, direction='up'):
        ''' Move one step up a layer '''
        names = list(self.EELayers.keys())
        values = list(self.EELayers.values())

        if direction == 'up':
            dir = 1
        elif direction == 'down':
            dir = -1
        else:
            dir = 0

        if layer_name in names:  # if layer exists
            # index and value of layer to move_layer
            i = names.index(layer_name)
            condition = (i < len(names)-1) if dir == 1 else (i > 0)
            if condition:  # if layer is not in the edge
                ival = values[i]
                # new index for layer
                newi = i+dir
                # get index and value that already exist in the new index
                iname_before = names[newi]
                ival_before = values[newi]
                # Change order
                # set layer and value in the new index
                names[newi] = layer_name
                values[newi] = ival
                # set replaced layer and its value in the index of moving layer
                names[i] = iname_before
                values[i] = ival_before

                newlayers = OrderedDict(zip(names, values))
                self.EELayers = newlayers

    @observe('EELayers')
    def _ob_EELayers(self, change):
        new = change['new']
        proxy_layers = [self.layers[0]]

        for val in new.values():
            layer = val['layer']
            proxy_layers.append(layer)

        self.layers = tuple(proxy_layers)

        # UPDATE INSPECTOR
        # Clear options
        self.inspector_wid.selector.options = {}
        # Add layer to the Inspector Widget
        self.inspector_wid.selector.options = new # self.EELayers

        # UPDATE LAYERS WIDGET
        # update Layers Widget
        self.layers_widget.selector.options = {}
        self.layers_widget.selector.options = new # self.EELayers

    @property
    def added_images(self):
        return sum(
            [1 for val in self.EELayers.values() if val['type'] == 'Image'])

    @property
    def added_geometries(self):
        return sum(
            [1 for val in self.EELayers.values() if val['type'] == 'Geometry'])

    def task_widget(self):
        with self.tasksWid:
            while True:
                list = ee.data.getTaskList()

    def show(self, tabs=True, layer_control=True, draw_control=False):
        """ Show the Map on the Notebook """
        if not self.is_shown:
            if layer_control:
                # Layers Control
                lc = ipyleaflet.LayersControl()
                self.add_control(lc)
            if draw_control:
                # Draw Control
                dc = ipyleaflet.DrawControl(# edit=False,
                                            # marker={'shapeOptions': {}}
                                            )
                dc.on_draw(self.handle_draw)
                self.add_control(dc)

            if tabs:
                display(self, self.tab_widget)
            else:
                display(self)
        else:
            # if len(tabs) > 0:
            if tabs:
                display(self, self.tab_widget)
            else:
                display(self)

        self.is_shown = True

    def show_tab(self, name):
        """ Show only a Tab Widget by calling its name. This is useful mainly
        in Jupyter Lab where you can see outputs in different tab_widget

        :param name: the name of the tab to show
        :type name: str
        """
        try:
            widget = self.tab_children_dict[name]
            display(widget)
        except:
            print('Tab not found')

    def addImage(self, image, visParams=None, name=None, show=True,
                 opacity=None, replace=True):
        """ Add an ee.Image to the Map

        :param image: Image to add to Map
        :type image: ee.Image
        :param visParams: visualization parameters. Can have the
            following arguments: bands, min, max.
        :type visParams: dict
        :param name: name for the layer
        :type name: str
        :return: the name of the added layer
        :rtype: str
        """
        # Check if layer exists
        if name in self.EELayers.keys():
            if not replace:
                msg = "Image with name '{}' exists already, please choose " \
                      "another name"
                print(msg.format(name))
                return
            else:
                # Get URL, attribution & vis params
                params = get_image_tile(image, visParams, show, opacity)

                # Remove Layer
                self.removeLayer(name)
        else:
            # Get URL, attribution & vis params
            params = get_image_tile(image, visParams, show, opacity)

        layer = ipyleaflet.TileLayer(url=params['url'],
                                     attribution=params['attribution'],
                                     name=name)

        EELayer = {'type': 'Image',
                   'object': image,
                   'visParams': params['visParams'],
                   'layer': layer}

        # self._add_EELayer(name, EELayer)
        # return name
        return EELayer

    def addMarker(self, marker, visParams=None, name=None, show=True,
                  opacity=None, replace=True,
                  inspect={'data':None, 'reducer':None, 'scale':None}):
        ''' General method to add Geometries, Features or FeatureCollections
        as Markers '''

        if isinstance(marker, ee.Geometry):
            self.addGeometry(marker, visParams, name, show, opacity, replace,
                             inspect)

        elif isinstance(marker, ee.Feature):
            self.addFeature(marker, visParams, name, show, opacity, replace,
                             inspect)

        elif isinstance(marker, ee.FeatureCollection):
            geometry = marker.geometry()
            self.addGeometry(marker, visParams, name, show, opacity, replace,
                             inspect)

    def addFeature(self, feature, visParams=None, name=None, show=True,
                    opacity=None, replace=True,
                    inspect={'data':None, 'reducer':None, 'scale':None}):
        """ Add a Feature to the Map

        :param feature: the Feature to add to Map
        :type feature: ee.Feature
        :param visParams:
        :type visParams: dict
        :param name: name for the layer
        :type name: str
        :param inspect: when adding a geometry or a feature you can pop up data
            from a desired layer. Params are:
            :data: the EEObject where to get the data from
            :reducer: the reducer to use
            :scale: the scale to reduce
        :type inspect: dict
        :return: the name of the added layer
        :rtype: str
        """
        thename = name if name else 'Feature {}'.format(self.added_geometries)

        # Check if layer exists
        if thename in self.EELayers.keys():
            if not replace:
                print("Layer with name '{}' exists already, please choose another name".format(thename))
                return
            else:
                self.removeLayer(thename)

        params = get_geojson_tile(feature, thename, inspect)
        layer = ipyleaflet.GeoJSON(data=params['geojson'],
                                   name=thename,
                                   popup=HTML(params['pop']))

        self._add_EELayer(thename, {'type': 'Feature',
                                    'object': feature,
                                    'visParams': None,
                                    'layer': layer})
        return thename

    def addGeometry(self, geometry, visParams=None, name=None, show=True,
                    opacity=None, replace=True,
                    inspect={'data':None, 'reducer':None, 'scale':None}):
        """ Add a Geometry to the Map

        :param geometry: the Geometry to add to Map
        :type geometry: ee.Geometry
        :param visParams:
        :type visParams: dict
        :param name: name for the layer
        :type name: str
        :param inspect: when adding a geometry or a feature you can pop up data
            from a desired layer. Params are:
            :data: the EEObject where to get the data from
            :reducer: the reducer to use
            :scale: the scale to reduce
        :type inspect: dict
        :return: the name of the added layer
        :rtype: str
        """
        thename = name if name else 'Geometry {}'.format(self.added_geometries)

        # Check if layer exists
        if thename in self.EELayers.keys():
            if not replace:
                print("Layer with name '{}' exists already, please choose another name".format(thename))
                return
            else:
                self.removeLayer(thename)

        params = get_geojson_tile(geometry, thename, inspect)
        layer = ipyleaflet.GeoJSON(data=params['geojson'],
                                   name=thename,
                                   popup=HTML(params['pop']))

        self._add_EELayer(thename, {'type': 'Geometry',
                                      'object': geometry,
                                      'visParams':None,
                                      'layer': layer})
        return thename

    def addFeatureLayer(self, feature, visParams=None, name=None, show=True,
                        opacity=None, replace=True):
        ''' Paint a Feature on the map, but the layer underneath is the
        actual added Feature '''

        visParams = visParams if visParams else {}

        if isinstance(feature, ee.Feature):
            ty = 'Feature'
        elif isinstance(feature, ee.FeatureCollection):
            ty = 'FeatureCollection'
        else:
            print('The object is not a Feature or FeatureCollection')
            return

        fill_color = visParams.get('fill_color', None)

        if 'outline_color' in visParams:
            out_color = visParams['outline_color']
        elif 'border_color' in visParams:
            out_color = visParams['border_color']
        else:
            out_color = 'black'

        outline = visParams.get('outline', 2)

        proxy_layer = maptool.paint(feature, out_color, fill_color, outline)

        thename = name if name else '{} {}'.format(ty, self.added_geometries)

        img_params = {'bands':['vis-red', 'vis-green', 'vis-blue'],
                      'min': 0, 'max':255}

        # Check if layer exists
        if thename in self.EELayers.keys():
            if not replace:
                print("{} with name '{}' exists already, please choose another name".format(ty, thename))
                return
            else:
                # Get URL, attribution & vis params
                params = get_image_tile(proxy_layer, img_params, show, opacity)

                # Remove Layer
                self.removeLayer(thename)
        else:
            # Get URL, attribution & vis params
            params = get_image_tile(proxy_layer, img_params, show, opacity)

        layer = ipyleaflet.TileLayer(url=params['url'],
                                     attribution=params['attribution'],
                                     name=thename)

        self._add_EELayer(thename, {'type': ty,
                                    'object': feature,
                                    'visParams': visParams,
                                    'layer': layer})
        return thename

    def addMosaic(self, collection, visParams=None, name=None, show=False,
                  opacity=None, replace=True):
        ''' Add an ImageCollection to EELayer and its mosaic to the Map.
        When using the inspector over this layer, it will print all values from
        the collection '''
        proxy = ee.ImageCollection(collection).sort('system:time_start')
        mosaic = ee.Image(proxy.mosaic())

        EELayer = self.addImage(mosaic, visParams, name, show, opacity, replace)
        # modify EELayer
        EELayer['type'] = 'ImageCollection'
        EELayer['object'] = ee.ImageCollection(collection)
        return EELayer

    def addImageCollection(self, collection, visParams=None, nametags=['id'],
                           show=False, opacity=None):
        """ Add every Image of an ImageCollection to the Map

        :param collection: the ImageCollection
        :type collection: ee.ImageCollection
        :param visParams: visualization parameter for each image. See `addImage`
        :type visParams: dict
        :param nametags: tags that will be the name for each image. It must be
            a list in which each element is a string. Each string can be any
            Image property, or one of the following:
            - system_date: the name will be the date of each Image
            - id: the name will be the ID of each Image (Default)
        :type nametags: list
        :param show: If True, adds and shows the Image, otherwise only add it
        :type show: bool
        """
        size = collection.size().getInfo()
        collist = collection.toList(size)
        separation = ' '
        for inx in range(size):
            img = ee.Image(collist.get(inx))
            name = ''
            properties = img.propertyNames().getInfo()
            for nametag in nametags:
                if nametag == 'id':
                    newname = img.id().getInfo()
                elif nametag == 'system_date':
                    newname = ee.Date(img.date()).format('YYYY-MM-dd').getInfo()
                elif nametag in properties:
                    newname = "{}:{}{}".format(nametag, img.get(nametag).getInfo(), separation)
                else:
                    newname = img.id().getInfo()

                name += newname
            self.addLayer(img, visParams, str(name), show, opacity)

    def addLayer(self, eeObject, visParams=None, name=None, show=True,
                 opacity=None, replace=True, **kwargs):
        """ Adds a given EE object to the map as a layer.

        :param eeObject: Earth Engine object to add to map
        :type eeObject: ee.Image || ee.Geometry || ee.Feature
        :param replace: if True, if there is a layer with the same name, this
            replace that layer.
        :type replace: bool

        For ee.Image and ee.ImageCollection see `addImage`
        for ee.Geometry and ee.Feature see `addGeometry`
        """
        visParams = visParams if visParams else {}

        # CASE: ee.Image
        if isinstance(eeObject, ee.Image):
            image_name = name if name else 'Image {}'.format(self.added_images)
            EELayer = self.addImage(eeObject, visParams=visParams,
                                    name=image_name, show=show,
                                    opacity=opacity, replace=replace)

            self._add_EELayer(image_name, EELayer)
            added_layer = EELayer

        # CASE: ee.Geometry
        elif isinstance(eeObject, ee.Geometry):
            geom = eeObject if isinstance(eeObject, ee.Geometry) else eeObject.geometry()
            kw = {'visParams':visParams, 'name':name, 'show':show, 'opacity':opacity}
            if kwargs.get('inspect'): kw.setdefault('inspect', kwargs.get('inspect'))
            added_layer = self.addGeometry(geom, replace=replace, **kw)

        # CASE: ee.Feature & ee.FeatureCollection
        elif isinstance(eeObject, ee.Feature) or isinstance(eeObject, ee.FeatureCollection):
            feat = eeObject
            kw = {'visParams':visParams, 'name':name, 'show':show, 'opacity':opacity}
            added_layer = self.addFeatureLayer(feat, replace=replace, **kw)

        # CASE: ee.ImageCollection
        elif isinstance(eeObject, ee.ImageCollection):
            '''
            proxy = eeObject.sort('system:time_start')
            mosaic = ee.Image(proxy.mosaic())
            added_layer = self.addImage(mosaic, visParams=visParams, name=thename,
                                        show=show, opacity=opacity, replace=replace)
            '''
            thename = name if name else 'ImageCollection {}'.format(self.added_images)
            EELayer = self.addMosaic(eeObject, visParams, thename, show,
                                     opacity, replace)
            self._add_EELayer(thename, EELayer)

            added_layer = EELayer

        else:
            added_layer = None
            print("`addLayer` doesn't support adding {} objects to the map".format(type(eeObject)))

        # return added_layer

    def removeLayer(self, name):
        """ Remove a layer by its name """
        if name in self.EELayers.keys():
            self._remove_EELayer(name)
        else:
            print('Layer {} is not present in the map'.format(name))
            return

    def getLayer(self, name):
        """ Get a layer by its name

        :param name: the name of the layer
        :type name: str
        :return: The complete EELayer which is a dict of

            :type: the type of the layer
            :object: the EE Object associated with the layer
            :visParams: the visualization parameters of the layer
            :layer: the TileLayer added to the Map (ipyleaflet.Map)

        :rtype: dict
        """
        if name in self.EELayers:
            layer = self.EELayers[name]
            return layer
        else:
            print('Layer {} is not present in the map'.format(name))
            return

    def getObject(self, name):
        ''' Get the EE Object from a layer's name '''
        obj = self.getLayer(name)['object']
        return obj

    def getVisParams(self, name):
        ''' Get the Visualization Parameters from a layer's name '''
        vis = self.getLayer(name)['visParams']
        return vis

    def centerObject(self, eeObject, zoom=None, method=1):
        """ Center an eeObject

        :param eeObject:
        :param zoom:
        :param method: experimetal methods to estimate zoom for fitting bounds
            Currently: 1 or 2
        :type: int
        """
        bounds = get_bounds(eeObject)
        if bounds:
            try:
                inverse = inverse_coordinates(bounds)
                centroid = ee.Geometry.Polygon(inverse)\
                             .centroid().getInfo()['coordinates']
            except:
                centroid = [0, 0]

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

    def getBounds(self, asGeoJSON=True):
        """ Returns the bounds of the current map view, as a list in the
        format [west, south, east, north] in degrees.

        Arguments:
        asGeoJSON (Boolean, optional):
        If true, returns map bounds as GeoJSON.

        Returns: GeoJSONGeometry|List<Number>|String
        """
        bounds = inverse_coordinates(self.bounds)
        if asGeoJSON:
            return ee.Geometry.Rectangle(bounds)
        else:
            return bounds

    def _update_tab_children(self):
        """ Update Tab children from tab_children_dict """
        # Set tab_widget children
        self.tab_widget.children = tuple(self.tab_children_dict.values())
        # Set tab_widget names
        for i, name in enumerate(self.tab_children_dict.keys()):
            self.tab_widget.set_title(i, name)

    def addTab(self, name, handler=None, widget=None):
        """ Add a Tab to the Panel. The handler is for the Map

        :param name: name for the new tab
        :type name: str
        :param handler: handle function for the new tab. Arguments of the
        function are:

          - type: the type of the event (click, mouseover, etc..)
          - coordinates: coordinates where the event occurred [lon, lat]
          - widget: the widget inside the Tab
          - map: the Map instance

        :param widget: widget inside the Tab. Defaults to HTML('')
        :type widget: ipywidgets.Widget
        """
        # Widget
        wid = widget if widget else HTML('')
        # Get tab's children as a list
        # tab_children = list(self.tab_widget.children)
        tab_children = self.tab_children_dict.values()
        # Get a list of tab's titles
        # titles = [self.tab_widget.get_title(i) for i, child in enumerate(tab_children)]
        titles = self.tab_children_dict.keys()
        # Check if tab already exists
        if name not in titles:
            ntabs = len(tab_children)

            # UPDATE DICTS
            # Add widget as a new children
            self.tab_children_dict[name] = wid
            # Set the handler for the new tab
            if handler:
                def proxy_handler(f):
                    def wrap(**kwargs):
                        # Add widget to handler arguments
                        kwargs['widget'] = self.tab_children_dict[name]
                        coords = kwargs['coordinates']
                        kwargs['coordinates'] = inverse_coordinates(coords)
                        kwargs['map'] = self
                        return f(**kwargs)
                    return wrap
                self.handlers[name] = proxy_handler(handler)
            else:
                self.handlers[name] = handler

            # Update tab children
            self._update_tab_children()
        else:
            print('Tab {} already exists, please choose another name'.format(name))

    def handle_change_tab(self, change):
        """ Handle function to trigger when tab changes """
        # Remove all handlers
        if change['name'] == 'selected_index':
            old = change['old']
            new = change['new']
            old_name = self.tab_widget.get_title(old)
            new_name = self.tab_widget.get_title(new)
            # Remove all handlers
            for handl in self.handlers.values():
                self.on_interaction(handl, True)
            # Set new handler if not None
            if new_name in self.handlers.keys():
                handler = self.handlers[new_name]
                if handler:
                    self.on_interaction(handler)

    def handle_inspector(self, **change):
        """ Handle function for the Inspector Widget """
        # Get click coordinates
        coords = change['coordinates']

        event = change['type'] # event type
        if event == 'click':  # If the user clicked
            # create a point where the user clicked
            point = ee.Geometry.Point(coords)

            # Get widget
            thewidget = change['widget'].main  # Accordion

            # First Accordion row text (name)
            first = 'Point {} at {} zoom'.format(coords, self.zoom)
            namelist = [first]
            wids4acc = [HTML('')] # first row has no content

            # Get only Selected Layers in the Inspector Selector
            selected_layers = dict(zip(self.inspector_wid.selector.label,
                                       self.inspector_wid.selector.value))

            length = len(selected_layers.keys())
            i = 1

            for name, obj in selected_layers.items(): # for every added layer
                # Clear children // Loading
                thewidget.children = [HTML('wait a second please..')]
                thewidget.set_title(0, 'Loading {} of {}...'.format(i, length))
                i += 1

                # Image
                if obj['type'] == 'Image':
                    # Get the image's values
                    try:
                        image = obj['object']
                        values = tools.image.get_value(image, point,
                                                       scale=ZOOM_SCALE[self.zoom],
                                                       side='client')
                        values = tools.dictionary.sort(values)
                        # Create the content
                        img_html = ''
                        for band, value in values.items():
                            img_html += '<b>{}</b>: {}</br>'.format(band,
                                                                    value)
                        wid = HTML(img_html)
                        # append widget to list of widgets
                        wids4acc.append(wid)
                        namelist.append(name)
                    except Exception as e:
                        # wid = HTML(str(e).replace('<','{').replace('>','}'))
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        trace = traceback.format_exception(exc_type, exc_value,
                                                           exc_traceback)
                        wid = ErrorAccordion(e, trace)
                        wids4acc.append(wid)
                        namelist.append('ERROR at layer {}'.format(name))

                # ImageCollection
                if obj['type'] == 'ImageCollection':
                    # Get the values from all images
                    try:
                        collection = obj['object']
                        values = tools.image.get_values(collection, point, scale=1,
                                                  properties=['system:time_start'],
                                                  side='client')

                        # header
                        allbands = [val.keys() for bands, val in values.items()]
                        bands = []
                        for bandlist in allbands:
                            for band in bandlist:
                                if band not in bands:
                                    bands.append(band)

                        header = ['image']+bands

                        # rows
                        rows = []
                        for imgid, val in values.items():
                            row = ['']*len(header)
                            row[0] = str(imgid)
                            for bandname, bandvalue in val.items():
                                pos = header.index(bandname) if bandname in header else None
                                if pos:
                                    row[pos] = str(bandvalue)
                            rows.append(row)

                        # Create the content
                        html = maptool.create_html_table(header, rows)
                        wid = HTML(html)
                        # append widget to list of widgets
                        wids4acc.append(wid)
                        namelist.append(name)
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        trace = traceback.format_exception(exc_type, exc_value,
                                                           exc_traceback)
                        wid = ErrorAccordion(e, trace)
                        wids4acc.append(wid)
                        namelist.append('ERROR at layer {}'.format(name))

                # Features
                if obj['type'] == 'Feature':
                    try:
                        feat = obj['object']
                        feat_geom = feat.geometry()
                        if feat_geom.contains(point).getInfo():
                            info = feature_properties_output(feat)
                            wid = HTML(info)
                            # append widget to list of widgets
                            wids4acc.append(wid)
                            namelist.append(name)
                    except Exception as e:
                        # wid = HTML(str(e).replace('<','{').replace('>','}'))
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        trace = traceback.format_exception(exc_type, exc_value,
                                                           exc_traceback)
                        wid = ErrorAccordion(e, trace)
                        wids4acc.append(wid)
                        namelist.append('ERROR at layer {}'.format(name))

                # FeatureCollections
                if obj['type'] == 'FeatureCollection':
                    try:
                        fc = obj['object']
                        filtered = fc.filterBounds(point)
                        if filtered.size().getInfo() > 0:
                            feat = ee.Feature(filtered.first())
                            info = feature_properties_output(feat)
                            wid = HTML(info)
                            # append widget to list of widgets
                            wids4acc.append(wid)
                            namelist.append(name)
                    except Exception as e:
                        wid = HTML(str(e).replace('<','{').replace('>','}'))
                        wids4acc.append(wid)
                        namelist.append('ERROR at layer {}'.format(name))

            # Set children and children's name of inspector widget
            thewidget.children = wids4acc
            for i, n in enumerate(namelist):
                thewidget.set_title(i, n)

    def handle_object_inspector(self, **change):
        """ Handle function for the Object Inspector Widget

        DEPRECATED
        """
        event = change['type'] # event type
        thewidget = change['widget']
        if event == 'click':  # If the user clicked
            # Clear children // Loading
            thewidget.children = [HTML('wait a second please..')]
            thewidget.set_title(0, 'Loading...')

            widgets = []
            i = 0

            for name, obj in self.EELayers.items(): # for every added layer
                the_object = obj['object']
                try:
                    properties = the_object.getInfo()
                    wid = ipytools.create_accordion(properties) # Accordion
                    wid.selected_index = None # this will unselect all
                except Exception as e:
                    wid = HTML(str(e))
                widgets.append(wid)
                thewidget.set_title(i, name)
                i += 1

            thewidget.children = widgets

    def handle_draw(self, dc_widget, action, geo_json):
        """ Handles drawings """
        ty = geo_json['geometry']['type']
        coords = geo_json['geometry']['coordinates']
        geom = self.draw_types[ty](coords)
        if action == 'created':
            self.addGeometry(geom)
        elif action == 'deleted':
            for key, val in self.EELayers.items():
                if geom == val:
                    self.removeLayer(key)


class CustomInspector(HBox):
    def __init__(self, **kwargs):
        desc = 'Select one or more layers'
        super(CustomInspector, self).__init__(description=desc, **kwargs)
        self.selector = SelectMultiple()
        self.main = Accordion()
        self.children = [self.selector, self.main]


class ErrorAccordion(Accordion):
    def __init__(self, error, traceback, **kwargs):
        super(ErrorAccordion, self).__init__(**kwargs)
        self.error = '{}'.format(error).replace('<','{').replace('>','}')

        newtraceback = ''
        for trace in traceback[1:]:
            newtraceback += '{}'.format(trace).replace('<','{').replace('>','}')
            newtraceback += '</br>'

        self.traceback = newtraceback

        self.errorWid = HTML(self.error)

        self.traceWid = HTML(self.traceback)

        self.children = (self.errorWid, self.traceWid)
        self.set_title(0, 'ERROR')
        self.set_title(1, 'TRACEBACK')


class LayersWidget(ipytools.RealBox):
    def __init__(self, map=None, **kwargs):
        super(LayersWidget, self).__init__(**kwargs)
        self.map = map
        self.selector = Select()

        # define init EELayer
        self.EELayer = None

        # Buttons
        self.center = Button(description='Center')
        self.center.on_click(self.on_click_center)

        self.remove = Button(description='Remove')
        self.remove.on_click(self.on_click_remove)

        self.show_prop = Button(description='Show Object')
        self.show_prop.on_click(self.on_click_show_object)

        self.vis = Button(description='Visualization')
        self.vis.on_click(self.on_click_vis)

        self.move_up = Button(description='Move up')
        self.move_up.on_click(self.on_up)

        self.move_down = Button(description='Move down')
        self.move_down.on_click(self.on_down)

        # Buttons Group 1
        self.group1 = VBox([self.center, self.remove,
                            self.vis, self.show_prop])

        # Buttons Group 2
        self.group2 = VBox([self.move_up, self.move_down])

        # self.children = [self.selector, self.group1]
        self.items = [[self.selector, self.group1, self.group2]]

        self.selector.observe(self.handle_selection, names='value')

    def on_up(self, button=None):
        if self.EELayer:
            self.map.move_layer(self.layer.name, 'up')

    def on_down(self, button=None):
        if self.EELayer:
            self.map.move_layer(self.layer.name, 'down')

    def handle_selection(self, change):
        new = change['new']
        self.EELayer = new

        # set original display
        self.items = [[self.selector, self.group1, self.group2]]

        if new:
            self.layer = new['layer']
            self.obj = new['object']
            self.ty = new['type']
            self.vis = new['visParams']

    def on_click_show_object(self, button=None):
        if self.EELayer:
            loading = HTML('Loading <b>{}</b>...'.format(self.layer.name))
            widget = VBox([loading])
            # widget = ipytools.create_object_output(self.obj)
            thread = threading.Thread(target=ipytools.create_async_output,
                                      args=(self.obj, widget))
            self.items = [[self.selector, self.group1],
                          [widget]]
            thread.start()

    def on_click_center(self, button=None):
        if self.EELayer:
            self.map.centerObject(self.obj)

    def on_click_remove(self, button=None):
        if self.EELayer:
            self.map.removeLayer(self.layer.name)

    def on_click_vis(self, button=None):
        if self.EELayer:
            # options
            selector = self.selector
            group1 = self.group1

            # map
            map = self.map
            layer_name = self.layer.name
            image = self.obj

            # Image Bands
            try:
                info = self.obj.getInfo()
            except Exception as e:
                self.items = [[self.selector, self.group1],
                              [HTML(str(e))]]
                return

            # IMAGES
            if self.ty == 'Image':
                ### image data ###
                bands = info['bands']
                imbands = [band['id'] for band in bands]
                bands_type = [band['data_type']['precision'] for band in bands]
                bands_min = []
                bands_max = []
                # as float bands don't hava an specific range, reduce region to get the
                # real range
                if 'float' in bands_type:
                    try:
                        minmax = image.reduceRegion(ee.Reducer.minMax())
                        for band in bands:
                            bandname = band['id']
                            try:
                                tmin = minmax.get('{}_min'.format(bandname)).getInfo() # 0
                                tmax = minmax.get('{}_max'.format(bandname)).getInfo() # 1
                            except:
                                tmin = 0
                                tmax = 1
                            bands_min.append(tmin)
                            bands_max.append(tmax)
                    except:
                        for band in bands:
                            dt = band['data_type']
                            try:
                                tmin = dt['min']
                                tmax = dt['max']
                            except:
                                tmin = 0
                                tmax = 1
                            bands_min.append(tmin)
                            bands_max.append(tmax)
                else:
                    for band in bands:
                        dt = band['data_type']
                        try:
                            tmin = dt['min']
                            tmax = dt['max']
                        except:
                            tmin = 0
                            tmax = 1
                        bands_min.append(tmin)
                        bands_max.append(tmax)


                # dict of {band: min} and {band:max}
                min_dict = dict(zip(imbands, bands_min))
                max_dict = dict(zip(imbands, bands_max))
                ######

                # Layer data
                layer_data = self.map.EELayers[layer_name]
                visParams = layer_data['visParams']

                # vis bands
                visBands = visParams['bands'].split(',')

                # vis min
                visMin = visParams['min']
                if isinstance(visMin, str):
                    visMin = [float(vis) for vis in visMin.split(',')]
                else:
                    visMin = [visMin]

                # vis max
                visMax = visParams['max']
                if isinstance(visMax, str):
                    visMax = [float(vis) for vis in visMax.split(',')]
                else:
                    visMax = [visMax]

                # dropdown handler
                def handle_dropdown(band_slider):
                    def wrap(change):
                        new = change['new']
                        band_slider.min = min_dict[new]
                        band_slider.max = max_dict[new]
                    return wrap

                def slider_1band(float=False, name='band'):
                    ''' Create the widget for one band '''
                    # get params to set in slider and dropdown
                    vismin = visMin[0]
                    vismax = visMax[0]
                    band = visBands[0]

                    drop = Dropdown(description=name, options=imbands, value=band)

                    if float:
                        slider = ipytools.FloatBandWidget(min=min_dict[drop.value],
                                                          max=max_dict[drop.value])
                    else:
                        slider = FloatRangeSlider(min=min_dict[drop.value],
                                                  max=max_dict[drop.value],
                                                  value=[vismin, vismax],
                                                  step=0.01)
                    # set handler
                    drop.observe(handle_dropdown(slider), names=['value'])

                    # widget for band selector + slider
                    band_slider = HBox([drop, slider])
                    # return VBox([band_slider], layout=Layout(width='500px'))
                    return band_slider

                def slider_3bands(float=False):
                    ''' Create the widget for one band '''
                    # get params to set in slider and dropdown
                    if len(visMin) == 1:
                        visminR = visminG = visminB = visMin[0]
                    else:
                        visminR = visMin[0]
                        visminG = visMin[1]
                        visminB = visMin[2]

                    if len(visMax) == 1:
                        vismaxR = vismaxG = vismaxB = visMax[0]
                    else:
                        vismaxR = visMax[0]
                        vismaxG = visMax[1]
                        vismaxB = visMax[2]

                    if len(visBands) == 1:
                        visbandR = visbandG = visbandB = visBands[0]
                    else:
                        visbandR = visBands[0]
                        visbandG = visBands[1]
                        visbandB = visBands[2]

                    drop = Dropdown(description='red', options=imbands, value=visbandR)
                    drop2 = Dropdown(description='green', options=imbands, value=visbandG)
                    drop3 = Dropdown(description='blue', options=imbands, value=visbandB)
                    slider = FloatRangeSlider(min=min_dict[drop.value],
                                              max=max_dict[drop.value],
                                              value=[visminR, vismaxR],
                                              step=0.01)
                    slider2 = FloatRangeSlider(min=min_dict[drop2.value],
                                               max=max_dict[drop2.value],
                                               value=[visminG, vismaxG],
                                               step=0.01)
                    slider3 = FloatRangeSlider(min=min_dict[drop3.value],
                                               max=max_dict[drop3.value],
                                               value=[visminB, vismaxB],
                                               step=0.01)
                    # set handlers
                    drop.observe(handle_dropdown(slider), names=['value'])
                    drop2.observe(handle_dropdown(slider2), names=['value'])
                    drop3.observe(handle_dropdown(slider3), names=['value'])

                    # widget for band selector + slider
                    band_slider = HBox([drop, slider])
                    band_slider2 = HBox([drop2, slider2])
                    band_slider3 = HBox([drop3, slider3])

                    return VBox([band_slider, band_slider2, band_slider3],
                                layout=Layout(width='700px'))

                # Create widget for 1 or 3 bands
                bands = RadioButtons(options=['1 band', '3 bands'],
                                     layout=Layout(width='80px'))

                # Create widget for band, min and max selection
                selection = slider_1band()

                # Apply button
                apply = Button(description='Apply', layout=Layout(width='100px'))

                # new row
                new_row = [bands, selection, apply]

                # update row of widgets
                def update_row_items(new_row):
                    self.items = [[selector, group1],
                                   new_row]

                # handler for radio button (1 band / 3 bands)
                def handle_radio_button(change):
                    new = change['new']
                    if new == '1 band':
                        # create widget
                        selection = slider_1band() # TODO
                        # update row of widgets
                        update_row_items([bands, selection, apply])
                    else:
                        red = slider_1band(name='red') # TODO
                        green = slider_1band(name='green')
                        blue = slider_1band(name='blue')
                        selection = VBox([red, green, blue])
                        # selection = slider_3bands()
                        update_row_items([bands, selection, apply])

                def handle_apply(button):
                    radio = self.items[1][0].value # radio button
                    vbox = self.items[1][1]
                    print('vbox', vbox)
                    if radio == '1 band':  # 1 band
                        hbox_band = vbox.children[0].children

                        band = hbox_band[0].value
                        min = hbox_band[1].value[0]
                        max = hbox_band[1].value[1]

                        map.addLayer(image, {'bands':[band], 'min':min, 'max':max},
                                     layer_name)
                    else:  # 3 bands
                        hbox_bandR = vbox.children[0].children
                        hbox_bandG = vbox.children[1].children
                        hbox_bandB = vbox.children[2].children

                        bandR = hbox_bandR[0].value
                        bandG = hbox_bandG[0].value
                        bandB = hbox_bandB[0].value

                        minR = hbox_bandR[1].value[0]
                        minG = hbox_bandG[1].value[0]
                        minB = hbox_bandB[1].value[0]

                        maxR = hbox_bandR[1].value[1]
                        maxG = hbox_bandG[1].value[1]
                        maxB = hbox_bandB[1].value[1]

                        map.addLayer(image, {'bands':[bandR, bandG, bandB],
                                             'min':[float(minR), float(minG), float(minB)],
                                             'max':[float(maxR), float(maxG), float(maxB)]},
                                     layer_name)

                bands.observe(handle_radio_button, names='value')
                update_row_items(new_row)
                apply.on_click(handle_apply)