"""Cloud masking functions for various Earth Engine datasets."""

import warnings
from typing import Optional, Union

import ee

from .ee_extra_utils import _get_platform_STAC


def maskClouds(
    x: Union[ee.Image, ee.ImageCollection],
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
        x: Image or Image Collection to mask
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

    platform_dict = _get_platform_STAC(x)
    platform = platform_dict["platform"]

    # Sentinel-2/3 cloud masking
    if "COPERNICUS/S2" in platform or "COPERNICUS/S3" in platform:
        return _mask_s2_s3(
            x, method, prob, maskCirrus, maskShadows, scaledImage, dark, cloudDist, buffer, cdi
        )
    # Landsat cloud masking
    elif "LANDSAT" in platform:
        return _mask_landsat(x, platform, maskShadows, maskCirrus)
    # MODIS cloud masking
    elif "MODIS" in platform:
        return _mask_modis(x, platform, maskShadows, maskCirrus)
    else:
        warnings.warn("This platform is not supported for cloud masking.")
        return x


def _mask_s2_s3(x, method, prob, maskCirrus, maskShadows, scaledImage, dark, cloudDist, buffer, cdi):
    """Mask clouds for Sentinel-2 and Sentinel-3."""

    def cloud_prob(img):
        """Mask using cloud probability."""
        clouds = ee.Image(img.get("cloud_mask")).select("probability")
        is_cloud = clouds.gte(prob).rename("CLOUD_MASK")
        return img.addBands(is_cloud)

    def cloud_score_plus(img):
        """Mask using cloud score+."""
        clouds = img.select("cs_cdf")
        is_cloud = clouds.lte(1 - (prob / 100)).rename("CLOUD_MASK")
        return img.addBands(is_cloud)

    def qa_mask(img):
        """Mask using QA band."""
        qa = img.select("QA60")
        cloud_bit_mask = 1 << 10
        is_cloud = qa.bitwiseAnd(cloud_bit_mask).eq(0)
        if maskCirrus:
            cirrus_bit_mask = 1 << 11
            is_cloud = is_cloud.And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        is_cloud = is_cloud.Not().rename("CLOUD_MASK")
        return img.addBands(is_cloud)

    def cdi_mask(img):
        """Mask using Cloud Displacement Index."""
        idx = img.get("system:index")
        s2_toa = ee.ImageCollection("COPERNICUS/S2").filter(ee.Filter.eq("system:index", idx)).first()
        cdi_img = ee.Algorithms.Sentinel2.CDI(s2_toa)
        is_cloud = cdi_img.lt(cdi).rename("CLOUD_MASK_CDI")
        return img.addBands(is_cloud)

    def get_shadows(img):
        """Detect cloud shadows."""
        not_water = img.select("SCL").neq(6)
        if not scaledImage:
            dark_pixels = img.select("B8").lt(dark * 1e4).multiply(not_water)
        else:
            dark_pixels = img.select("B8").lt(dark).multiply(not_water)

        shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get("MEAN_SOLAR_AZIMUTH_ANGLE")))
        cloud_projection = img.select("CLOUD_MASK").directionalDistanceTransform(
            shadow_azimuth, cloudDist / 10
        )
        cloud_projection = (
            cloud_projection.reproject(crs=img.select(0).projection(), scale=10).select("distance").mask()
        )
        is_shadow = cloud_projection.multiply(dark_pixels).rename("SHADOW_MASK")
        return img.addBands(is_shadow)

    def clean_dilate(img):
        """Dilate cloud and shadow masks."""
        is_cloud_shadow = img.select("CLOUD_MASK")
        if cdi is not None:
            is_cloud_shadow = is_cloud_shadow.And(img.select("CLOUD_MASK_CDI"))
        if maskShadows:
            is_cloud_shadow = is_cloud_shadow.add(img.select("SHADOW_MASK")).gt(0)
        is_cloud_shadow = (
            is_cloud_shadow.focal_min(20, units="meters")
            .focal_max(buffer * 2 / 10, units="meters")
            .rename("CLOUD_SHADOW_MASK")
        )
        return img.addBands(is_cloud_shadow)

    def apply_mask(img):
        """Apply cloud/shadow mask."""
        return img.updateMask(img.select("CLOUD_SHADOW_MASK").Not())

    # Apply masking based on method
    if isinstance(x, ee.image.Image):
        if method == "cloud_prob":
            s2_clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            filt = ee.Filter.equals(leftField="system:index", rightField="system:index")
            s2_with_mask = ee.Join.saveFirst("cloud_mask").apply(ee.ImageCollection(x), s2_clouds, filt)
            masked = ee.ImageCollection(s2_with_mask).map(cloud_prob).first()
        elif method == "cloud_score+":
            qa_band = "cs_cdf"
            s2_clouds = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED").select(qa_band)
            s2_with_mask = ee.ImageCollection(x).linkCollection(s2_clouds, [qa_band])
            masked = ee.ImageCollection(s2_with_mask).map(cloud_score_plus).first()
        elif method == "qa":
            masked = qa_mask(x)

        if cdi is not None:
            masked = cdi_mask(masked)
        if maskShadows:
            masked = get_shadows(masked)
        masked = apply_mask(clean_dilate(masked))
    else:
        if method == "cloud_prob":
            s2_clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
            filt = ee.Filter.equals(leftField="system:index", rightField="system:index")
            s2_with_mask = ee.Join.saveFirst("cloud_mask").apply(x, s2_clouds, filt)
            masked = ee.ImageCollection(s2_with_mask).map(cloud_prob)
        elif method == "cloud_score+":
            qa_band = "cs_cdf"
            s2_clouds = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED").select(qa_band)
            s2_with_mask = x.linkCollection(s2_clouds, [qa_band])
            masked = ee.ImageCollection(s2_with_mask).map(cloud_score_plus)
        elif method == "qa":
            masked = x.map(qa_mask)

        if cdi is not None:
            masked = masked.map(cdi_mask)
        if maskShadows:
            masked = masked.map(get_shadows)
        masked = masked.map(clean_dilate).map(apply_mask)

    return masked


def _mask_landsat(x, platform, maskShadows, maskCirrus):
    """Mask clouds for Landsat products."""
    # Determine which Landsat version and collection
    is_c2 = "C02" in platform or "C2" in platform
    is_l8_l9 = "LC08" in platform or "LC09" in platform
    is_l7 = "LE07" in platform
    is_l45 = "LT04" in platform or "LT05" in platform

    def mask_l8_l9_c2(img):
        """Mask Landsat 8/9 Collection 2."""
        qa = img.select("QA_PIXEL")
        not_cloud = qa.bitwiseAnd(1 << 3).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 4).eq(0))
        if maskCirrus:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        return img.updateMask(not_cloud)

    def mask_l457_c2(img):
        """Mask Landsat 4/5/7 Collection 2."""
        qa = img.select("QA_PIXEL")
        not_cloud = qa.bitwiseAnd(1 << 3).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 4).eq(0))
        return img.updateMask(not_cloud)

    def mask_l8_c1(img):
        """Mask Landsat 8 Collection 1."""
        qa = img.select("pixel_qa")
        clouds_bit_mask = 1 << 5
        mask = qa.bitwiseAnd(clouds_bit_mask).eq(0)
        if maskShadows:
            cloud_shadow_bit_mask = 1 << 3
            mask = mask.And(qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0))
        return img.updateMask(mask)

    def mask_l457_c1(img):
        """Mask Landsat 4/5/7 Collection 1."""
        qa = img.select("pixel_qa")
        cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7))
        if maskShadows:
            cloud = cloud.Or(qa.bitwiseAnd(1 << 3))
        mask2 = img.mask().reduce(ee.Reducer.min())
        return img.updateMask(cloud.Not()).updateMask(mask2)

    if isinstance(x, ee.image.Image):
        if is_c2 and (is_l8_l9 or is_l7):
            return mask_l8_l9_c2(x) if is_l8_l9 else mask_l457_c2(x)
        elif is_c2 and is_l45:
            return mask_l457_c2(x)
        elif is_l8_l9:
            return mask_l8_c1(x)
        else:
            return mask_l457_c1(x)
    else:
        if is_c2 and (is_l8_l9 or is_l7):
            mask_func = mask_l8_l9_c2 if is_l8_l9 else mask_l457_c2
        elif is_c2 and is_l45:
            mask_func = mask_l457_c2
        elif is_l8_l9:
            mask_func = mask_l8_c1
        else:
            mask_func = mask_l457_c1
        return x.map(mask_func)


def _mask_modis(x, platform, maskShadows, maskCirrus):
    """Mask clouds for MODIS products."""

    def mask_mod09ga(img):
        """Mask MOD09GA."""
        qa = img.select("state_1km")
        not_cloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 8).eq(0))
        return img.updateMask(not_cloud)

    def mask_mod09q1(img):
        """Mask MOD09Q1."""
        qa = img.select("State")
        not_cloud = qa.bitwiseAnd(1 << 0).eq(0)
        if maskShadows:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 2).eq(0))
        if maskCirrus:
            not_cloud = not_cloud.And(qa.bitwiseAnd(1 << 8).eq(0))
        return img.updateMask(not_cloud)

    def mask_mod13(img):
        """Mask MOD13."""
        qa = img.select("SummaryQA")
        not_cloud = qa.eq(0)
        return img.updateMask(not_cloud)

    def mask_mod17_mod16(img):
        """Mask MOD17A2H and MOD16A2."""
        if "MOD17" in platform:
            qa = img.select("Psn_QC")
        else:
            qa = img.select("ET_QC")
        not_cloud = qa.bitwiseAnd(1 << 3).eq(0)
        return img.updateMask(not_cloud)

    if isinstance(x, ee.image.Image):
        if "MOD09GA" in platform or "MYD09GA" in platform:
            return mask_mod09ga(x)
        elif "MOD09Q1" in platform or "MYD09Q1" in platform or "MOD09A1" in platform or "MYD09A1" in platform:
            return mask_mod09q1(x)
        elif "MOD13" in platform or "MYD13" in platform:
            return mask_mod13(x)
        elif "MOD17" in platform or "MYD17" in platform or "MOD16" in platform or "MYD16" in platform:
            return mask_mod17_mod16(x)
        else:
            warnings.warn("This MODIS platform is not supported for cloud masking.")
            return x
    else:
        if "MOD09GA" in platform or "MYD09GA" in platform:
            return x.map(mask_mod09ga)
        elif "MOD09Q1" in platform or "MYD09Q1" in platform or "MOD09A1" in platform or "MYD09A1" in platform:
            return x.map(mask_mod09q1)
        elif "MOD13" in platform or "MYD13" in platform:
            return x.map(mask_mod13)
        elif "MOD17" in platform or "MYD17" in platform or "MOD16" in platform or "MYD16" in platform:
            return x.map(mask_mod17_mod16)
        else:
            warnings.warn("This MODIS platform is not supported for cloud masking.")
            return x
