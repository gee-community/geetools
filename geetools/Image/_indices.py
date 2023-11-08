"""Methods to compute the spectral indices for the Image class."""
from __future__ import annotations

import ee_extra.Spectral.core


def indices(cls) -> dict:
    """Return the list of indices implemented in this module.

    Returns:
        List of indices implemented in this module

    Examples:
        .. jupyter-execute::

            import ee, geetools

            ind = ee.Image.geetools.indices()["BAIS2"]
            print(ind["long_name"])
            print(ind["formula"])
            print(ind["reference"])
    """
    return ee_extra.Spectral.core.indices()
