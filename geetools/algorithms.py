# coding=utf-8
"""Module holding misc algorithms."""
import math

import ee
import ee.data

from . import tools


def distanceToMask(
    image,
    kernel=None,
    radius=1000,
    unit="meters",
    scale=None,
    geometry=None,
    band_name="distance_to_mask",
    normalize=False,
):
    """Compute the distance to the mask in meters.

    :param image: Image holding the mask
    :type image: ee.Image
    :param kernel: Kernel to use for computing the distance. By default uses
        euclidean
    :type kernel: ee.Kernel
    :param radius: radius for the kernel. Defaults to 1000
    :type radius: int
    :param unit: units for the kernel radius. Defaults to 'meters'
    :type unit: str
    :param scale: scale for reprojection. If None, will reproject on the fly
        (according to EE lazy computing)
    :type scale: int
    :param geometry: compute the distance only inside this geometry. If you
        want to compute the distance inside a clipped image, using this
        parameter will make the edges not be considered as a mask.
    :type geometry: ee.Geometry or ee.Feature
    :param band_name: name of the resulting band. Defaults to
        'distance_to_mask'
    :type band_name: str
    :param normalize: Normalize result (between 0 and 1)
    :type normalize: bool
    :return: A one band image with the distance to the mask
    :rtype: ee.Image
    """
    if not kernel:
        kernel = ee.Kernel.euclidean(radius, unit)

    # select first band
    image = image.select(0)

    # get mask
    mask = image.mask()
    inverse = mask.Not()

    if geometry:
        # manage geometry types
        if isinstance(geometry, (ee.Feature, ee.FeatureCollection)):
            geometry = geometry.geometry()

        inverse = inverse.clip(geometry)

    # Compute distance to the mask (inverse)
    distance = inverse.distance(kernel)

    if scale:
        proj = image.projection()
        distance = distance.reproject(proj.atScale(scale))

    # make mask to be the max distance
    dist_mask = distance.mask().Not().remap([0, 1], [0, radius])

    if geometry:
        dist_mask = dist_mask.clip(geometry)

    final = distance.unmask().add(dist_mask)

    if normalize:
        final = tools.image.parametrize(final, (0, radius), (0, 1))

    return final.rename(band_name)


def maskCover(
    image,
    geometry=None,
    scale=None,
    property_name="MASK_COVER",
    crs=None,
    crsTransform=None,
    bestEffort=False,
    maxPixels=1e13,
    tileScale=1,
):
    """Percentage of masked pixels (masked/total * 100) as an Image property.

    :param image: ee.Image holding the mask. If the image has more than
        one band, the first one will be used
    :type image: ee.Image
    :param geometry: the value will be computed inside this geometry. If None,
        will use image boundaries. If unbounded the result will be 0
    :type geometry: ee.Geometry or ee.Feature
    :param scale: the scale of the mask
    :type scale: int
    :param property_name: the name of the resulting property
    :type property_name: str
    :return: The same parsed image with a new property holding the mask cover
        percentage
    :rtype: ee.Image
    """
    # keep only first band
    imageband = image.select(0)

    # get projection
    projection = imageband.projection()

    if not scale:
        scale = projection.nominalScale()

    # get band name
    band = ee.String(imageband.bandNames().get(0))

    # Make an image with all ones
    ones_i = ee.Image.constant(1).reproject(projection).rename(band)

    if not geometry:
        geometry = image.geometry()

    # manage geometry types
    if isinstance(geometry, (ee.Feature, ee.FeatureCollection)):
        geometry = geometry.geometry()

    unbounded = geometry.isUnbounded()

    # Get total number of pixels
    ones = ones_i.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geometry,
        scale=scale,
        maxPixels=maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale,
    ).get(band)
    ones = ee.Number(ones)

    # select first band, unmask and get the inverse
    mask = imageband.mask()
    mask_not = mask.Not()
    image_to_compute = mask.updateMask(mask_not)

    # Get number of zeros in the given image
    zeros_in_mask = image_to_compute.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geometry,
        scale=scale,
        maxPixels=maxPixels,
        crs=crs,
        crsTransform=crsTransform,
        bestEffort=bestEffort,
        tileScale=tileScale,
    ).get(band)
    zeros_in_mask = ee.Number(zeros_in_mask)

    percentage = tools.trimDecimals(zeros_in_mask.divide(ones), 4)

    # Multiply by 100
    cover = percentage.multiply(100)

    # Return None if geometry is unbounded
    final = ee.Number(ee.Algorithms.If(unbounded, 0, cover))

    return image.set(property_name, final)


def euclideanDistance(image1, image2, bands=None, discard_zeros=False, name="distance"):
    """Compute the Euclidean distance between two images. The image's bands.

    is the dimension of the arrays.

    :param image1:
    :type image1: ee.Image
    :param image2:
    :type image2: ee.Image
    :param bands: the bands that want to be computed
    :type bands: list
    :param discard_zeros: pixel values equal to zero will not count in the
        distance computation
    :type discard_zeros: bool
    :param name: the name of the resulting band
    :type name: str
    :return: a distance image
    :rtype: ee.Image
    """
    if not bands:
        bands = image1.bandNames()

    image1 = image1.select(bands)
    image2 = image2.select(bands)

    proxy = tools.image.empty(0, bands)
    image1 = proxy.where(image1.gt(0), image1)
    image2 = proxy.where(image2.gt(0), image2)

    if discard_zeros:
        # zeros
        zeros1 = image1.eq(0)
        zeros2 = image2.eq(0)

        # fill zeros with values from the other image
        image1 = image1.where(zeros1, image2)
        image2 = image2.where(zeros2, image1)

    a = image1.subtract(image2)
    b = a.pow(2)
    c = b.reduce("sum")
    d = c.sqrt()

    return d.rename(name)


def sumDistance(image, collection, bands=None, discard_zeros=False, name="sumdist"):
    """Compute de sum of all distances between the given image and the.

    collection passed.

    :param image:
    :param collection:
    :return:
    """
    condition = isinstance(collection, ee.ImageCollection)

    if condition:
        collection = collection.toList(collection.size())

    accum = ee.Image(0).rename(name)

    def over_rest(im, ini):
        ini = ee.Image(ini)
        im = ee.Image(im)
        dist = ee.Image(euclideanDistance(image, im, bands, discard_zeros)).rename(name)
        return ini.add(dist)

    return ee.Image(collection.iterate(over_rest, accum))


def pansharpenKernel(image, pan, rgb=None, kernel=None):
    """Compute the per-pixel means of the unsharpened bands.

    source: https://gis.stackexchange.com/questions/296615/pansharpen-landsat-mosaic-in-google-earth-engine.

    :param pan: the name of the panchromatic band
    :type pan: str
    :param rgb: the red green blue bands
    :type rgb: tuple or list
    :param kernel: the kernel to reduce neighbors
    :type kernel: ee.Kernel
    :rtype: ee.Image
    """
    if not kernel:
        kernel = ee.Kernel.square(90, "meters")
    if not rgb:
        rgb = ["red", "green", "blue"]

    if not pan:
        pan = "pan"

    bgr = image.select(rgb)
    pani = image.select(pan)
    bgr_mean = bgr.reduce("mean").rename("mean")
    # Compute the aggregate mean of the unsharpened bands and the pan band
    mean_values = pani.addBands(bgr_mean).reduceNeighborhood(ee.Reducer.mean(), kernel)
    gain = mean_values.select("mean_mean").divide(mean_values.select("{}_mean".format(pan)))
    sharpen = bgr.divide(bgr_mean).multiply(pani).multiply(gain)
    return ee.Image(sharpen.copyProperties(source=image, properties=image.propertyNames()))


def pansharpenIhsFusion(image, pan=None, rgb=None):
    """HSV-based Pan-Sharpening.

    source: https://gis.stackexchange.com/questions/296615/pansharpen-landsat-mosaic-in-google-earth-engine.

    :param image:
    :type image: ee.Image
    the name of the panchromatic band
    :type pan: str
    :param rgb: the red green blue bands
    :type rgb: tuple or list
    :rtype: ee.Image
    """
    if not rgb:
        rgb = ["red", "green", "blue"]

    if not pan:
        pan = "pan"

    rgb = image.select(rgb)
    pan = image.select(pan)
    # Convert to HSV, swap in the pan band, and convert back to RGB.
    huesat = rgb.rgbToHsv().select("hue", "saturation")
    upres = ee.Image.cat(huesat, pan).hsvToRgb()
    return image.addBands(upres)


class Landsat(object):
    """TODO add docstring."""

    @staticmethod
    def unmask_slc_off(image, optical_bands="B.+"):
        """Unmask pixels that were affected by scl-off  error in Landsat 7.

        Expects a Landsat 7 image and it is meant to be used before any other
        masking, otherwise this could affect the previous mask.

        The parameter `optical_bands` must be used if band were renamed. By
        default it is `B.+` which means that optical bands are those starting
        with B: B1 (blue), B2 (green), B3 (red), B4 (nir), B5 (swir),
        B6 (thermal), B7 (swir2).
        """
        idate = image.date()
        slcoff = ee.Date("2003-05-31")
        condition = idate.difference(slcoff, "days").gte(0)

        def compute(i):
            mask = i.mask()
            reduced = mask.select(optical_bands).reduce("sum")
            slc_off = reduced.eq(0)
            unmasked = i.unmask()
            newmask = mask.where(slc_off, 1)
            return unmasked.updateMask(newmask)

        return ee.Image(ee.Algorithms.If(condition, compute(image), image))

    @staticmethod
    def _rescale(image, bands=None, thermal_bands=None, original="TOA", to="SR", number="all"):
        """Rescaling logic."""
        if not bands:
            bands = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
        bands = ee.List(bands)

        if not thermal_bands:
            thermal_bands = ["B10", "B11"]
        thermal_bands = ee.List(thermal_bands)

        allbands = bands.cat(thermal_bands)

        if number == "8":
            max_raw = 65535
        else:
            max_raw = 255

        if original == "TOA" and to == "SR":
            scaled = image.select(bands).multiply(10000).toInt16()
            scaled_thermal = image.select(thermal_bands).multiply(10).toInt16()
        elif original == "SR" and to == "TOA":
            scaled = image.select(bands).toFloat().divide(10000)
            scaled_thermal = image.select(thermal_bands).toFloat().divide(10)
        elif original == "TOA" and to == "RAW":
            scaled = tools.image.parametrize(image.select(bands), (0, 1), (0, max_raw))
            scaled_thermal = tools.image.parametrize(
                image.select(bands), (0, 1), (0, max_raw)
            ).multiply(1000)

        original_bands = image.bandNames()

        rest_bands = tools.ee_list.difference(original_bands, allbands)

        rest_image = image.select(rest_bands)

        return rest_image.addBands(scaled).addBands(scaled_thermal)

    @staticmethod
    def rescaleToaSr(image, bands=None, thermal_bands=None):
        """Re-scale a TOA Landsat image to match the data type of SR Landsat.

        image.

        :param image: a Landsat TOA image
        :type image: ee.Image
        :param bands: bands to rescale by 10000. If None will use the bands for
            Landsat 8 (['B1','B2','B3','B4','B5','B6','B7']).
        :type bands: list
        :param thermal_bands: bands to rescale by 100. Defaults to
            ['B10', 'B11']
        :type thermal_bands: list
        :rtype: ee.Image
        """
        return Landsat._rescale(image, bands, thermal_bands, "TOA", "SR")

    @staticmethod
    def rescaleSrToa(image, bands=None, thermal_bands=None):
        """Re-scale a TOA Landsat image to match the data type of SR Landsat.

        image.

        :param image: a Landsat TOA image
        :type image: ee.Image
        :param bands: bands to rescale by 10000. If None will use the bands for
            Landsat 8 (B[1-7]).
        :type bands: list
        :param thermal_bands: bands to rescale by 100. Defaults to
            ['B10', 'B11']
        :type thermal_bands: list
        :rtype: ee.Image
        """
        return Landsat._rescale(image, bands, thermal_bands, "SR", "TOA")

    @staticmethod
    def harmonization(
        image,
        blue="B2",
        green="B3",
        red="B4",
        nir="B5",
        swir="B6",
        swir2="B7",
        max_value=None,
    ):
        """Harmonization of Landsat 8 images to be consistent with.

        Landsat 7 images.

        Roy, D.P., Kovalskyy, V., Zhang, H.K., Vermote, E.F., Yan, L.,
        Kumar, S.S, Egorov, A., 2016, Characterization of Landsat-7 to
        Landsat-8 reflective wavelength and normalized difference vegetation
        index continuity, Remote Sensing of Environment, 185, 57-70.
        (http://dx.doi.org/10.1016/j.rse.2015.12.024) Table 2 -
        reduced major axis (RMA) regression coefficients

        :param image: A Landsat 8 Image
        :param max_value: the maximum value for the optical bands. For float
            bands it is 1 (TOA), for int16 it is 10000 (SR) and for int8 it is
            255 (RAW). It default to 1 (TOA)
        :return:
        """
        bands = ee.List([blue, green, red, nir, swir, swir2])
        band_types = image.bandTypes().select(bands)

        if max_value is None:
            max_value = 1

        slopes = ee.Image.constant([0.9785, 0.9542, 0.9825, 1.0073, 1.0171, 0.9949])
        itcp = ee.Image.constant([-0.0095, -0.0016, -0.0022, -0.0021, -0.0030, 0.0029])

        only_bands = image.select(bands)
        resampled = only_bands.resample("bicubic")

        harmonized = resampled.subtract(itcp.multiply(max_value)).divide(slopes)

        harmonized = harmonized.cast(band_types)

        # append rest of the bands
        return image.addBands(harmonized, overwrite=True)

    @staticmethod
    def brdfCorrect(
        image,
        red="red",
        green="green",
        blue="blue",
        nir="nir",
        swir1="swir1",
        swir2="swir2",
    ):
        """Correct Landsat data for BRDF effects using a c-factor.

        D.P. Roy, H.K. Zhang, J. Ju, J.L. Gomez-Dans, P.E. Lewis, C.B. Schaaf,
        Q. Sun, J. Li, H. Huang, V. Kovalskyy, A general method to normalize
        Landsat reflectance data to nadir BRDF adjusted reflectance,
        Remote Sensing of Environment, Volume 176, April 2016, Pages 255-271

        Interpreted and coded here by Daniel Wiell and Erik Lindquist of the
        United Nations Food and Agriculture Organization

        Transcipted to GEE Python API by Rodrigo E. Principe

        If the band names of the passed image are 'blue', 'green', etc,
        those will be used, if not, relations must be indicated in params.

        :rtype: ee.Image
        """
        original = image
        constants = {"pi": math.pi}

        ### HELPERS ###
        def merge(o1, o2):
            def addAll(target, toAdd):
                for key, val in toAdd.items():
                    target[key] = val

            result = {}
            addAll(result, o1)
            addAll(result, o2)
            return result

        def format_str(string, args=None):
            args = args if args else {}
            allArgs = merge(constants, args)
            return string.format(**allArgs)

        def toImage(img, band, args=None):
            """compute an expression passed in band if it's a str.

            formats the expression in band using format_str if necessary
            :return: one band image.
            """
            if isinstance(band, str):
                # print('band:', band)
                if (band.find(".") > -1) or (band.find(" ") > -1) or (band.find("{") > -1):
                    # print('formatted:', format_str(band, args), '\n')
                    band = img.expression(format_str(band, args), {"i": img})
                else:
                    band = image.select(band)

            return ee.Image(band)

        def set_name(img, name, toAdd, args=None):
            """compute the band (toAdd) with toImage.

            add the band to the passed image and rename it.
            """
            toAdd = toImage(img, toAdd, args)
            return img.addBands(toAdd.rename(name), None, True)

        def setIf(img, name, condition=None, trueValue=None, falseValue=None):
            """TODO missing docstring."""

            def invertMask(mask):
                # return mask.multiply(-1).add(1)
                return mask.Not()

            condition = toImage(img, condition)
            trueMasked = toImage(img, trueValue).mask(toImage(img, condition))
            falseMasked = toImage(img, falseValue).mask(invertMask(condition))
            value = trueMasked.unmask(falseMasked)
            return set_name(img, name, value)

        def x(point):
            """TODO missing docstring."""
            return ee.Number(ee.List(point).get(0))

        def y(point):
            return ee.Number(ee.List(point).get(1))

        def pointBetween(pointA, pointB):
            return ee.Geometry.LineString([pointA, pointB]).centroid().coordinates()

        def slopeBetween(pointA, pointB):
            return ((y(pointA)).subtract(y(pointB))).divide((x(pointA)).subtract(x(pointB)))

        def toLine(pointA, pointB):
            return ee.Geometry.LineString([pointA, pointB])

        ### END HELPERS ###

        # image = image.select([red, green, blue, nir, swir1, swir2],
        #                      ['red', 'green', 'blue', 'nir', 'swir1', 'swir2'])

        inputBandNames = image.bandNames()

        coefficientsByBand = {
            blue: {"fiso": 0.0774, "fgeo": 0.0079, "fvol": 0.0372},
            green: {"fiso": 0.1306, "fgeo": 0.0178, "fvol": 0.0580},
            red: {"fiso": 0.1690, "fgeo": 0.0227, "fvol": 0.0574},
            nir: {"fiso": 0.3093, "fgeo": 0.0330, "fvol": 0.1535},
            swir1: {"fiso": 0.3430, "fgeo": 0.0453, "fvol": 0.1154},
            swir2: {"fiso": 0.2658, "fgeo": 0.0387, "fvol": 0.0639},
        }

        def findCorners(img):
            footprint = ee.Geometry(img.get("system:footprint"))
            bounds = ee.List(footprint.bounds().coordinates().get(0))
            coords = footprint.coordinates()

            def wrap_xs(item):
                return x(item)

            xs = coords.map(wrap_xs)

            def wrap_ys(item):
                return y(item)

            ys = coords.map(wrap_ys)

            def findCorner(targetValue, values):
                def wrap_diff(value):
                    return ee.Number(value).subtract(targetValue).abs()

                diff = values.map(wrap_diff)
                minValue = diff.reduce(ee.Reducer.min())
                idx = diff.indexOf(minValue)
                return ee.Number(coords.get(idx))

            lowerLeft = findCorner(x(bounds.get(0)), xs)
            lowerRight = findCorner(y(bounds.get(1)), ys)
            upperRight = findCorner(x(bounds.get(2)), xs)
            upperLeft = findCorner(y(bounds.get(3)), ys)
            return {
                "upperLeft": upperLeft,
                "upperRight": upperRight,
                "lowerRight": lowerRight,
                "lowerLeft": lowerLeft,
            }

        corners = findCorners(image)

        def viewAngles(img):
            maxDistanceToSceneEdge = 1000000
            maxSatelliteZenith = 7.5
            upperCenter = pointBetween(corners["upperLeft"], corners["upperRight"])
            lowerCenter = pointBetween(corners["lowerLeft"], corners["lowerRight"])
            slope = slopeBetween(lowerCenter, upperCenter)
            slopePerp = ee.Number(-1).divide(slope)
            img = set_name(
                img,
                "viewAz",
                ee.Image(ee.Number(math.pi / 2).subtract((slopePerp).atan())),
            )

            leftLine = toLine(corners["upperLeft"], corners["lowerLeft"])
            rightLine = toLine(corners["upperRight"], corners["lowerRight"])
            leftDistance = ee.FeatureCollection(leftLine).distance(maxDistanceToSceneEdge)
            rightDistance = ee.FeatureCollection(rightLine).distance(maxDistanceToSceneEdge)
            viewZenith = (
                rightDistance.multiply(maxSatelliteZenith * 2)
                .divide(rightDistance.add(leftDistance))
                .subtract(maxSatelliteZenith)
            )
            img = set_name(img, "viewZen", viewZenith.multiply(math.pi).divide(180))

            return img

        image = viewAngles(image)

        def solarPosition(img):
            # Ported from http://pythonfmask.org/en/latest/_modules/fmask/landsatangles.html
            date = ee.Date(ee.Number(img.get("system:time_start")))
            secondsInHour = 3600
            img = set_name(img, "longDeg", ee.Image.pixelLonLat().select("longitude"))

            img = set_name(
                img,
                "latRad",
                ee.Image.pixelLonLat().select("latitude").multiply(math.pi).divide(180),
            )

            img = set_name(
                img,
                "hourGMT",
                ee.Number(date.getRelative("second", "day")).divide(secondsInHour),
            )

            img = set_name(img, "jdp", date.getFraction("year"))  # Julian Date Proportion

            img = set_name(img, "jdpr", "i.jdp * 2 * {pi}")  # Julian Date Proportion in Radians

            img = set_name(img, "meanSolarTime", "i.hourGMT + i.longDeg / 15")

            img = set_name(
                img,
                "localSolarDiff",
                "(0.000075 + 0.001868 * cos(i.jdpr) - 0.032077 * sin(i.jdpr)"
                + "- 0.014615 * cos(2 * i.jdpr) - 0.040849 * sin(2 * i.jdpr))"
                + "* 12 * 60 / {pi}",
            )

            img = set_name(img, "trueSolarTime", "i.meanSolarTime + i.localSolarDiff / 60 - 12")

            img = set_name(img, "angleHour", "i.trueSolarTime * 15 * {pi} / 180")

            img = set_name(
                img,
                "delta",
                "0.006918"
                + "- 0.399912 * cos(1 * i.jdpr) + 0.070257 * sin(1 * i.jdpr)"
                + "- 0.006758 * cos(2 * i.jdpr) + 0.000907 * sin(2 * i.jdpr)"
                + "- 0.002697 * cos(3 * i.jdpr) + 0.001480 * sin(3 * i.jdpr)",
            )

            img = set_name(
                img,
                "cosSunZen",
                "sin(i.latRad) * sin(i.delta) "
                + "+ cos(i.latRad) * cos(i.delta) * cos(i.angleHour)",
            )

            img = set_name(img, "sunZen", "acos(i.cosSunZen)")

            img = set_name(
                img,
                "sinSunAzSW",
                toImage(img, "cos(i.delta) * sin(i.angleHour) / sin(i.sunZen)").clamp(-1, 1),
            )

            img = set_name(
                img,
                "cosSunAzSW",
                "(-cos(i.latRad) * sin(i.delta)"
                + "+ sin(i.latRad) * cos(i.delta) * cos(i.angleHour)) / sin(i.sunZen)",
            )

            img = set_name(img, "sunAzSW", "asin(i.sinSunAzSW)")

            img = setIf(img, "sunAzSW", "i.cosSunAzSW <= 0", "{pi} - i.sunAzSW", "i.sunAzSW")

            img = setIf(
                img,
                "sunAzSW",
                "i.cosSunAzSW > 0 and i.sinSunAzSW <= 0",
                "2 * {pi} + i.sunAzSW",
                "i.sunAzSW",
            )

            img = set_name(img, "sunAz", "i.sunAzSW + {pi}")

            img = setIf(img, "sunAz", "i.sunAz > 2 * {pi}", "i.sunAz - 2 * {pi}", "i.sunAz")

            return img

        image = solarPosition(image)

        def sunZenOut(img):
            # https://nex.nasa.gov/nex/static/media/publication/HLS.v1.0.UserGuide.pdf
            img = set_name(
                img,
                "centerLat",
                ee.Number(
                    ee.Geometry(img.get("system:footprint"))
                    .bounds()
                    .centroid(30)
                    .coordinates()
                    .get(0)
                )
                .multiply(math.pi)
                .divide(180),
            )
            img = set_name(
                img,
                "sunZenOut",
                "(31.0076"
                + "- 0.1272 * i.centerLat"
                + "+ 0.01187 * pow(i.centerLat, 2)"
                + "+ 2.40E-05 * pow(i.centerLat, 3)"
                + "- 9.48E-07 * pow(i.centerLat, 4)"
                + "- 1.95E-09 * pow(i.centerLat, 5)"
                + "+ 6.15E-11 * pow(i.centerLat, 6)) * {pi}/180",
            )

            return img

        image = sunZenOut(image)
        image = set_name(image, "relativeSunViewAz", "i.sunAz - i.viewAz")

        def cosPhaseAngle(img, name, sunZen, viewZen, relativeSunViewAz):
            args = {
                "sunZen": sunZen,
                "viewZen": viewZen,
                "relativeSunViewAz": relativeSunViewAz,
            }

            img = set_name(
                img,
                name,
                toImage(
                    img,
                    "cos({sunZen}) * cos({viewZen})"
                    + "+ sin({sunZen}) * sin({viewZen}) * cos({relativeSunViewAz})",
                    args,
                ).clamp(-1, 1),
            )
            return img

        def rossThick(img, bandName, sunZen, viewZen, relativeSunViewAz):
            args = {
                "sunZen": sunZen,
                "viewZen": viewZen,
                "relativeSunViewAz": relativeSunViewAz,
            }

            img = cosPhaseAngle(img, "cosPhaseAngle", sunZen, viewZen, relativeSunViewAz)
            img = set_name(img, "phaseAngle", "acos(i.cosPhaseAngle)")

            img = set_name(
                img,
                bandName,
                "(({pi}/2 - i.phaseAngle) * i.cosPhaseAngle + sin(i.phaseAngle)) "
                + "/ (cos({sunZen}) + cos({viewZen})) - {pi}/4",
                args,
            )

            return img

        image = rossThick(image, "kvol", "i.sunZen", "i.viewZen", "i.relativeSunViewAz")
        image = rossThick(image, "kvol0", "i.sunZenOut", 0, 0)

        def anglePrime(img, name, angle):
            args = {"b/r": 1, "angle": angle}
            img = set_name(img, "tanAnglePrime", "{b/r} * tan({angle})", args)
            img = setIf(img, "tanAnglePrime", "i.tanAnglePrime < 0", 0)
            img = set_name(img, name, "atan(i.tanAnglePrime)")
            return img

        def liThin(img, bandName, sunZen, viewZen, relativeSunViewAz):
            # From https://modis.gsfc.nasa.gov/data/atbd/atbd_mod09.pdf
            args = {
                "sunZen": sunZen,
                "viewZen": viewZen,
                "relativeSunViewAz": relativeSunViewAz,
                "h/b": 2,
            }

            img = anglePrime(img, "sunZenPrime", sunZen)
            img = anglePrime(img, "viewZenPrime", viewZen)
            img = cosPhaseAngle(
                img,
                "cosPhaseAnglePrime",
                "i.sunZenPrime",
                "i.viewZenPrime",
                relativeSunViewAz,
            )
            img = set_name(
                img,
                "distance",
                "sqrt(pow(tan(i.sunZenPrime), 2) + pow(tan(i.viewZenPrime), 2)"
                + "- 2 * tan(i.sunZenPrime) * tan(i.viewZenPrime)"
                + "* cos({relativeSunViewAz}))",
                args,
            )
            img = set_name(img, "temp", "1/cos(i.sunZenPrime) + 1/cos(i.viewZenPrime)")
            img = set_name(
                img,
                "cosT",
                toImage(
                    img,
                    "{h/b} * sqrt(pow(i.distance, 2)"
                    + "+ pow(tan(i.sunZenPrime) * tan(i.viewZenPrime)"
                    + "* sin({relativeSunViewAz}), 2))/i.temp",
                    args,
                ).clamp(-1, 1),
            )
            img = set_name(img, "t", "acos(i.cosT)")
            img = set_name(img, "overlap", "(1/{pi}) * (i.t - sin(i.t) * i.cosT) * (i.temp)")
            img = setIf(img, "overlap", "i.overlap > 0", 0)
            img = set_name(
                img,
                bandName,
                "i.overlap - i.temp"
                + "+ (1/2) * (1 + i.cosPhaseAnglePrime) * (1/cos(i.sunZenPrime))"
                + "* (1/cos(i.viewZenPrime))",
            )

            return img

        image = liThin(image, "kgeo", "i.sunZen", "i.viewZen", "i.relativeSunViewAz")
        image = liThin(image, "kgeo0", "i.sunZenOut", 0, 0)

        def brdf(img, bandName, kvolBand, kgeoBand, coefficients):
            args = merge(
                coefficients,
                {
                    "kvol": "3 * i."
                    + kvolBand,  # check this multiplication factor. Is there an 'optimal' value?  Without a factor here, there is not enough correction.
                    "kgeo": "i." + kgeoBand,
                },
            )

            img = set_name(img, bandName, "{fiso} + {fvol} * {kvol} + {fgeo} * {kvol}", args)
            return img

        def applyCFactor(img, bandName, coefficients):
            img = brdf(img, "brdf", "kvol", "kgeo", coefficients)
            img = brdf(img, "brdf0", "kvol0", "kgeo0", coefficients)
            img = set_name(img, "cFactor", "i.brdf0 / i.brdf", coefficients)
            img = set_name(img, bandName, "{bandName} * i.cFactor", {"bandName": "i." + bandName})
            return img

        def adjustBands(img):
            """apply cFactor per band."""
            for bandName in coefficientsByBand:
                coefficients = coefficientsByBand[bandName]
                img = applyCFactor(img, bandName, coefficients)
            return img

        image = adjustBands(image).select(inputBandNames)

        return original.addBands(image, overwrite=True)
