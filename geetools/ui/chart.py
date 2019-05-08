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
from .. import tools, utils
import pandas as pd
import datetime

# TODO: make not plotted bands values appear on tooltip
# TODO: give capability to plot a secondary axis with other data


def ydata2pandas(ydata):
    """ Convert data from charts y_data property to pandas """
    dataframes = []
    for serie, data in ydata.items():
        index = []
        values = []
        for d in data:
            x = d[0]
            y = d[1]
            index.append(x)
            values.append(y)
        df = pd.DataFrame({serie:values}, index=index)
        dataframes.append(df)

    return pd.concat(dataframes, axis=1, sort=False)


def concat(*plots):
    """ Concatenate plots. The type of the resulting plot will be the type
        of the first parsed plot
    """
    first = plots[0]
    if isinstance(first, DateTimeLine):
        chart = DateTimeLine()
    else:
        chart = Line()

    y_data = {}
    for plot in plots:
        p_data = plot.y_data
        for serie, data in p_data.items():
            y_data[serie] = data
            chart.add(serie, data)

    chart.y_data = y_data
    return chart


def renderWidget(chart, width=None, height=None):
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


def fromPandas(line_chart, dataframe, x=None, y=None, datetime=False,
               drop_null=True):
    """ Creates a Line chart from a pandas dataFrame """

    ### CHECK FOR PANDAS DATAFRAME
    if not isinstance(dataframe, pd.DataFrame):
        raise ValueError('first argument must be a pandas DataFrame')

    if drop_null:
        dataframe = dataframe.dropna()
    else:
        dataframe = dataframe.fillna(0)

    def column2list(df, col, null=0):
        """
        Helper function to transform a column from a dataframe to a list.
        NaN values will be replaced with `null` parameter.
        String values will be replaced with float
        """
        values = []
        for val in df[col].values.tolist():
            if pd.isnull(val):
                val = null
            if isinstance(val, str):
                val = float(val)
            values.append(val)
        return values

    if not x:
        # Sort dataframe by x values
        dataframe = dataframe.sort_index()
        labels = [int(n) for n in dataframe.index.tolist()]
    else:
        # Sort dataframe by x values
        dataframe = dataframe.sort_values(x)
        labels = column2list(dataframe, x)

    if not datetime:
        x_values = labels
    else:
        x_values = [tools.date.millisToDatetime(d) for d in labels]

    # add property to parsed line_chart object
    line_chart.x_labels = x_values

    if isinstance(y, list):
        for column in y:
            if column == x:
                continue

            ydata = column2list(dataframe, column)
            nydata = []
            for dt, value in zip(x_values, ydata):
                nydata.append((dt, value))
            ydata = nydata

            # TODO: add values config
            # pygal.org/en/latest/documentation/configuration/value.html
            line_chart.add(column, ydata)
            line_chart.y_data[column] = ydata
    else:
        ydata = column2list(dataframe, y)

        nydata = []
        for dt, value in zip(x_values, ydata):
            nydata.append((dt, value))

        ydata = nydata

        line_chart.add(y, ydata)
        line_chart.y_data[y] = ydata

    return line_chart


class Line(pygal.XY):
    def __init__(self, **kwargs):
        super(Line, self).__init__(**kwargs)
        self.y_data = dict()
        self.x_label_rotation = 30

    @property
    def dataframe(self):
        return ydata2pandas(self.y_data)

    def renderWidget(self, width=None, height=None):
        """ Render a pygal chart into a Jupyter Notebook """
        return renderWidget(self, width, height)

    def cat(self, *plots):
        """ Concatenate with other Line Graphics """
        return concat(self, *plots)


class DateTimeLine(pygal.DateTimeLine):
    def __init__(self, **kwargs):
        super(DateTimeLine, self).__init__(**kwargs)
        self.y_data = dict()
        self.x_label_rotation = 30

    @property
    def dataframe(self):
        return ydata2pandas(self.y_data)

    def renderWidget(self, width=None, height=None):
        """ Render a pygal chart into a Jupyter Notebook """
        return renderWidget(self, width, height)

    def cat(self, *plots):
        """ Concatenate with other DateTimeLine Graphics """
        return concat(self, *plots)


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
    def series(imageCollection, region, reducer='mean', scale=None,
               xProperty='system:time_start', bands=None, label_bands=None,
               properties=None, label_properties=None):
        """ Basic plot over an ImageCollection

        :param region: the region to reduce over an get a (unique) value
        :type region: ee.Geometry or ee.Feature or ee.FeatureCollection
        :param reducer: the reducer to apply over the region.
        :param scale: the scale to apply the reducer. If None, will use the
            nominal scale of the first band of the first image of the
            collection
        :param xProperty: the property that will be use for the x axis
        :param bands: the bands that will be used for the y axis
        :param label_bands: the names for the series of bands. Have to match
            the length of bands
        :param properties: the properties that will be used for the y axis
        :param label_properties: the names for the series of properties. Have
            to match the length of properties
        :return: a linear chart
        :rtype: pygal.XY
        """
        Image.check_imageCollection(imageCollection)

        # first image (for getting bands and properties)
        first = ee.Image(imageCollection.first())
        allbands = first.bandNames().getInfo()

        # scale
        if not scale:
            scale = first.select(0).projection().nominalScale()

        # Get Y (bands)
        if not bands and not properties:
            bands = allbands
            properties = []
            label_properties = []
            if not label_bands:
                label_bands = allbands
        elif bands and not properties:
            properties = []
            label_properties = []
            if not label_bands:
                label_bands = bands
        elif properties and not bands:
            bands = []
            label_bands = []
            if not label_properties:
                label_properties = properties
        else:
            if not label_bands:
                label_bands = bands
            if not label_properties:
                label_properties = properties

                # Check for consistance
        if len(bands) != len(label_bands):
            msg = 'The number of the labels for bands must be equal to the ' \
                  'number of parsed bands. Found {} and {}'.format(
                len(label_bands), len(bands))
            raise ValueError(msg)

        if len(properties) != len(label_properties):
            msg = 'The number of the labels for properties must be equal to ' \
                  'the number of parsed properties. Found {} and {}'.format(
                len(label_properties), len(properties))
            raise ValueError(msg)

        # Select bands
        imageCollection = imageCollection.select(bands)

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

        x_properties = [xProperty]

        if properties is not None:
            x_properties = x_properties + properties

        data = tools.imagecollection.getValues(
            collection=imageCollection,
            geometry=geom,
            reducer=reducer,
            scale=scale,
            properties=x_properties,
            side='client')

        if label_bands and label_properties:
            ydata = label_bands + label_properties
        elif label_bands and not label_properties:
            ydata = label_bands
        else:
            ydata = label_properties

        # Replace band names with labels provided
        if label_bands:
            for iid, values_dict in data.items():
                for old_name, new_name in zip(bands, label_bands):
                    if new_name != old_name:
                        data[iid][new_name] = data[iid][old_name]
                        data[iid].pop(old_name)

        # Replace property names with labels provided
        if label_properties:
            for iid, values_dict in data.items():
                for old_name, new_name in zip(properties, label_properties):
                    if new_name != old_name:
                        data[iid][new_name] = data[iid][old_name]
                        data[iid].pop(old_name)

        df = tools.imagecollection.data2pandas(data)
        newdf = df.sort_values(xProperty)

        if datetime:
            chart = DateTimeLine()
        else:
            chart = Line()

        line_chart = fromPandas(chart, newdf, y=ydata,
                                x=xProperty, datetime=datetime)

        if isinstance(reducer, str):
            reducer_name = reducer
        else:
            reducer_name = reducer.getInfo()['type'].split('.')[1]

        chart_title = 'Band {} in relation with {} across images'
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

            line_chart = fromPandas(chart, newdf, y=y_labels,
                                    x=xProperty, datetime=datetime)

            reducer_name = reducer.getInfo()['type'].split('.')[1]
            chart_title = '{} {} values in different regions in relation ' \
                          'with {}\nlabeled by {}'
            chart_title = chart_title.format(band, reducer_name,
                                             xProperty, seriesProperty)
            line_chart.title = chart_title

            return line_chart


    @staticmethod
    def bandsByRegion(image, collection, xProperty='system:index', bands=None,
                      reducer='mean', scale=None, labels=None, **kwargs):
        """ Plot values for each region given an xBand

        :param image: The image to get the values from
        :param collection: The collection must be contained in the image
        :type collection: ee.FeatureCollection
        :param xProperty: The property of the Features that will be used as
            x value. If a band is parsed, the value will be obtained using
            the parsed reducer
        :param bands: the band to be in the y axis
        :param reducer: the reducer to apply in each Feature
        :param scale: the scale to apply the reducer
        :return: a chart
        :rtype: pygal.XY
        """
        allbands = image.bandNames().getInfo()

        xProperty_is_band = xProperty in allbands

        if not bands:
            bands = [band for band in allbands]

        if not labels:
            labels = [band for band in bands]

        if xProperty_is_band and xProperty not in bands:
            bands.append(xProperty)
            labels.append(xProperty)

        # Check for consistance
        if len(labels) != len(bands):
            msg = 'The number of labels provided must be the same as the ' \
                  'number of bands. Found {} and {}'.format(
                len(labels), len(bands))
            raise ValueError(msg)

        if xProperty == 'system:index':
            xProperty = None

        if isinstance(collection, ee.Geometry):
            msg = 'the parsed collection must be a FeatureCollection or a ' \
                  'Feature'
            raise ValueError(msg)

        if isinstance(collection, ee.Feature):
            collection = ee.FeatureCollection([collection])

        image = image.select(bands, labels)

        fc = image.reduceRegions(collection=collection, reducer=reducer,
                                 scale=scale, **kwargs)

        if isinstance(reducer, ee.Reducer):
            rname = utils.getReducerName(reducer)
        else:
            rname = reducer

        if len(bands) == 1:
            band = bands[0]
            def rename(feat):
                condition = feat.propertyNames().contains(rname)
                return ee.Algorithms.If(
                    condition, ee.Feature(feat).select([rname], [band]), feat)

            fc = fc.map(rename)

        pd = utils.reduceRegionsPandas(fc)

        l = Line()

        line_chart = fromPandas(l, pd, x=xProperty, y=labels)

        chart_title = 'Band {} in relation with {} across features'
        chart_title = chart_title.format(rname, xProperty)
        line_chart.title = chart_title

        return line_chart
