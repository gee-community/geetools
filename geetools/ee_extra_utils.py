"""Utilities for geetools ee_extra extraction module."""

import json
from pathlib import Path
from typing import Any, Union

import ee
import requests

from .ee_extra_tasseled_cap import PLATFORM_COEFFICIENTS

# Cache for fetched catalog data
_CATALOG_CACHE: dict[str, dict] = {}


def _load_JSON(filename: str = "ee-catalog-ids.json") -> Any:
    """Load JSON file from geetools data directory.

    Args:
        filename: JSON filename to load from data directory

    Returns:
        Parsed JSON content
    """
    data_dir = Path(__file__).parent / "data"
    json_file = data_dir / filename

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {json_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {json_file}: {e}")


def _get_catalog_data() -> dict[str, Any]:
    """Fetch scale/offset catalog from GitHub.

    Downloads the scale and offset parameters for all datasets from the
    ee-catalog-scale-offset-params repository.

    Returns:
        Dictionary with dataset IDs as keys and scale/offset parameters as values

    Raises:
        requests.RequestException: If unable to fetch from GitHub
    """
    if "catalog" in _CATALOG_CACHE:
        return _CATALOG_CACHE["catalog"]

    url = "https://raw.githubusercontent.com/davemlz/ee-catalog-scale-offset-params/main/list/ee-catalog-scale-offset-parameters.json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        _CATALOG_CACHE["catalog"] = data
        return data
    except requests.RequestException as e:
        raise requests.RequestException(
            f"Failed to fetch catalog from GitHub: {e}. " "Ensure you have an active internet connection."
        )


def _get_scale_offset_params(dataset_id: str) -> tuple[dict, dict]:
    """Get scale and offset parameters for a dataset.

    Args:
        dataset_id: Earth Engine dataset ID (e.g., 'COPERNICUS/S2_SR')

    Returns:
        Tuple of (scale_params, offset_params) dictionaries
    """
    catalog = _get_catalog_data()

    # Look up the dataset in the catalog
    if dataset_id not in catalog:
        return {}, {}

    dataset_info = catalog[dataset_id]
    scale_params = dataset_info.get("scale_params", {})
    offset_params = dataset_info.get("offset_params", {})

    return scale_params, offset_params


def _get_platform_STAC(x: Union[ee.Image, ee.ImageCollection]) -> dict:
    """Get platform and other STAC information from image or image collection.

    Args:
        x: ee.Image or ee.ImageCollection

    Returns:
        Dictionary with platform and other metadata
    """
    if isinstance(x, ee.imagecollection.ImageCollection):
        x = x.first()

    # Get the dataset ID from the image
    dataset_id = ee.String(x.get("system:id")).getInfo()

    # Extract platform from dataset ID
    if dataset_id:
        dataset_id.split("/")[0]
        return {"platform": dataset_id}

    # Fallback: try to get from properties
    properties = x.propertyNames().getInfo()

    # Common platform detection patterns
    {
        "COPERNICUS/S2_SR": "COPERNICUS/S2_SR",
        "COPERNICUS/S2_SR_HARMONIZED": "COPERNICUS/S2_SR_HARMONIZED",
        "LANDSAT": "LANDSAT",
    }

    for prop in properties:
        if "SPACECRAFT_ID" in prop or "SPACECRAFT" in prop:
            return {"platform": dataset_id or "unknown"}

    return {"platform": dataset_id or "unknown"}


def _get_tc_coefficients(platform: str) -> dict:
    """Get platform-specific tasseled cap transformation coefficients.

    Args:
        platform: Platform name retrieved from STAC

    Returns:
        Dictionary with band names and transformation coefficients for
        brightness (TCB), greenness (TCG), and wetness (TCW)

    Raises:
        Exception: If platform has no supported coefficients
    """
    if platform not in PLATFORM_COEFFICIENTS:
        available = list(PLATFORM_COEFFICIENTS.keys())
        raise Exception(
            f"Sorry, satellite platform {platform} not supported for tasseled "
            f"cap transformation! Use one of {available}"
        )

    return PLATFORM_COEFFICIENTS[platform]
