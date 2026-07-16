"""Pan-sharpening functions for Earth Engine images."""

from typing import Any, List, Optional, Union

import ee

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
    src: Union[ee.Image, ee.ImageCollection],
    method: str = "SFIM",
    qa: Optional[Union[str, List[str]]] = None,
    prefix: str = "geetools",
    **kwargs: Any,
) -> Union[ee.Image, ee.ImageCollection]:
    """Apply panchromatic sharpening to an Image or ImageCollection.

    Args:
        src: Image or ImageCollection to sharpen
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

    is_image = isinstance(src, ee.image.Image)
    ref = src if is_image else src.first()

    # Hoist platform detection outside any mapped function
    dataset_id = ee.Asset(ref.get("system:id").getInfo()).parent.as_posix()
    if dataset_id not in PLATFORM_BANDS:
        raise ValueError(f"Platform '{dataset_id}' not supported for pan-sharpening.")
    bands_config = PLATFORM_BANDS[dataset_id]

    def apply_sharpening(img: ee.Image) -> ee.Image:
        source = img.select(bands_config["sharpenable"])
        pan = img.select(bands_config["pan"])

        if method == "SFIM":
            sharpened = _sharpen_sfim(source, pan)
        elif method == "HPFA":
            sharpened = _sharpen_hpfa(source, pan)
        elif method == "PCS":
            sharpened = _sharpen_pcs(source, pan, **kwargs)
        elif method == "SM":
            sharpened = _sharpen_sm(source, pan)

        sharpened = ee.Image(ee.Element.copyProperties(sharpened, source, pan.propertyNames()))
        return sharpened.updateMask(source.mask())

    if is_image:
        return apply_sharpening(src)
    return src.map(apply_sharpening)


def _sharpen_sfim(img: ee.Image, pan: ee.Image) -> ee.Image:
    """Apply Smoothing Filter-based Intensity Modulation (SFIM) sharpening."""
    img_scale = img.projection().nominalScale()
    pan_scale = pan.projection().nominalScale()
    kernel_width = img_scale.divide(pan_scale)
    kernel = ee.Kernel.square(radius=kernel_width.divide(2))
    pan_smooth = pan.reduceNeighborhood(reducer=ee.Reducer.mean(), kernel=kernel)
    img = img.resample("bicubic")
    return img.multiply(pan).divide(pan_smooth).reproject(pan.projection())


def _sharpen_hpfa(img: ee.Image, pan: ee.Image) -> ee.Image:
    """Apply High-Pass Filter Addition (HPFA) sharpening."""
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
    return img.add(pan.convolve(kernel)).reproject(pan.projection())


def _sharpen_pcs(img: ee.Image, pan: ee.Image, **kwargs: Any) -> ee.Image:
    """Apply Principal Component Substitution (PCS) sharpening."""
    img = img.resample("bicubic").reproject(pan.projection())
    band_names = img.bandNames()
    band_means = img.reduceRegion(ee.Reducer.mean(), **kwargs)
    img_means = band_means.toImage(band_names)
    img_centered = img.subtract(img_means)
    img_arr = img_centered.toArray()
    covar = img_arr.reduceRegion(ee.Reducer.centeredCovariance(), **kwargs)
    covar_arr = ee.Array(covar.get("array"))
    eigens = covar_arr.eigen()
    eigenvectors = eigens.slice(1, 1)
    img_arr_2d = img_arr.toArray(1)
    principal_components = (
        ee.Image(eigenvectors).matrixMultiply(img_arr_2d).arrayProject([0]).arrayFlatten([band_names])
    )
    pc1_name = principal_components.bandNames().get(0)
    pc1 = principal_components.select([pc1_name]).rename(["PC1"])
    pan_matched = _match_histogram_simple(pan.rename(["pan"]), pc1).rename([pc1_name])
    principal_components = principal_components.addBands(pan_matched, overwrite=True)
    sharp_centered = (
        ee.Image(eigenvectors)
        .matrixSolve(principal_components.toArray().toArray(1))
        .arrayProject([0])
        .arrayFlatten([band_names])
    )
    return sharp_centered.add(img_means)


def _sharpen_sm(img: ee.Image, pan: ee.Image) -> ee.Image:
    """Apply Simple Mean (SM) sharpening."""
    return img.resample("bicubic").add(pan).multiply(0.5).reproject(pan.projection())


def _match_histogram_simple(source: ee.Image, target: ee.Image) -> ee.Image:
    """Linear histogram matching based on mean and standard deviation."""
    source_mean = source.reduceRegion(ee.Reducer.mean()).get(source.bandNames().get(0))
    target_mean = target.reduceRegion(ee.Reducer.mean()).get(target.bandNames().get(0))
    source_stddev = source.reduceRegion(ee.Reducer.stdDev()).get(source.bandNames().get(0))
    target_stddev = target.reduceRegion(ee.Reducer.stdDev()).get(target.bandNames().get(0))
    return source.subtract(source_mean).multiply(target_stddev).divide(source_stddev).add(target_mean)
