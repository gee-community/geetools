# coding=utf-8
""" Dispatch methods for different EE Object types """
import ee
from ipywidgets import *
from . import ipytools

def belong_to_ee(eeobject):
    """ Determine if the parsed object belongs to the Earth Engine API """
    module = getattr(eeobject, '__module__', None)
    parent = module.split('.')[0] if module else None
    if parent == ee.__name__:
        return True
    else:
        return False


def dispatch_image(image, widget=False):
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

    if not widget:
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


def dispatch_date(date, widget=False):
    """ Dispatch a ee.Date """
    info = date.format().getInfo()

    if not widget:
        return info
    else:
        return Label(info)


# OBJECT DISPATCHER
def eeobject_dispatcher(eeobject):
    if belong_to_ee(eeobject):
        # DISPATCH!!
        if isinstance(eeobject, (ee.Date,)):
            return dispatch_date(eeobject)

        elif isinstance(eeobject, (ee.Image,)):
            return dispatch_image(eeobject)

        else:
            return eeobject.getInfo()
    else:
        return str(eeobject)


# WIDGET DISPATCHER
def widget_dispatcher(eeobject):
    """ Dispatch a Widget regarding its type """
    if belong_to_ee(eeobject):
        # DISPATCH!!
        if isinstance(eeobject, (ee.Image,)):
            return dispatch_image(eeobject, True)

        elif isinstance(eeobject, (ee.Date,)):
            return dispatch_date(eeobject, True)

        else:
            info = eeobject.getInfo()

            if isinstance(info, (dict,)):
                info = eeobject_dispatcher(eeobject)
                return ipytools.create_accordion(info)
            else:
                info = eeobject_dispatcher(eeobject)
                return HTML(str(info)+'<br/>')