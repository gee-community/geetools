# coding=utf-8
""" Dispatch methods for different EE Object types """
import ee
from ipywidgets import *
from . import ipytools

def belongToEE(eeobject):
    """ Determine if the parsed object belongs to the Earth Engine API """
    module = getattr(eeobject, '__module__', None)
    parent = module.split('.')[0] if module else None
    if parent == ee.__name__:
        return True
    else:
        return False


# GENERAL DISPATCHER
def dispatch(eeobject, notebook=False):
    """ General dispatcher """
    if belongToEE(eeobject):
        # DISPATCH!!
        if isinstance(eeobject, (ee.Image,)):
            return dispatchImage(eeobject, notebook)
        elif isinstance(eeobject, (ee.Date,)):
            return dispatchDate(eeobject, notebook)
        elif isinstance(eeobject, (ee.DateRange,)):
            return dispatchDaterange(eeobject, notebook)
        # ADD MORE ABOVE ME!
        else:
            info = eeobject.getInfo()

            if notebook:
                if isinstance(info, (dict,)):
                    info = eeobjectDispatcher(eeobject)
                    return ipytools.create_accordion(info)
                else:
                    info = eeobjectDispatcher(eeobject)
                    return HTML(str(info)+'<br/>')

            return info
    else:
        info = str(eeobject)
        if notebook:
            return Label(info)
        else:
            return info


def dispatchImage(image, notebook=False):
    """ Dispatch a Widget for an Image Object """
    info = image.getInfo()

    # IMAGE
    image_id = info['id'] if 'id' in info else 'No Image ID'
    prop = info.get('properties')
    bands = info.get('bands')
    bands_names = [band.get('id') for band in bands]

    # BAND PRECISION
    bands_precision = []
    for band in bands:
        data = band.get('data_type')
        if data:
            precision = data.get('precision')
            bands_precision.append(precision)

    # BAND CRS
    bands_crs = []
    for band in bands:
        crs = band.get('crs')
        bands_crs.append(crs)

    # BAND MIN AND MAX
    bands_min = []
    for band in bands:
        data = band.get('data_type')
        if data:
            bmin = data.get('min')
            bands_min.append(bmin)

    bands_max = []
    for band in bands:
        data = band.get('data_type')
        if data:
            bmax = data.get('max')
            bands_max.append(bmax)

    if not notebook:
        return info
    else:
        # BANDS
        new_band_names = []
        zipped_data = zip(bands_names, bands_precision, bands_min, bands_max,
                          bands_crs)
        for name, ty, mn, mx, epsg in zipped_data:
            value = '<li><b>{}</b> ({}) {} to {} - {}</li>'.format(name,ty,
                                                                   mn,mx,epsg)
            new_band_names.append(value)
        bands_wid = HTML('<ul>'+''.join(new_band_names)+'</ul>')

        # PROPERTIES
        if prop:
            new_properties = []
            for key, val in prop.items():
                value = '<li><b>{}</b>: {}</li>'.format(key, val)
                new_properties.append(value)
            prop_wid = HTML('<ul>'+''.join(new_properties)+'</ul>')
        else:
            prop_wid = HTML('Image has no properties')

        # ID
        header = HTML('<b>Image id:</b> {id} </br>'.format(id=image_id))

        acc = Accordion([bands_wid, prop_wid])
        acc.set_title(0, 'Bands')
        acc.set_title(1, 'Properties')
        acc.selected_index = None # thisp will unselect all

        return VBox([header, acc])


def dispatchDate(date, notebook=False):
    """ Dispatch a ee.Date """
    info = date.format().getInfo()

    if not notebook:
        return info
    else:
        return Label(info)


def dispatchDaterange(daterange, notebook=False):
    """ Dispatch a DateRange """
    start = daterange.start().format().getInfo()
    end = daterange.end().format().getInfo()
    value = '{} to {}'.format(start, end)

    if not notebook:
        return value
    else:
        return Label(value)


# OBJECT DISPATCHER
def eeobjectDispatcher(eeobject):
    return dispatch(eeobject, False)


# WIDGET DISPATCHER
def widgetDispatcher(eeobject):
    """ Dispatch a Widget regarding its type """
    return dispatch(eeobject, True)
