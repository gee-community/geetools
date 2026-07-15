"""Utilities for geetools ee_extra extraction module."""

import json
from pathlib import Path
from typing import Any, Union

import ee


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
