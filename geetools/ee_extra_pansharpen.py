"""Pan-sharpening functions for Earth Engine images."""

from typing import Any, Dict, List, Optional, TypeVar, Union

import ee

ImageLike = TypeVar("ImageLike", ee.Image, ee.ImageCollection)

# Platform-specific band configurations
PLATFORM_BANDS = {
    # Landsat 9 (LC09)
    "LANDSAT/LC09/C02/T1_TOA": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC09/C02/T1_RT_TOA": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC09/C02/T1_L2": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC09/C02/T1": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC09/C02/T1_RT": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    # Landsat 8 (LC08)
    "LANDSAT/LC08/C02/T1_TOA": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC08/C02/T1_RT_TOA": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC08/C02/T1_L2": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC08/C02/T1": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC08/C02/T1_RT": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC08/C02/T2": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    "LANDSAT/LC08/C02/T2_TOA": {"sharpenable": ["B2", "B3", "B4", "B5", "B6", "B7"], "pan": "B8"},
    # Landsat 7 (LE07)
    "LANDSAT/LE07/C02/T1_TOA": {"sharpenable": ["B1", "B2", "B3", "B4", "B5", "B7"], "pan": "B8"},
    "LANDSAT/LE07/C02/T1_L2": {"sharpenable": ["B1", "B2", "B3", "B4", "B5", "B7"], "pan": "B8"},
    "LANDSAT/LE07/C02/T1": {"sharpenable": ["B1", "B2", "B3", "B4", "B5", "B7"], "pan": "B8"},
    "LANDSAT/LE07/C02/T2": {"sharpenable": ["B1", "B2", "B3", "B4", "B5", "B7"], "pan": "B8"},
    "LANDSAT/LE07/C02/T2_TOA": {"sharpenable": ["B1", "B2", "B3", "B4", "B5", "B7"], "pan": "B8"},
}


def panSharpen(
    img: ImageLike,
    method: str = "SFIM",
    qa: Optional[Union[str, List[str]]] = None,
    prefix: str = "geetools",
    **kwargs: Any,
) -> ImageLike:
    """Apply panchromatic sharpening to an Image or ImageCollection.

    Args:
        img: Image or ImageCollection to sharpen
        method: Sharpening algorithm ('SFIM', 'HPFA', 'PCS', 'SM')
        qa: Optional quality metrics to calculate
        prefix: Prefix for property names
        **kwargs: Additional keyword arguments for ee.Image.reduceRegion()

    Returns:
        Sharpened Image or ImageCollection
    """
    valid_methods = ["SFIM", "HPFA", "PCS", "SM"]
    if method not in valid_methods:
        raise ValueError(f"Method '{method}' not supported. Use one of {valid_methods}.")

    def get_platform_bands(test_img: ee.Image) -> Dict[str, Any]:
        """Get correct platform bands for sharpening."""
        dataset_id = ee.String(test_img.get("system:id")).getInfo()
        if dataset_id not in PLATFORM_BANDS:
            raise ValueError(f"Platform '{dataset_id}' not supported for pan-sharpening.")
        return PLATFORM_BANDS[dataset_id]

    def apply_sharpening(test_img: ee.Image) -> ee.Image:
        """Identify and apply correct sharpening algorithm."""
        bands_config = get_platform_bands(test_img)
        source = test_img.select(bands_config["sharpenable"])
        pan = test_img.select(bands_config["pan"])

        if method == "SFIM":
            sharpened = _sharpen_sfim(source, pan)
        elif method == "HPFA":
            sharpened = _sharpen_hpfa(source, pan)
        elif method == "PCS":
            sharpened = _sharpen_pcs(source, pan, **kwargs)
        elif method == "SM":
            sharpened = _sharpen_sm(source, pan)

        # Copy properties from original
        sharpened = ee.Image(ee.Element.copyProperties(sharpened, source, pan.propertyNames()))
        sharpened = sharpened.updateMask(source.mask())

        return sharpened

    if isinstance(img, ee.image.Image):
        return apply_sharpening(img)
    elif isinstance(img, ee.imagecollection.ImageCollection):
        return img.map(apply_sharpening)
    else:
        raise TypeError("Input must be ee.Image or ee.ImageCollection")


def _sharpen_sfim(img: ee.Image, pan: ee.Image) -> ee.Image:
    """Apply Smoothing Filter-based Intensity Modulation (SFIM) sharpening.

    Reference: Liu, J. G. (2000). Smoothing Filter-based Intensity Modulation: A
    spectral preserve image fusion technique for improving spatial details.
    International Journal of Remote Sensing, 21(18), 3461-3472.
    """
    img_scale = img.projection().nominalScale()
    pan_scale = pan.projection().nominalScale()
    kernel_width = img_scale.divide(pan_scale)
    kernel = ee.Kernel.square(radius=kernel_width.divide(2))
    pan_smooth = pan.reduceNeighborhood(reducer=ee.Reducer.mean(), kernel=kernel)

    img = img.resample("bicubic")
    sharp = img.multiply(pan).divide(pan_smooth)
    sharp = sharp.reproject(pan.projection())
    return sharp


def _sharpen_hpfa(img: ee.Image, pan: ee.Image) -> ee.Image:
    """Apply High-Pass Filter Addition (HPFA) sharpening.

    Reference: Gangkofner, U. G., Pradhan, P. S., & Holcomb, D. W. (2008).
    Optimizing the High-Pass Filter Addition Technique for Image Fusion.
    Photogrammetric Engineering & Remote Sensing, 74(9), 1107-1118.
    """
    img_scale = img.projection().nominalScale()
    pan_scale = pan.projection().nominalScale()
    kernel_width = img_scale.divide(pan_scale).multiply(2).add(1).int()

    img = img.resample("bicubic")

    center_val = kernel_width.pow(2).subtract(1)
    center = kernel_width.divide(2).int()
    kernel_row = ee.List.repeat(-1, kernel_width)
    kernel_list = ee.List.repeat(kernel_row, kernel_width)
    kernel_list = kernel_list.set(center, ee.List(kernel_list.get(center)).set(center, center_val))
    kernel = ee.Kernel.fixed(weights=kernel_list, normalize=True)

    pan_hpf = pan.convolve(kernel)
    sharp = img.add(pan_hpf)
    sharp = sharp.reproject(pan.projection())

    return sharp


def _sharpen_pcs(img: ee.Image, pan: ee.Image, **kwargs: Any) -> ee.Image:
    """Apply Principal Component Substitution (PCS) sharpening.

    PCS replaces the first principal component with the panchromatic band
    after histogram matching.
    """
    img = img.resample("bicubic").reproject(pan.projection())
    band_names = img.bandNames()

    band_means = img.reduceRegion(ee.Reducer.mean(), **kwargs)
    img_means = band_means.toImage(band_names)
    img_centered = img.subtract(img_means)

    # Calculate covariance
    img_arr = img_centered.toArray()
    covar = img_arr.reduceRegion(ee.Reducer.centeredCovariance(), **kwargs)
    covar_arr = ee.Array(covar.get("array"))

    # Get eigenvectors
    eigens = covar_arr.eigen()
    eigenvectors = eigens.slice(1, 1)
    img_arr_2d = img_arr.toArray(1)

    # Project onto eigenvectors
    principal_components = (
        ee.Image(eigenvectors).matrixMultiply(img_arr_2d).arrayProject([0]).arrayFlatten([band_names])
    )

    pc1_name = principal_components.bandNames().get(0)
    pc1 = principal_components.select([pc1_name]).rename(["PC1"])
    pan_renamed = pan.rename(["pan"])

    # Match histogram of pan to PC1
    pan_matched = _match_histogram_simple(pan_renamed, pc1).rename([pc1_name])

    # Replace PC1 with matched pan
    principal_components = principal_components.addBands(pan_matched, overwrite=True)

    # Inverse transform
    sharp_centered = (
        ee.Image(eigenvectors)
        .matrixSolve(principal_components.toArray().toArray(1))
        .arrayProject([0])
        .arrayFlatten([band_names])
    )
    sharp = sharp_centered.add(img_means)

    return sharp


def _sharpen_sm(img: ee.Image, pan: ee.Image) -> ee.Image:
    """Apply Simple Mean (SM) sharpening.

    Simple average of resampled multispectral and panchromatic bands.
    """
    img = img.resample("bicubic")
    sharp = img.add(pan).multiply(0.5)
    sharp = sharp.reproject(pan.projection())
    return sharp


def _match_histogram_simple(source: ee.Image, target: ee.Image) -> ee.Image:
    """Simple histogram matching between source and target images.

    Uses linear stretching based on mean and standard deviation.
    """
    source_mean = source.reduceRegion(ee.Reducer.mean()).get(source.bandNames().get(0))
    target_mean = target.reduceRegion(ee.Reducer.mean()).get(target.bandNames().get(0))

    source_stddev = source.reduceRegion(ee.Reducer.stdDev()).get(source.bandNames().get(0))
    target_stddev = target.reduceRegion(ee.Reducer.stdDev()).get(target.bandNames().get(0))

    # Linear stretch
    matched = source.subtract(source_mean).multiply(target_stddev).divide(source_stddev).add(target_mean)

    return matched
