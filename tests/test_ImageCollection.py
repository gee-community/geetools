"""Test the ImageCollection class."""

import ee

import geetools  # noqa: F401


def reduce(collection: ee.ImageCollection) -> ee.Dictionary:
    """Compute the mean reduction on the first image of the imageCollection."""
    first = collection.first()
    geometry = first.geometry().centroid().buffer(100)
    return first.reduceRegion(ee.Reducer.mean(), geometry, 1)


class TestMaskClouds:
    """Test the ``maskClouds`` method."""

    def test_mask_s2_sr(self, s2_sr, data_regression):
        masked = s2_sr.geetools.maskClouds(prob=75, buffer=300, cdi=-0.5)
        data_regression.check(reduce(masked).getInfo())


class TestClosest:
    """Test the ``closest`` method."""

    def test_closest_s2_sr(self, s2_sr, data_regression):
        closest = s2_sr.geetools.closest("2021-10-01")
        data_regression.check(closest.size().getInfo())


class TestSpectralIndices:
    """Test the ``spectralIndices`` method."""

    def test_spectral_indices(self, s2_sr, data_regression):
        indices = s2_sr.geetools.spectralIndices(["NDVI", "NDWI"])
        data_regression.check(reduce(indices).getInfo())


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

    def test_scale_and_offset(self, s2_sr, data_regression):
        scaled = s2_sr.geetools.scaleAndOffset()
        data_regression.check(reduce(scaled).getInfo())


class TestPreprocess:
    """Test the ``preprocess`` method."""

    def test_preprocess(self, s2_sr, data_regression):
        preprocessed = s2_sr.geetools.preprocess()
        data_regression.check(reduce(preprocessed).getInfo())


class TestGetSTAC:
    """Test the ``getSTAC`` method."""

    def test_get_stac(self, s2_sr, data_regression):
        stac = s2_sr.geetools.getSTAC()
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

    def test_pan_sharpen(self, l8_toa, data_regression):
        sharpened = l8_toa.geetools.panSharpen()
        data_regression.check(reduce(sharpened).getInfo())


class TestTasseledCap:
    """Test the ``tasseledCap`` method."""

    def test_tasseled_cap(self, s2, data_regression):
        tc = s2.geetools.tasseledCap()
        data_regression.check(reduce(tc).getInfo())
