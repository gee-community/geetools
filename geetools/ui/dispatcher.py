# coding=utf-8
""" Dispatch methods for different EE Object types """
import ee


def belongToEE(eeobject):
    """ Determine if the parsed object belongs to the Earth Engine API """
    module = getattr(eeobject, '__module__', None)
    parent = module.split('.')[0] if module else None
    if parent == ee.__name__:
        return True
    else:
        return False


# GENERAL DISPATCHER
def dispatch(eeobject):
    """ General dispatcher """
    if belongToEE(eeobject):
        # DISPATCH!!
        if isinstance(eeobject, (ee.Image,)):
            return dispatchImage(eeobject)
        elif isinstance(eeobject, (ee.Date,)):
            return dispatchDate(eeobject)
        elif isinstance(eeobject, (ee.DateRange,)):
            return dispatchDaterange(eeobject)
        # ADD MORE ABOVE ME!
        else:
            info = eeobject.getInfo()
            return info
    else:
        info = str(eeobject)
        return info


def dispatchImage(image):
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

    bands = {}
    for name, pres, crs, minval, maxval in zip(
            bands_names, bands_precision, bands_crs, bands_min, bands_max):
        bands[name] = dict(precision=pres, crs=crs, min=minval, max=maxval)

    return dict(id=image_id, bands=bands, properties=prop)


def dispatchDate(date):
    """ Dispatch a ee.Date """
    info = date.format().getInfo()

    return info


def dispatchDaterange(daterange):
    """ Dispatch a DateRange """
    start = daterange.start().format().getInfo()
    end = daterange.end().format().getInfo()
    value = '{} to {}'.format(start, end)

    return value
