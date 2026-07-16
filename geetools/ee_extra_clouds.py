"""Cloud masking functions for various Earth Engine datasets."""

import warnings
from typing import Optional, Union

import ee


def maskClouds(
    src: Union[ee.Image, ee.ImageCollection],
    method: str = "cloud_prob",
    prob: Union[int, float] = 60,
    maskCirrus: bool = True,
    maskShadows: bool = True,
    scaledImage: bool = False,
    dark: float = 0.15,
    cloudDist: int = 1000,
    buffer: int = 250,
    cdi: Optional[float] = None,
) -> Union[ee.Image, ee.ImageCollection]:
    """Mask clouds and shadows in an image or image collection.

    Args:
        src: Image or ImageCollection to mask
        method: Method used to mask clouds ('cloud_prob', 'cloud_score+', or 'qa')
        prob: Cloud probability threshold (0-100)
        maskCirrus: Whether to mask cirrus clouds
        maskShadows: Whether to mask cloud shadows
        scaledImage: Whether pixel values are scaled to [0,1]
        dark: NIR threshold for shadow detection
        cloudDist: Maximum distance in meters for shadow detection
        buffer: Distance in meters to dilate cloud objects
        cdi: Cloud Displacement Index threshold

    Returns:
        Cloud-shadow masked image or image collection
    """
    valid_methods = ["cloud_prob", "cloud_score+", "qa"]
    if method not in valid_methods:
        raise Exception(f"'{method}' is not a valid method. Use one of {valid_methods}.")

    is_image = isinstance(src, ee.image.Image)
    col = ee.ImageCollection([src]) if is_image else src

    asset_id = ee.String((src if is_image else src.first()).get("system:id")).getInfo()
    platform = ee.Asset(asset_id).parent.as_posix()

    if "COPERNICUS/S2" in platform or "COPERNICUS/S3" in platform:
        result = _mask_s2_s3(
            col, method, prob, maskCirrus, maskShadows, scaledImage, dark, cloudDist, buffer, cdi
        )
    elif "LANDSAT" in platform:
        result = _mask_landsat(col, platform, maskShadows, maskCirrus)
    elif "MODIS" in platform:
        result = _mask_modis(col, platform, maskShadows, maskCirrus)
    else:
        warnings.warn("This platform is not supported for cloud masking.")
        return src

    return result.first() if is_image else result


def _mask_s2_s3(col, method, prob, maskCirrus, maskShadows, scaledImage, dark, cloudDist, buffer, cdi):
    """Mask clouds for Sentinel-2 and Sentinel-3."""

    def cloud_prob_mask(img):
        clouds = ee.Image(img.get("cloud_mask")).select("probability")
        return img.addBands(clouds.gte(prob).rename("CLOUD_MASK"))

    def cloud_score_plus_mask(img):
        return img.addBands(img.select("cs_cdf").lte(1 - (prob / 100)).rename("CLOUD_MASK"))

    def qa_mask(img):
        qa = img.select("QA60")
        is_cloud = qa.bitwiseAnd(1 << 10).eq(0)
        if maskCirrus:
            is_cloud = is_cloud.And(qa.bitwiseAnd(1 << 11).eq(0))
        return img.addBands(is_cloud.Not().rename("CLOUD_MASK"))

    def cdi_mask(img):
        idx = img.get("system:index")
        s2_toa = ee.ImageCollection("COPERNICUS/S2").filter(ee.Filter.eq("system:index", idx)).first()
        return img.addBands(ee.Algorithms.Sentinel2.CDI(s2_toa).lt(cdi).rename("CLOUD_MASK_CDI"))

    def get_shadows(img):
        not_water = img.select("SCL").neq(6)
        dark_pixels = img.select("B8").lt(dark * 1e4 if not scaledImage else dark).multiply(not_water)
        shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get("MEAN_SOLAR_AZIMUTH_ANGLE")))
        cloud_projection = img.select("CLOUD_MASK").directionalDistanceTransform(
            shadow_azimuth, cloudDist / 10
        )
        cloud_projection = (
            cloud_projection.reproject(crs=img.select(0).projection(), scale=10).select("distance").mask()
        )
        return img.addBands(cloud_projection.multiply(dark_pixels).rename("SHADOW_MASK"))

    def clean_dilate(img):
        is_cloud_shadow = img.select("CLOUD_MASK")
        if cdi is not None:
            is_cloud_shadow = is_cloud_shadow.And(img.select("CLOUD_MASK_CDI"))
        if maskShadows:
            is_cloud_shadow = is_cloud_shadow.add(img.select("SHADOW_MASK")).gt(0)
        return img.addBands(
            is_cloud_shadow.focal_min(20, units="meters")
            .focal_max(buffer * 2 / 10, units="meters")
            .rename("CLOUD_SHADOW_MASK")
        )

    def apply_mask(img):
        return img.updateMask(img.select("CLOUD_SHADOW_MASK").Not())

    if method == "cloud_prob":
        s2_clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
        filt = ee.Filter.equals(leftField="system:index", rightField="system:index")
        col = ee.ImageCollection(ee.Join.saveFirst("cloud_mask").apply(col, s2_clouds, filt)).map(
            cloud_prob_mask
        )
    elif method == "cloud_score+":
        qa_band = "cs_cdf"
        s2_clouds = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED").select(qa_band)
        col = col.linkCollection(s2_clouds, [qa_band]).map(cloud_score_plus_mask)
    elif method == "qa":
        col = col.map(qa_mask)

    if cdi is not None:
        col = col.map(cdi_mask)
    if maskShadows:
        col = col.map(get_shadows)

    return col.map(clean_dilate).map(apply_mask)


def _mask_landsat(col, platform, maskShadows, maskCirrus):
    """Mask clouds for Landsat products."""
    is_c2 = "C02" in platform or "C2" in platform
    is_l8_l9 = "LC08" in platform or "LC09" in platform
    is_l7 = "LE07" in platform
    is_l45 = "LT04" in platform or "LT05" in platform

    def mask_l8_l9_c2(img):
        qa = img.select("QA_PIXEL")
        not_cloud = qa.bitwiseAnd(1 << 3).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 4).eq(0))
        if maskCirrus:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        return img.updateMask(not_cloud)

    def mask_l457_c2(img):
        qa = img.select("QA_PIXEL")
        not_cloud = qa.bitwiseAnd(1 << 3).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 4).eq(0))
        return img.updateMask(not_cloud)

    def mask_l8_c1(img):
        qa = img.select("pixel_qa")
        not_cloud = qa.bitwiseAnd(1 << 5).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 3).eq(0))
        return img.updateMask(not_cloud)

    def mask_l457_c1(img):
        qa = img.select("pixel_qa")
        cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7))
        if maskShadows:
            cloud = cloud.Or(qa.bitwiseAnd(1 << 3))
        return img.updateMask(cloud.Not()).updateMask(img.mask().reduce(ee.Reducer.min()))

    if is_c2 and (is_l8_l9 or is_l7):
        mask_func = mask_l8_l9_c2 if is_l8_l9 else mask_l457_c2
    elif is_c2 and is_l45:
        mask_func = mask_l457_c2
    elif is_l8_l9:
        mask_func = mask_l8_c1
    else:
        mask_func = mask_l457_c1

    return col.map(mask_func)


def _mask_modis(col, platform, maskShadows, maskCirrus):
    """Mask clouds for MODIS products."""

    def mask_mod09ga(img):
        qa = img.select("state_1km")
        not_cloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 8).eq(0))
        return img.updateMask(not_cloud)

    def mask_mod09q1(img):
        qa = img.select("State")
        not_cloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 8).eq(0))
        return img.updateMask(not_cloud)

    def mask_mod13(img):
        return img.updateMask(img.select("SummaryQA").eq(0))

    def mask_mod17(img):
        return img.updateMask(img.select("Psn_QC").bitwiseAnd(1 << 3).eq(0))

    def mask_mod16(img):
        return img.updateMask(img.select("ET_QC").bitwiseAnd(1 << 3).eq(0))

    if "MOD09GA" in platform or "MYD09GA" in platform:
        mask_func = mask_mod09ga
    elif any(p in platform for p in ["MOD09Q1", "MYD09Q1", "MOD09A1", "MYD09A1"]):
        mask_func = mask_mod09q1
    elif "MOD13" in platform or "MYD13" in platform:
        mask_func = mask_mod13
    elif "MOD17" in platform or "MYD17" in platform:
        mask_func = mask_mod17
    elif "MOD16" in platform or "MYD16" in platform:
        mask_func = mask_mod16
    else:
        warnings.warn("This MODIS platform is not supported for cloud masking.")
        return col

    return col.map(mask_func)
