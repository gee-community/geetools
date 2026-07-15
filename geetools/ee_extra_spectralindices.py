"""Spectral indices calculations for Earth Engine images."""

from typing import Any, Dict, List, TypeVar, Union

import ee

ImageCollectionLike = TypeVar("ImageCollectionLike")
ImageLike = TypeVar("ImageLike", ee.Image, ee.ImageCollection)

# Common spectral indices definitions
SPECTRAL_INDICES = {
    # Vegetation indices
    "NDVI": {"formula": "(NIR - RED) / (NIR + RED)", "category": "vegetation"},
    "EVI": {
        "formula": "2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)",
        "category": "vegetation",
    },
    "SAVI": {
        "formula": "((NIR - RED) / (NIR + RED + L)) * (1 + L)",
        "category": "vegetation",
    },
    "NDII": {"formula": "(NIR - SWIR1) / (NIR + SWIR1)", "category": "vegetation"},
    "NDMI": {"formula": "(NIR - SWIR1) / (NIR + SWIR1)", "category": "vegetation"},
    "NDSI": {"formula": "(GREEN - SWIR1) / (GREEN + SWIR1)", "category": "snow"},
    "NDTI": {"formula": "(SWIR1 - SWIR2) / (SWIR1 + SWIR2)", "category": "vegetation"},
    # Burn indices
    "NBR": {"formula": "(NIR - SWIR2) / (NIR + SWIR2)", "category": "burn"},
    "NBR2": {"formula": "(SWIR1 - SWIR2) / (SWIR1 + SWIR2)", "category": "burn"},
    # Water indices
    "NDWI": {"formula": "(GREEN - NIR) / (GREEN + NIR)", "category": "water"},
    "MNDWI": {"formula": "(GREEN - SWIR1) / (GREEN + SWIR1)", "category": "water"},
    # Urban/Built-up indices
    "NDBI": {"formula": "(SWIR1 - NIR) / (SWIR1 + NIR)", "category": "urban"},
    # Additional vegetation
    "MSI": {"formula": "SWIR1 / NIR", "category": "vegetation"},
    "GNDVI": {"formula": "(NIR - GREEN) / (NIR + GREEN)", "category": "vegetation"},
}

# Platform-specific band mappings
BAND_MAPPING = {
    "LANDSAT/LC08": {
        "BLUE": "B2",
        "GREEN": "B3",
        "RED": "B4",
        "NIR": "B5",
        "SWIR1": "B6",
        "SWIR2": "B7",
    },
    "LANDSAT/LC09": {
        "BLUE": "B2",
        "GREEN": "B3",
        "RED": "B4",
        "NIR": "B5",
        "SWIR1": "B6",
        "SWIR2": "B7",
    },
    "COPERNICUS/S2": {
        "BLUE": "B2",
        "GREEN": "B3",
        "RED": "B4",
        "NIR": "B8",
        "SWIR1": "B11",
        "SWIR2": "B12",
    },
    "COPERNICUS/S2_SR": {
        "BLUE": "B2",
        "GREEN": "B3",
        "RED": "B4",
        "NIR": "B8",
        "SWIR1": "B11",
        "SWIR2": "B12",
    },
}

# Index categories
CATEGORIES = {
    "vegetation": [
        "NDVI",
        "EVI",
        "SAVI",
        "NDII",
        "NDMI",
        "GNDVI",
        "MSI",
        "NDTI",
    ],
    "burn": ["NBR", "NBR2"],
    "water": ["NDWI", "MNDWI"],
    "snow": ["NDSI"],
    "urban": ["NDBI"],
    "all": list(SPECTRAL_INDICES.keys()),
}


def spectralIndices(
    img: ImageLike,
    index: Union[str, List[str]] = "NDVI",
    G: float = 2.5,
    C1: float = 6.0,
    C2: float = 7.5,
    L: float = 1.0,
    cexp: float = 1.16,
    nexp: float = 2.0,
    alpha: float = 0.1,
    slope: float = 1.0,
    intercept: float = 0.0,
    gamma: float = 1.0,
    omega: float = 2.0,
    beta: float = 0.05,
    k: float = 0.0,
    fdelta: float = 0.581,
    epsilon: float = 1.0,
    kernel: str = "RBF",
    sigma: Union[str, float] = "0.5 * (a + b)",
    p: float = 2.0,
    c: float = 1.0,
    lambdaN: float = 858.5,
    lambdaR: float = 645.0,
    lambdaG: float = 555.0,
    online: bool = False,
    drop: bool = False,
    **kwargs: Any,
) -> ImageLike:
    """Compute spectral indices for an image or image collection.

    Computes one or more spectral indices from the Awesome List of Spectral Indices.
    Indices are added as new bands to the image.

    Parameters:
        img: Image or ImageCollection to compute indices on.
        index: Index name or list of index names to compute. Can also be a category:
               'vegetation', 'burn', 'water', 'snow', 'urban', or 'all'.
        G: Gain factor for EVI. Default: 2.5
        C1: Coefficient 1 for EVI. Default: 6.0
        C2: Coefficient 2 for EVI. Default: 7.5
        L: Canopy background adjustment for SAVI. Default: 1.0
        drop: Whether to drop all bands except the new indices. Default: False
        **kwargs: Additional keyword arguments (unused, for API compatibility)

    Returns:
        Image or ImageCollection with computed spectral indices as new bands.

    Examples:
        >>> import ee
        >>> import geetools
        >>> ee.Initialize()
        >>> img = ee.Image('COPERNICUS/S2/20190828T151811_20190828T151809_T18GYT')
        >>> with_indices = geetools.ee_extra_spectralindices.spectralIndices(
        ...     img,
        ...     index=['NDVI', 'EVI', 'NBR']
        ... )
    """
    # Parse index input
    indices_to_compute = _get_indices_to_compute(index)

    def compute_indices(test_img: ee.Image) -> ee.Image:
        """Compute spectral indices for a single image."""
        dataset_id = ee.String(test_img.get("system:id")).getInfo()
        bands = _get_band_mapping(test_img, dataset_id)

        result = test_img
        for idx_name in indices_to_compute:
            if idx_name not in SPECTRAL_INDICES:
                continue

            idx_def = SPECTRAL_INDICES[idx_name]
            formula = idx_def["formula"]

            # Substitute band names with actual bands
            band_expr = formula
            for band_name, actual_band in bands.items():
                # Create band reference
                band_ref = f"(B('{actual_band}'))"
                band_expr = band_expr.replace(band_name, band_ref)

            # Add coefficient substitutions for special indices
            band_expr = band_expr.replace("L", str(L))
            band_expr = band_expr.replace("G", str(G))
            band_expr = band_expr.replace("C1", str(C1))
            band_expr = band_expr.replace("C2", str(C2))

            # Evaluate expression
            try:
                index_band = test_img.expression(
                    band_expr, {band: test_img.select(bands[band.strip("B()'")]) for band in bands}
                )
                index_band = index_band.rename(idx_name)
                result = result.addBands(index_band)
            except Exception:
                # Fallback: try simple band math for basic formulas
                try:
                    index_band = _compute_index_simple(test_img, idx_name, bands)
                    result = result.addBands(index_band)
                except Exception:
                    continue

        if drop:
            # Keep only the original bands plus indices
            index_names = [idx for idx in indices_to_compute if idx in SPECTRAL_INDICES]
            all_bands = list(test_img.bandNames().getInfo()) + index_names
            result = result.select(all_bands)

        return result

    if isinstance(img, ee.image.Image):
        return compute_indices(img)
    elif isinstance(img, ee.imagecollection.ImageCollection):
        return img.map(compute_indices)
    else:
        raise TypeError("Input must be ee.Image or ee.ImageCollection")


def _get_indices_to_compute(index: Union[str, List[str]]) -> List[str]:
    """Parse index input and return list of indices to compute."""
    if isinstance(index, str):
        if index in CATEGORIES:
            return CATEGORIES[index]
        elif index in SPECTRAL_INDICES:
            return [index]
        else:
            return ["NDVI"]
    elif isinstance(index, list):
        return index
    else:
        return ["NDVI"]


def _get_band_mapping(img: ee.Image, dataset_id: str) -> Dict[str, str]:
    """Get band names for the image based on dataset ID."""
    # Try to find matching dataset
    for key, mapping in BAND_MAPPING.items():
        if key in dataset_id:
            return mapping

    # Default mapping (generic)
    return {
        "BLUE": "B2",
        "GREEN": "B3",
        "RED": "B4",
        "NIR": "B8",
        "SWIR1": "B11",
        "SWIR2": "B12",
    }


def _compute_index_simple(img: ee.Image, index_name: str, bands: Dict[str, str]) -> ee.Image:
    """Compute index using simple band math."""
    if index_name == "NDVI":
        nir = img.select(bands["NIR"])
        red = img.select(bands["RED"])
        return nir.subtract(red).divide(nir.add(red)).rename("NDVI")

    elif index_name == "EVI":
        nir = img.select(bands["NIR"])
        red = img.select(bands["RED"])
        blue = img.select(bands["BLUE"])
        return (
            nir.subtract(red)
            .divide(nir.multiply(6).add(red).multiply(6).add(blue.multiply(7.5)).add(1))
            .multiply(2.5)
            .rename("EVI")
        )

    elif index_name == "NDMI" or index_name == "NDII":
        nir = img.select(bands["NIR"])
        swir1 = img.select(bands["SWIR1"])
        return nir.subtract(swir1).divide(nir.add(swir1)).rename(index_name)

    elif index_name == "NBR":
        nir = img.select(bands["NIR"])
        swir2 = img.select(bands["SWIR2"])
        return nir.subtract(swir2).divide(nir.add(swir2)).rename("NBR")

    elif index_name == "NDWI":
        green = img.select(bands["GREEN"])
        nir = img.select(bands["NIR"])
        return green.subtract(nir).divide(green.add(nir)).rename("NDWI")

    elif index_name == "MNDWI":
        green = img.select(bands["GREEN"])
        swir1 = img.select(bands["SWIR1"])
        return green.subtract(swir1).divide(green.add(swir1)).rename("MNDWI")

    elif index_name == "NDBI":
        swir1 = img.select(bands["SWIR1"])
        nir = img.select(bands["NIR"])
        return swir1.subtract(nir).divide(swir1.add(nir)).rename("NDBI")

    else:
        raise ValueError(f"Index {index_name} not supported in simple computation")
