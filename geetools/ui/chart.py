# coding=utf-8
""" Charts from Google Earth Engine data. Inpired by this question
https://gis.stackexchange.com/questions/291823/ui-charts-for-indices-time-series-in-python-api-of-google-earth-engine
and https://youtu.be/FytuB8nFHPQ, but at the moment relaying on `pygal`
library because it's the easiest to integrate with ipywidgets

author: Rodrigo E. Principe
author email: fitoprincipe82@gmail.com
gitHub: https://github.com/gee-community/gee_tools
"""
import pygal
import base64
import ee
from .. import tools
import pandas as pd

# TODO: make not plotted bands values appear on tooltip
# TODO: give capability to plot a secondary axis with other data


def render_widget(chart, width=None, height=None):
    """ Render a pygal chart into a Jupyter Notebook """
    from ipywidgets import HTML

    b64 = base64.b64encode(chart.render()).decode('utf-8')

    src = 'data:image/svg+xml;charset=utf-8;base64,'+b64

    if width and not height:
        html = '<embed src={} width={}></embed>'.format(src, width)
    elif height and not width:
        html = '<embed src={} height={}></embed>'.format(src, height)
    elif width and height:
        html = '<embed src={} height={} width={}></embed>'.format(src,
                                                                  height,
                                                                  width)
    else:
        html = '<embed src={}>'.format(src)

    return HTML(html)


def from_pandas(line_chart, dataframe, x=None, y=None, datetime=False):
    """ Creates a Line chart from a pandas dataFrame """
    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError('first argument must be a pandas DataFrame')

    if not x:
        labels = dataframe[dataframe.columns[0]]
    else:
        labels = dataframe[x].values.tolist()

    if not datetime:
        x_values = labels
    else:
        x_values = [tools.date.millis2datetime(d) for d in labels]

    # add property to parsed line_chart object
    line_chart.x_labels = x_values

    if isinstance(y, list):
        for column in y:
            if column == x:
                continue
            ydata = dataframe[column].values.tolist()
            if datetime:
                # ydata = [(dt, value) for dt, value in zip(x_values, ydata)]
                # ydata = tuple(zip(x_values, ydata))
                nydata = []
                for n, (dt, value) in enumerate(zip(x_values, ydata)):
                    if not pd.isnull(dataframe[column][n]):
                        nydata.append((dt, value))
                ydata = tuple(nydata)
            else:
                ydata = [{'value': data} for data in ydata]

            # TODO: add values config
            # pygal.org/en/latest/documentation/configuration/value.html
            line_chart.add(column, ydata)
            line_chart.y_data[column] = ydata
    else:
        ydata = dataframe[y].values.tolist()
        line_chart.add(y, ydata)
        line_chart.y_data[y] = ydata

    line_chart.data = dataframe
    return line_chart


class Line(pygal.Line):
    def __init__(self, **kwargs):
        super(Line, self).__init__(**kwargs)
        self.data = None
        self.y_data = dict()
        self.x_label_rotation = 30

    def render_widget(self, width=None, height=None):
        """ Render a pygal chart into a Jupyter Notebook """
        return render_widget(self, width, height)


class DateTimeLine(pygal.DateTimeLine):
    def __init__(self, **kwargs):
        super(DateTimeLine, self).__init__(**kwargs)
        self.data = None
        self.y_data = dict()
        self.x_label_rotation = 30

    def render_widget(self, width=None, height=None):
        """ Render a pygal chart into a Jupyter Notebook """
        return render_widget(self, width, height)


class Image(object):
    """ Charts for Images """
    def __init__(self, source):
        self.source = source

    @staticmethod
    def check_imageCollection(imageCollection):
        if not isinstance(imageCollection, ee.ImageCollection):
            msg = 'first parameter of Image.doySeries must be an ' \
                  'ImageCollection, found {}'
            raise ValueError(msg.format(type(imageCollection)))

    @staticmethod
    def series(imageCollection, region, reducer=ee.Reducer.mean(),
               scale=None, xProperty='system:time_start', bands=None,
               labels=None):
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

        # Select bands
        imageCollection = imageCollection.select(ydata)

        # Get Images properties
        properties = first.propertyNames().getInfo()

        # If xProperty == 'system:time_start' will compute datetime
        datetime = True if xProperty == 'system:time_start' else False

        # generate data
        if isinstance(region, ee.Geometry):
            geom = region
        elif isinstance(region, (ee.Feature, ee.FeatureCollection)):
            geom = region.geometry()
        else:
            msg = 'Parameter `region` must be `ee.Geometry`, `ee.Feautre` or' \
                  ' or `ee.FeatureCollection, found {}'
            raise ValueError(msg.format(type(region)))

        if xProperty in properties:
            # include xProperty in data
            x_property = [xProperty]
        elif xProperty in allbands:
            # xProperty will be included in data because is a band
            x_property = []
        else:
            msg = 'xProperty "{}" not found in properties or bands'
            raise ValueError(msg.format(xProperty))

        data = tools.imagecollection.get_values(
            collection=imageCollection,
            geometry=geom,
            reducer=reducer,
            scale=scale,
            properties=x_property,
            side='client')

        # Replace band names with labels provided
        if labels and len(ydata) == len(labels):
            for iid, values_dict in data.items():
                for old_name, new_name in zip(ydata, labels):
                    data[iid][new_name] = data[iid][old_name]
                    data[iid].pop(old_name)
            ydata = labels

        df = tools.imagecollection.data2pandas(data)
        newdf = df.sort_values(xProperty)

        if datetime:
            chart = DateTimeLine()
        else:
            chart = Line()

        line_chart = from_pandas(chart, newdf, y=ydata,
                                 x=xProperty, datetime=datetime)

        reducer_name = reducer.getInfo()['type'].split('.')[1]
        chart_title = 'Band {} in relation with {}'
        chart_title = chart_title.format(reducer_name, xProperty)
        line_chart.title = chart_title

        return line_chart

    @staticmethod
    def seriesByRegion(imageCollection, regions, reducer, band=None,
                       scale=None, xProperty='system:time_start',
                       seriesProperty='system:index'):

        # If xProperty == 'system:time_start' will compute datetime
        datetime = True if xProperty == 'system:time_start' else False

        Image.check_imageCollection(imageCollection)
        first = ee.Image(imageCollection.first())

        # Make defaults
        if not band:
            band = ee.String(first.bandNames().get(0))
        if not scale:
            # scale = first.select([0]).projection().nominalScale()
            scale = 1

        # select band
        imageCollection = imageCollection.select(band)

        # Generate data
        # Geometry
        if isinstance(regions, ee.Geometry):
            print('Using `seriesByRegion` with `ee.Geometry` will give you'
                  ' the same output as `series`, use that method instead')

            chart_title = '{} values in merged geometry in relation with {}'
            chart_title = chart_title.format(band, xProperty)

            chart_line = Image.series(imageCollection, regions, reducer,
                                      scale=scale, xProperty=xProperty,
                                      bands=[band], labels=['geometry'])
            chart_line.title = chart_title
            return chart_line

        elif isinstance(regions, ee.Feature):
            reducer_name = reducer.getInfo()['type'].split('.')[1]

            chart_title = '{} {} values in one regions in relation ' \
                          'with {}\nlabeled by {}'
            chart_title = chart_title.format(band, reducer_name,
                                             xProperty, seriesProperty)

            label = regions.get(seriesProperty).getInfo()
            label = label if label else 'unknown feature'
            chart_line = Image.series(imageCollection, regions, reducer,
                                      scale=scale, xProperty=xProperty,
                                      bands=[band], labels=[label])
            chart_line.title = chart_title
            return chart_line

        elif isinstance(regions, ee.FeatureCollection):

            def over_col(img, inicol):
                inicol = ee.Dictionary(inicol)
                x_prop = img.get(xProperty)
                iid = img.get('system:index')

                def over_fc(feat, inifeat):
                    inifeat = ee.Dictionary(inifeat)
                    name = feat.get(seriesProperty)
                    data = img.reduceRegion(reducer,
                                            feat.geometry(),
                                            scale).get(band)
                    return inifeat.set(name, data)

                fc_data = ee.Dictionary(
                    regions.iterate(over_fc, ee.Dictionary({}))
                ).set(xProperty, x_prop)

                return inicol.set(iid, fc_data)

            data = ee.Dictionary(
                imageCollection.iterate(over_col, ee.Dictionary({})))

            data = data.getInfo()

            df = tools.imagecollection.data2pandas(data)
            newdf = df.sort_values(xProperty)

            y_labels = newdf.columns.values.tolist()

            if datetime:
                chart = DateTimeLine()
            else:
                chart = Line()

            line_chart = from_pandas(chart, newdf, y=y_labels,
                                     x=xProperty, datetime=datetime)

            reducer_name = reducer.getInfo()['type'].split('.')[1]
            chart_title = '{} {} values in different regions in relation ' \
                          'with {}\nlabeled by {}'
            chart_title = chart_title.format(band, reducer_name,
                                             xProperty, seriesProperty)
            line_chart.title = chart_title

            return line_chart

