# coding=utf-8
"""Legacy Helper functions for visualizing data on a map."""
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Removed as this lib does not deal with map anymore")
def stretch_std(image, region, bands=None, std=1, scale=None):
    """Get mins and maxs values for stretching a visualization using standard deviation."""
    raise NotImplementedError(
        "Interactive methods have been moved to ipygee. For non-interactive, rely on your visualization library like rasterio, matplotlib, etc."
    )


@deprecated(version="1.0.0", reason="Removed as this lib does not deal with map anymore")
def stretch_percentile(image, region, bands=None, percentile=90, scale=None):
    """Get mins and maxs values for stretching a visualization using percentiles."""
    raise NotImplementedError(
        "Interactive methods have been moved to ipygee. For non-interactive, rely on your visualization library like rasterio, matplotlib, etc."
    )
