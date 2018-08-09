# coding=utf-8
''' Charts from Google Earth Engine data. Inpired by this question
https://gis.stackexchange.com/questions/291823/ui-charts-for-indices-time-series-in-python-api-of-google-earth-engine
and https://youtu.be/FytuB8nFHPQ, but at the moment relaying on `pygal`
library because it's the easiest to integrate with ipywidgets

author: Rodrigo E. Principe
author email: fitoprincipe82@gmail.com
gitHub: https://github.com/gee-community/gee_tools
'''

import pygal
import base64
import ee
from . import tools
import pandas as pd


class Line(pygal.Line):
    def __init__(self, **kwargs):
        super(Line, self).__init__(**kwargs)
        self.data = None
        self.y_labels = dict()

    @staticmethod
    def from_pandas(dataframe, x=None, y=None, datetime=False, **kwargs):
        ''' Creates a Line chart from a pandas dataFrame '''
        if not isinstance(dataframe, pd.DataFrame):
            raise ValueError('first argument must be a pandas DataFrame')

        line_chart = Line(**kwargs)

        if not x:
            labels = dataframe[dataframe.columns[0]]
        else:
            labels = dataframe[x].values.tolist()

        if not datetime:
            x_values = labels
        else:
            x_values = [tools.Date.millis2datetime(d) for d in labels]

        line_chart.x_labels = x_values

        if isinstance(y, list):
            for column in y:
                if column == x:
                    continue
                ydata = dataframe[column].values.tolist()
                line_chart.add(column, ydata)
                line_chart.y_labels[column] = ydata
        else:
            ydata = dataframe[y].values.tolist()
            line_chart.add(y, ydata)
            line_chart.y_labels[y] = ydata

        line_chart.data = dataframe
        return line_chart

    def render_widget(self):
        from ipywidgets import HTML

        b64 = base64.b64encode(self.render())
        src = 'data:image/svg+xml;charset=utf-8;base64,'+b64

        return HTML('<embed src={}></embed>'.format(src))


class Image(object):
    ''' Charts for Images '''
    def __init__(self, source):
        self.source = source

    @staticmethod
    def create_widget(pygal_chart):
        ''' Create a HTML Widget (ipywidget) '''
        from ipywidgets import HTML

        b64 = base64.b64encode(pygal_chart.render())
        src = 'data:image/svg+xml;charset=utf-8;base64,'+b64

        return HTML('<embed src={}></embed>'.format(src))


    @staticmethod
    def data2pandas(data):
        ''' Convert data coming from tools.get_values to a pandas DataFrame'''
        # Indices
        # header
        allbands = [val.keys() for bands, val in data.items()]
        header = []
        for bandlist in allbands:
            for band in bandlist:
                if band not in header:
                    header.append(band)

        data_dict = {}
        indices = []
        for i, head in enumerate(header):
            band_data = []
            for iid, val in data.items():
                if i == 0:
                    indices.append(iid)
                # for bandname, bandvalue in val.items():
                band_data.append(val[head])
            data_dict[head] = band_data

        df = pd.DataFrame(data=data_dict, index=indices)

        return df


    @staticmethod
    def check_imageCollection(imageCollection):
        if not isinstance(imageCollection, ee.ImageCollection):
            msg = 'first parameter of Image.doySeries must be an ' \
                  'ImageCollection, found {}'
            raise ValueError(msg.format(type(imageCollection)))

    @staticmethod
    def series(imageCollection, region, reducer=ee.Reducer.mean(),
               scale=None, xProperty='system:time_start', bands=None):
        Image.check_imageCollection(imageCollection)

        # scale
        if not scale:
            scale = 1

        # first image (for getting bands and properties)
        first = ee.Image(imageCollection.first())
        allbands = first.bandNames().getInfo()

        # Get Y (bands)
        if not bands:
            ydata = allbands
        else:
            ydata = bands

        # Get Images properties
        properties = first.propertyNames().getInfo()

        # If xProperty == 'system:time_start' will compute datetime
        datetime = True if xProperty == 'system:time_start' else False

        # generate data
        data = {}
        if isinstance(region, ee.Geometry):
            geom = region
        elif isinstance(region, (ee.Feature, ee.FeatureCollection)):
            geom = region.geometry()

        if xProperty in properties:
            # include xProperty in data
            x_property = [xProperty]
            selection_bands = ydata
        elif xProperty in allbands:
            # xProperty will be included in data because is a band
            x_property = []
            if xProperty not in ydata:
                selection_bands = ydata + [xProperty]
        else:
            msg = 'xProperty "{}" not found in properties or bands'
            raise ValueError(msg.format(xProperty))

        data = tools.get_values(imageCollection, geom, reducer, scale,
                                properties=x_property, side='client')

        df = Image.data2pandas(data)
        newdf = df.sort_values(xProperty)

        line_chart = Line.from_pandas(newdf, y=ydata,
                                      x=xProperty, datetime=datetime)

        return line_chart

    @staticmethod
    def seriesByRegion(imageCollection, regions, reducer, band=None,
                       scale=None, xProperty='system:time_start',
                       seriesProperty='system:index'):

        Image.check_imageCollection(imageCollection)
        first = ee.Image(imageCollection.first())

        # Make defaults
        if not band:
            band = ee.String(first.bandNames().get(0))
        if not scale:
            # scale = first.select([0]).projection().nominalScale()
            scale = 1

        # Generate data
        # Geometry
        if isinstance(regions, ee.Geometry):
            reduction = ee.Image(imageCollection.reduce(reducer))
            data = reduction.reduceRegion(ee.Reducer.first(),
                                          regions, scale, maxPixels=1e13)
