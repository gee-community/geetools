"""Spectral indices calculations for Earth Engine images."""

from typing import Any, Dict, List, Union

import ee

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
    "LANDSAT/LC08": {"BLUE": "B2", "GREEN": "B3", "RED": "B4", "NIR": "B5", "SWIR1": "B6", "SWIR2": "B7"},
    "LANDSAT/LC09": {"BLUE": "B2", "GREEN": "B3", "RED": "B4", "NIR": "B5", "SWIR1": "B6", "SWIR2": "B7"},
    "COPERNICUS/S2": {"BLUE": "B2", "GREEN": "B3", "RED": "B4", "NIR": "B8", "SWIR1": "B11", "SWIR2": "B12"},
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
    "vegetation": ["NDVI", "EVI", "SAVI", "NDII", "NDMI", "GNDVI", "MSI", "NDTI"],
    "burn": ["NBR", "NBR2"],
    "water": ["NDWI", "MNDWI"],
    "snow": ["NDSI"],
    "urban": ["NDBI"],
    "all": list(SPECTRAL_INDICES.keys()),
}


def spectralIndices(
    src: Union[ee.Image, ee.ImageCollection],
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
) -> Union[ee.Image, ee.ImageCollection]:
    """Compute spectral indices for an image or image collection."""
    indices_to_compute = _get_indices_to_compute(index)

    is_image = isinstance(src, ee.image.Image)
    ref = src if is_image else src.first()
    dataset_id = ee.String(ref.get("system:id")).getInfo()
    band_map = _get_band_mapping(dataset_id)

    def compute_indices(img: ee.Image) -> ee.Image:
        result = img
        for idx_name in indices_to_compute:
            if idx_name not in SPECTRAL_INDICES:
                continue
            try:
                result = result.addBands(_compute_index_simple(img, idx_name, band_map, L))
            except Exception:
                continue
        if drop:
            index_names = [idx for idx in indices_to_compute if idx in SPECTRAL_INDICES]
            result = result.select(img.bandNames().cat(ee.List(index_names)))
        return result

    if is_image:
        return compute_indices(src)
    return src.map(compute_indices)


def _get_indices_to_compute(index: Union[str, List[str]]) -> List[str]:
    """Parse index input and return list of indices to compute."""
    if isinstance(index, list):
        return index
    return CATEGORIES.get(index, [index] if index in SPECTRAL_INDICES else ["NDVI"])


def _get_band_mapping(dataset_id: str) -> Dict[str, str]:
    """Get band names for the dataset based on dataset ID."""
    for key, mapping in BAND_MAPPING.items():
        if key in dataset_id:
            return mapping
    return {"BLUE": "B2", "GREEN": "B3", "RED": "B4", "NIR": "B8", "SWIR1": "B11", "SWIR2": "B12"}


def _compute_index_simple(img: ee.Image, index_name: str, bands: Dict[str, str], L: float = 1.0) -> ee.Image:
    """Compute index using band math."""
    if index_name == "NDVI":
        nir, red = img.select(bands["NIR"]), img.select(bands["RED"])
        return nir.subtract(red).divide(nir.add(red)).rename("NDVI")

    elif index_name == "EVI":
        nir, red, blue = img.select(bands["NIR"]), img.select(bands["RED"]), img.select(bands["BLUE"])
        return (
            nir.subtract(red)
            .divide(nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1))
            .multiply(2.5)
            .rename("EVI")
        )

    elif index_name == "SAVI":
        nir, red = img.select(bands["NIR"]), img.select(bands["RED"])
        return nir.subtract(red).divide(nir.add(red).add(L)).multiply(1 + L).rename("SAVI")

    elif index_name in ("NDMI", "NDII"):
        nir, swir1 = img.select(bands["NIR"]), img.select(bands["SWIR1"])
        return nir.subtract(swir1).divide(nir.add(swir1)).rename(index_name)

    elif index_name == "NBR":
        nir, swir2 = img.select(bands["NIR"]), img.select(bands["SWIR2"])
        return nir.subtract(swir2).divide(nir.add(swir2)).rename("NBR")

    elif index_name == "NBR2":
        swir1, swir2 = img.select(bands["SWIR1"]), img.select(bands["SWIR2"])
        return swir1.subtract(swir2).divide(swir1.add(swir2)).rename("NBR2")

    elif index_name == "NDWI":
        green, nir = img.select(bands["GREEN"]), img.select(bands["NIR"])
        return green.subtract(nir).divide(green.add(nir)).rename("NDWI")

    elif index_name == "MNDWI":
        green, swir1 = img.select(bands["GREEN"]), img.select(bands["SWIR1"])
        return green.subtract(swir1).divide(green.add(swir1)).rename("MNDWI")

    elif index_name == "NDBI":
        swir1, nir = img.select(bands["SWIR1"]), img.select(bands["NIR"])
        return swir1.subtract(nir).divide(swir1.add(nir)).rename("NDBI")

    elif index_name == "NDSI":
        green, swir1 = img.select(bands["GREEN"]), img.select(bands["SWIR1"])
        return green.subtract(swir1).divide(green.add(swir1)).rename("NDSI")

    elif index_name == "NDTI":
        swir1, swir2 = img.select(bands["SWIR1"]), img.select(bands["SWIR2"])
        return swir1.subtract(swir2).divide(swir1.add(swir2)).rename("NDTI")

    elif index_name == "GNDVI":
        nir, green = img.select(bands["NIR"]), img.select(bands["GREEN"])
        return nir.subtract(green).divide(nir.add(green)).rename("GNDVI")

    elif index_name == "MSI":
        return img.select(bands["SWIR1"]).divide(img.select(bands["NIR"])).rename("MSI")

    else:
        raise ValueError(f"Index {index_name} not supported")
