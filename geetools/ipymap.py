# coding=utf-8

''' This module is designed to use ONLY in the Jupyter Notebook. It is
 inspired on Tyler Erickson's contribution on
https://github.com/gee-community/ee-jupyter-contrib/blob/master/examples/getting-started/display-interactive-map.ipynb'''

import ipyleaflet
from ipywidgets import HTML, Tab, Text, Accordion, Checkbox, HBox, Output,\
                       Label, VBox, SelectMultiple, link
from IPython.display import display
from traitlets import List, Dict
import ee
if not ee.data._initialized: ee.Initialize()
from collections import OrderedDict
from . import tools
from .maptool import get_default_vis, inverse_coordinates, get_data,\
                     get_image_tile, get_geojson_tile, get_bounds, get_zoom,\
                     create_html
from . import ipytools

import json
import time

class Map(ipyleaflet.Map):
    tab_children_dict = Dict()
    def __init__(self, **kwargs):
        # Change defaults
        kwargs.setdefault('center', [0, 0])
        kwargs.setdefault('zoom', 2)
        super(Map, self).__init__(**kwargs)
        self.is_shown = False
        self.EELayers = {}

        # TABS
        # Tab widget
        self.tab_widget = Tab()
        # Handler for Tab
        self.tab_widget.observe(self.handle_change_tab)

        # Dictonary to hold tab's widgets
        # (tab's name:widget)
        self.tab_names = [] # ['Inspector', 'Objects']
        self.tab_children = [] # [self.inspector_wid, self.object_inspector_wid]
        self.tab_children_dict = OrderedDict(zip(self.tab_names,
                                                 self.tab_children))

        # Dictionary of map's handlers
        self.handlers = {} # {'Inspector': self.handle_inspector, 'Objects': self.handle_object_inspector}

        # As I cannot create a Geometry with a GeoJSON string I do a workaround
        self.draw_types = {'Polygon': ee.Geometry.Polygon,
                           'Point': ee.Geometry.Point,
                           'LineString': ee.Geometry.LineString,
                           }

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

    def show(self, tabs=['Inspector', 'Objects', 'Tasks'],
             layer_control=True, draw_control=False):
        """ Show the Map on the Notebook """
        if not self.is_shown:
            if layer_control:
                # Layers Control
                lc = ipyleaflet.LayersControl()
                self.add_control(lc)
            if draw_control:
                # Draw Control
                dc = ipyleaflet.DrawControl(edit=False,
                                            marker={'shapeOptions': {}})
                dc.on_draw(self.handle_draw)
                self.add_control(dc)

            if len(tabs) > 0:
                # Inspector Widget (Accordion)
                self.inspector_wid = CustomInspector()
                # inspector_wid.update_selector(self)
                # inspector_wid.selected_index = None # this will unselect all
                self.inspector_wid.main.selected_index = None # this will unselect all
                # Object Inspector Widget (Accordion)
                object_inspector_wid = Accordion()
                object_inspector_wid.selected_index = None # this will unselect all
                # Task Manager Widget
                task_manager = ipytools.TaskManager()

                widgets = {'Inspector': self.inspector_wid,
                           'Objects': object_inspector_wid,
                           'Tasks': task_manager,
                           }
                handlers = {'Inspector': self.handle_inspector,
                            'Objects': self.handle_object_inspector,
                            'Tasks': None,
                            }
                for tab in tabs:
                    if tab in widgets.keys():
                        widget = widgets[tab]
                        handler = handlers[tab]
                        self.addTab(tab, handler, widget)
                    else:
                        raise ValueError('Tab {} is not recognized. Choose one of {}'.format(tab, widgets.keys()))
                # First handler: Inspector
                self.on_interaction(self.handlers[tabs[0]])

                # Link tab_children_dict with custom inspector
                # link((inspector_wid.selector, 'options'), (self.tab_children_dict, ))

                display(self, self.tab_widget)
            else:
                display(self)
        else:
            if len(tabs) > 0:
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
        thename = name if name else 'Image {}'.format(self.added_images)

        # Check if layer exists
        if thename in self.EELayers.keys():
            if not replace:
                print("Image with name '{}' exists already, please choose another name".format(thename))
                return
            else:
                self.removeLayer(thename)

        params = get_image_tile(image, visParams, show, opacity)

        layer = ipyleaflet.TileLayer(url=params['url'],
                                     attribution=params['attribution'],
                                     name=thename)
        self.add_layer(layer)
        self.EELayers[thename] = {'type':'Image',
                                  'object':image,
                                  'visParams':visParams,
                                  'layer':layer}
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

        params = get_geojson_tile(geometry,thename, inspect)
        layer = ipyleaflet.GeoJSON(data=params['geojson'],
                                   name=thename,
                                   popup=HTML(params['pop']))
        self.add_layer(layer)
        self.EELayers[thename] = {'type':'Geometry',
                                  'object': geometry,
                                  'visParams':None,
                                  'layer': layer}
        return thename

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
        # CASE: ee.Image
        if isinstance(eeObject, ee.Image):
            added_layer = self.addImage(eeObject, visParams=visParams, name=name,
                                        show=show, opacity=opacity, replace=replace)
        # CASE: ee.Geometry
        elif isinstance(eeObject, ee.Geometry) or isinstance(eeObject, ee.Feature):
            geom = eeObject if isinstance(eeObject, ee.Geometry) else eeObject.geometry()
            kw = {'visParams':visParams, 'name':name, 'show':show, 'opacity':opacity}
            if kwargs.get('inspect'): kw.setdefault('inspect', kwargs.get('inspect'))
            added_layer = self.addGeometry(geom, replace=replace, **kw)
        # CASE: ee.ImageCollection
        elif isinstance(eeObject, ee.ImageCollection):
            proxy = eeObject.sort('system:time_start')
            mosaic = ee.Image(proxy.mosaic())
            thename = name if name else 'Mosaic {}'.format(self.added_images)
            added_layer = self.addImage(mosaic, visParams=visParams, name=thename,
                                        show=show, opacity=opacity, replace=replace)
        elif isinstance(eeObject, ee.FeatureCollection):
            geom = eeObject.geometry()
            kw = {'visParams':visParams, 'name':name, 'show':show, 'opacity':opacity}
            added_layer =  self.addGeometry(geom, replace=replace, **kw)
        else:
            added_layer = None
            print("`addLayer` doesn't support adding {} objects to the map".format(type(eeObject)))

        # Clear options
        self.inspector_wid.selector.options = {}

        # Add layer to the Inspector Widget
        self.inspector_wid.selector.options = self.EELayers

        return added_layer

    def removeLayer(self, name):
        """ Remove a layer by its name """
        if name in self.EELayers.keys():
            layer = self.EELayers[name]['layer']
            self.remove_layer(layer)
            self.EELayers.pop(name)

            # Clear options
            self.inspector_wid.selector.options = {}

            # Add layer to the Inspector Widget
            self.inspector_wid.selector.options = self.EELayers

        else:
            print('Layer {} is not present in the map'.format(name))
            return

    def getLayer(self, name):
        """ Get a layer by its name

        :param name: the name of the layer
        :type name: str
        :return: the EE object from the specified layer
        :rtype: ee.ComputedObject
        """
        if name in self.EELayers.keys():
            layer = self.EELayers[name]
            return layer
        else:
            print('Layer {} is not present in the map'.format(name))
            return

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
        elif isinstance(eeObject, ee.Feature) or isinstance(eeObject, ee.Image):
            centroid = eeObject.geometry().centroid().getInfo()['coordinates']
        elif isinstance(eeObject, list):
            pol = ee.Geometry.Polygon(inverse_coordinates(list))
            centroid = pol.centroid().getInfo()['coordinates']

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
        self.tab_widget.children = self.tab_children_dict.values()
        # Set tab_widget names
        for i, name in enumerate(self.tab_children_dict.keys()):
            self.tab_widget.set_title(i, name)

    def addTab(self, name, handler=None, widget=None):
        """ Add a Tab to the Panel. The handler is for the Map

        :param name: name for the new tab
        :type name: str
        :param handler: handle function for the new tab. Arguments of the
            function are:

            :type: the type of the event (click, mouseover, etc..)
            :coordinates: coordinates where the event occured [lon, lat]
            :widget: the widget inside the Tab
            :map: the Map instance

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
            # thewidget = change['widget']
            thewidget = change['widget'].main

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

                # IMAGES
                if obj['type'] == 'Image':
                    # Get the image's values
                    try:
                        image = obj['object']
                        values = tools.get_value(image, point, 10, 'client')
                        values = tools.sort_dict(values)
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
                        wid = HTML(str(e).replace('<','{').replace('>','}'))
                        wids4acc.append(wid)
                        namelist.append('ERROR at layer {}'.format(name))

            # Set children and children's name of inspector widget
            thewidget.children = wids4acc
            for i, n in enumerate(namelist):
                thewidget.set_title(i, n)

    def handle_object_inspector(self, **change):
        """ Handle function for the Object Inspector Widget """
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