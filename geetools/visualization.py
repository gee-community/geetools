# coding=utf-8
""" Helper functions for visualizing """
import ee


def stretch_std(image, region, bands=None, std=1, scale=None):
    """ Get mins and maxs values for stretching a visualization using standard
    deviation """
    if not bands:
        names = image.bandNames()
        bands = ee.List(ee.Algorithms.If(
            names.size().gte(3), names.slice(0,3), names.slice(0)))
        bands = bands.getInfo()

    image = image.select(bands)
    geom = region or image.geometry()
    params = dict(geometry=geom, bestEffort=True)
    if scale:
        params['scale'] = scale

    params['reducer'] = ee.Reducer.mean()
    mean = image.reduceRegion(**params)

    params['reducer'] = ee.Reducer.stdDev()
    stdDev = image.reduceRegion(**params)

    def minmax(band, val):
        minv = ee.Number(val).subtract(ee.Number(stdDev.get(band)).multiply(std))
        maxv = ee.Number(val).add(ee.Number(stdDev.get(band)).multiply(std))
        return ee.List([minv, maxv])

    if len(bands) == 1:
        band = bands[0]
        values = minmax(band, mean.get(band)).getInfo()
        minv = values[0]
        maxv = values[1]
    else:
        values = mean.map(minmax).select(bands).getInfo()
        minv = [values[bands[0]][0], values[bands[1]][0], values[bands[2]][0]]
        maxv = [values[bands[0]][1], values[bands[1]][1], values[bands[2]][1]]

    return dict(bands=bands, min=minv, max=maxv)



def stretch_percentile(image, region, bands=None, percentile=90, scale=None):
    """ Get mins and maxs values for stretching a visualization using
    percentiles """
    # Calculate start and end percentiles
    startp = 50-(percentile/2)
    endp = 50+(percentile/2)

    if not bands:
        names = image.bandNames()
        bands = ee.List(ee.Algorithms.If(
            names.size().gte(3), names.slice(0,3), names.slice(0)))
        bands = bands.getInfo()

    image = image.select(bands)
    geom = region or image.geometry()
    params = dict(geometry=geom, bestEffort=True)
    if scale:
        params['scale'] = scale

    params['reducer'] = ee.Reducer.percentile([startp, endp])
    percentiles = image.reduceRegion(**params)

    def minmax(band):
        minkey = ee.String(band).cat('_p').cat(ee.Number(startp).format())
        maxkey = ee.String(band).cat('_p').cat(ee.Number(endp).format())

        minv = ee.Number(percentiles.get(minkey))
        maxv = ee.Number(percentiles.get(maxkey))
        return ee.List([minv, maxv])

    if len(bands) == 1:
        band = bands[0]
        values = minmax(band).getInfo()
        minv = values[0]
        maxv = values[1]
    else:
        values = ee.List(bands).map(minmax).getInfo()
        minv = [values[0][0], values[1][0], values[2][0]]
        maxv = [values[0][1], values[1][1], values[2][1]]

    return dict(bands=bands, min=minv, max=maxv)
