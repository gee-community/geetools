"""Test the ImageCollection class."""
from typing import Optional

import ee
import numpy as np
import pytest

import geetools


def reduce(collection: ee.ImageCollection, geometry: Optional[ee.Geometry] = None) -> ee.Dictionary:
    """Compute the mean reduction on the first image of the imageCollection."""
    first = collection.first()
    geometry = first.geometry() if geometry is None else geometry.geometry()
    geometry = geometry.centroid(1).buffer(100)
    return first.reduceRegion(ee.Reducer.mean(), geometry, 1)


class TestMaskClouds:
    """Test the ``maskClouds`` method."""

    def test_mask_s2_sr(self, s2_sr, num_regression):
        masked = s2_sr.geetools.maskClouds(prob=75, buffer=300, cdi=-0.5)
        num_regression.check(reduce(masked).getInfo())


class TestClosest:
    """Test the ``closest`` method."""

    def test_closest_s2_sr(self, s2_sr, data_regression):
        closest = s2_sr.geetools.closest("2021-10-01")
        data_regression.check(closest.size().getInfo())


class TestSpectralIndices:
    """Test the ``spectralIndices`` method."""

    def test_spectral_indices(self, s2_sr, num_regression):
        indices = s2_sr.geetools.spectralIndices(["NDVI", "NDWI"])
        num_regression.check(reduce(indices).getInfo())


class TestGetScaleParams:
    """Test the ``getScaleParams`` method."""

    def test_get_scale_params(self, s2_sr, data_regression):
        scale_params = s2_sr.geetools.getScaleParams()
        data_regression.check(scale_params)


class TestGetOffsetParams:
    """Test the ``getOffsetParams`` method."""

    def test_get_offset_params(self, s2_sr, data_regression):
        offset_params = s2_sr.geetools.getOffsetParams()
        data_regression.check(offset_params)


class TestScaleAndOffset:
    """Test the ``scaleAndOffset`` method."""

    def test_scale_and_offset(self, s2_sr, num_regression):
        scaled = s2_sr.geetools.scaleAndOffset()
        num_regression.check(reduce(scaled).getInfo())


class TestPreprocess:
    """Test the ``preprocess`` method."""

    def test_preprocess(self, s2_sr, num_regression):
        preprocessed = s2_sr.geetools.preprocess()
        values = {k: np.nan if v is None else v for k, v in reduce(preprocessed).getInfo().items()}
        num_regression.check(values)


class TestGetSTAC:
    """Test the ``getSTAC`` method."""

    def test_get_stac(self, s2_sr, data_regression):
        stac = s2_sr.geetools.getSTAC()
        stac["extent"].pop("temporal")  # it will change all the time
        data_regression.check(stac)


class TestGetDOI:
    """Test the ``getDOI`` method."""

    def test_get_doi(self, s2_sr, data_regression):
        doi = s2_sr.geetools.getDOI()
        data_regression.check(doi)


class TestGetCitation:
    """Test the ``getCitation`` method."""

    def test_get_citation(self, s2_sr, data_regression):
        citation = s2_sr.geetools.getCitation()
        data_regression.check(citation)


class TestPanSharpen:
    """Test the ``panSharpen`` method."""

    def test_pan_sharpen(self, l8_toa, num_regression):
        sharpened = l8_toa.geetools.panSharpen()
        num_regression.check(reduce(sharpened).getInfo())


class TestTasseledCap:
    """Test the ``tasseledCap`` method."""

    def test_tasseled_cap(self, s2, num_regression):
        tc = s2.geetools.tasseledCap()
        num_regression.check(reduce(tc).getInfo())


class TestAppend:
    """Test the ``append`` method."""

    def test_append(self, s2_sr, data_regression):
        appended = s2_sr.geetools.append(s2_sr.first())
        data_regression.check(appended.size().getInfo())

    def test_deprecated_add(self, s2_sr, data_regression):
        with pytest.deprecated_call():
            appended = geetools.imagecollection.add(s2_sr, s2_sr.first())
            data_regression.check(appended.size().getInfo())


class TestcollectionMask:
    """Test the ``collectionMask`` method."""

    def test_collection_mask(self, s2_sr, amazonas, num_regression):
        masked = s2_sr.geetools.collectionMask()
        num_regression.check(reduce(ee.ImageCollection([masked]), amazonas).getInfo())

    def test_deprecated_mask(self, s2_sr, amazonas, num_regression):
        with pytest.deprecated_call():
            masked = geetools.imagecollection.allMasked(s2_sr)
            num_regression.check(reduce(ee.ImageCollection([masked]), amazonas).getInfo())


class TestIloc:
    """Test the iloc class."""

    def test_iloc(self, s2_sr, num_regression):
        ic = ee.ImageCollection([s2_sr.geetools.iloc(0).subtract(s2_sr.first())])
        values = {k: np.nan if v is None else v for k, v in reduce(ic).getInfo().items()}
        num_regression.check(values)

    def test_deprecated_get_image(self, s2_sr, num_regression):
        with pytest.deprecated_call():
            image = geetools.imagecollection.getImage(s2_sr, 0).subtract(s2_sr.first())
            ic = ee.ImageCollection([image])
            values = {k: np.nan if v is None else v for k, v in reduce(ic).getInfo().items()}
            num_regression.check(values)


class TestIntegral:
    """Test the ``integral`` method."""

    def test_integral(self, s2_sr, amazonas, num_regression):
        integral = s2_sr.limit(10).geetools.integral("B4").select("integral")
        ic = ee.ImageCollection([integral])
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
        num_regression.check(values)

    def test_deprecated_integral(self, s2_sr, amazonas, num_regression):
        with pytest.deprecated_call():
            integral = geetools.imagecollection.area_under_curve(s2_sr.limit(10), "B4").select(
                "under_curve"
            )
            ic = ee.ImageCollection([integral])
            values = {
                k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()
            }
            num_regression.check(values)


class TestOutliers:
    """Test the ``outliers`` method."""

    def test_outliers(self, s2_sr, amazonas, num_regression):
        ic = s2_sr.limit(10).geetools.outliers()
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
        num_regression.check(values)

    def test_outliers_with_bands(self, s2_sr, amazonas, num_regression):
        ic = s2_sr.limit(10).geetools.outliers(bands=["B4", "B2"])
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
        num_regression.check(values)

    def test_outliers_with_sigma(self, s2_sr, amazonas, num_regression):
        ic = s2_sr.limit(10).geetools.outliers(sigma=3)
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
        num_regression.check(values)

    def test_outliers_with_drop(self, s2_sr, amazonas, num_regression):
        ic = s2_sr.limit(10).geetools.outliers(drop=True)
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
        num_regression.check(values)

    def test_deprecated_outliers(self, s2_sr, amazonas, num_regression):
        with pytest.deprecated_call():
            ic = geetools.imagecollection.outliers(s2_sr.limit(10), ["B4"])
            values = {
                k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()
            }
            num_regression.check(values)
