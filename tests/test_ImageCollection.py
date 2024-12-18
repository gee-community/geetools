"""Test the ImageCollection class."""
from __future__ import annotations

import io

import ee
import numpy as np
import pytest
from jsonschema import validate
from matplotlib import pyplot as plt

import geetools


def reduce(
    collection: ee.ImageCollection, geometry: ee.Geometry | None = None, reducer: str = "first"
) -> ee.Dictionary:
    """Compute the mean reduction on the first image of the imageCollection."""
    image = getattr(collection, reducer)()
    geometry = image.geometry() if geometry is None else geometry.geometry()
    geometry = geometry.centroid(1).buffer(100)
    return image.reduceRegion(ee.Reducer.mean(), geometry, 1)


def round_dict(d: dict = None, decimals: int = 2) -> dict:
    """Round all the values of a dictionary."""
    d = d or {}
    for k, v in d.items():
        if isinstance(v, dict):
            round_dict(v, decimals)
        else:
            d[k] = round(v, decimals)
    return d


class TestMaskClouds:
    """Test the ``maskClouds`` method."""

    @pytest.mark.xfail(
        reason="ee_extra is joining ImgeCollection which is not compatible with ee v1.x."
    )
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

    @pytest.mark.xfail(
        reason="ee_extra is joining ImgeCollection which is not compatible with ee v1.x."
    )
    def test_preprocess(self, s2_sr, num_regression):
        preprocessed = s2_sr.geetools.preprocess()
        values = {k: np.nan if v is None else v for k, v in reduce(preprocessed).getInfo().items()}
        num_regression.check(values)


class TestGetSTAC:
    """Test the ``getSTAC`` method."""

    def test_get_stac(self, s2_sr):
        stac = s2_sr.geetools.getSTAC()
        assert stac["id"] == "COPERNICUS/S2_SR_HARMONIZED"

    def test_get_stac_schema(self, s2_sr, stac_schema):
        stac = s2_sr.geetools.getSTAC()
        validate(stac, stac_schema)


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

    @pytest.mark.xfail(reason="ee_extra does not accept C02 L08 collection yet.")
    def test_pan_sharpen(self, l8_toa, num_regression):
        sharpened = l8_toa.geetools.panSharpen()
        num_regression.check(reduce(sharpened).getInfo())


class TestTasseledCap:
    """Test the ``tasseledCap`` method."""

    def test_tasseled_cap(self, l8_sr, num_regression):
        tc = l8_sr.geetools.tasseledCap()
        num_regression.check(reduce(tc).getInfo())


class TestAppend:
    """Test the ``append`` method."""

    def test_append(self, s2_sr, data_regression):
        appended = s2_sr.geetools.append(s2_sr.first())
        data_regression.check(appended.size().getInfo())


class TestcollectionMask:
    """Test the ``collectionMask`` method."""

    def test_collection_mask(self, s2_sr, amazonas, num_regression):
        masked = s2_sr.geetools.collectionMask()
        num_regression.check(reduce(ee.ImageCollection([masked]), amazonas).getInfo())


class TestIloc:
    """Test the iloc class."""

    def test_iloc(self, s2_sr, num_regression):
        ic = ee.ImageCollection([s2_sr.geetools.iloc(0).subtract(s2_sr.first())])
        values = {k: np.nan if v is None else v for k, v in reduce(ic).getInfo().items()}
        num_regression.check(values)


class TestIntegral:
    """Test the ``integral`` method."""

    def test_integral(self, s2_sr, amazonas, num_regression):
        integral = s2_sr.limit(10).geetools.integral("B4").select("integral")
        ic = ee.ImageCollection([integral])
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
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


class TestToXarray:
    """Test the ``toXarray`` method."""

    def test_to_xarray(self, s2_sr, data_regression):
        ds = s2_sr.geetools.to_xarray()

        # drop all the dtype as they are not consistently setup depending on the xarray version
        def drop_dtype(d=ds):
            for k, v in ds.items():
                if isinstance(v, dict):
                    drop_dtype(v)
                elif k == "dtype":
                    del ds[k]

        drop_dtype()

        # ds = ds.astype(np.float64)
        data_regression.check(ds.to_dict(data=False))


class TestValidPixel:
    """Test the ``validPixel`` method."""

    def test_validPixel(self, s2_sr, amazonas, num_regression):
        s2_sr = s2_sr.filterDate("2021-01-01", "2021-01-31")
        ic = ee.ImageCollection([s2_sr.geetools.validPixel("B1")])
        values = {k: np.nan if v is None else v for k, v in reduce(ic, amazonas).getInfo().items()}
        num_regression.check(values)


class TestContainsBandNames:
    """Test the ``containsBandNames`` method and derivated."""

    def test_contains_all(self, s2_sr):
        ic = s2_sr.select(["B2", "B3", "B4"])
        ic = ic.geetools.containsAllBands(["B2", "B3"])
        assert ic.size().getInfo() == 2449

    def test_contains_all_mismatch(self, s2_sr):
        ic = s2_sr.select(["B2", "B3", "B4"])
        ic = ic.geetools.containsAllBands(["B2", "B3", "B5"])
        assert ic.size().getInfo() == 0

    def test_contains_any(self, s2_sr):
        ic = s2_sr.select(["B2", "B3", "B4"])
        ic = ic.geetools.containsAnyBands(["B2", "B3", "B5"])
        assert ic.size().getInfo() == 2449

    def test_contains_any_mismatch(self, s2_sr):
        ic = s2_sr.select(["B2", "B3", "B4"])
        ic = ic.geetools.containsAnyBands(["B5", "B6"])
        assert ic.size().getInfo() == 0


class TestAggregateArray:
    """Test the ``aggregateArray`` method."""

    def test_aggregate_array(self, s2_sr, data_regression):
        # reduce the number of properties beforehand to avoid the test to fail
        keys = s2_sr.first().propertyNames()
        keys = keys.filter(ee.Filter.stringStartsWith("item", "system:")).remove("system:version")
        s2_sr_filtered = s2_sr.limit(3).map(
            lambda i: ee.Image().addBands(i).copyProperties(i, keys)
        )
        aggregated = s2_sr_filtered.geetools.aggregateArray()
        data_regression.check(aggregated.getInfo())

    def test_aggregate_array_with_properties(self, s2_sr, data_regression):
        aggregated = s2_sr.limit(10).geetools.aggregateArray(["system:time_start", "system:index"])
        data_regression.check(aggregated.getInfo())


class TestGroupInterval:
    """Test the ``groupInterval`` method."""

    def test_group_interval(self, jaxa_rainfall):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        grouped = ic.geetools.groupInterval()
        assert grouped.size().getInfo() == 3
        assert ee.ImageCollection(grouped.get(0)).size().getInfo() == 720

    def test_group_interval_with_interval(self, jaxa_rainfall):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        grouped = ic.geetools.groupInterval(duration=2)
        assert grouped.size().getInfo() == 2
        assert ee.ImageCollection(grouped.get(0)).size().getInfo() == 1440
        assert ee.ImageCollection(grouped.get(1)).size().getInfo() == 719

    def test_group_interval_with_interval_and_unit(self, jaxa_rainfall):
        # get 3 days worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-01-04")
        grouped = ic.geetools.groupInterval(duration=1, unit="day")
        assert grouped.size().getInfo() == 3
        assert ee.ImageCollection(grouped.get(0)).size().getInfo() == 24

    def test_group_interval_drop_empty_collections(self, s2_sr):
        ic = s2_sr.filterDate("2021-01-01", "2021-01-07")
        grouped = ic.geetools.groupInterval(duration=1, unit="day")
        # Each collection must not be empty
        for i in range(grouped.size().getInfo()):
            imgCollection = ee.ImageCollection(grouped.get(i))
            assert imgCollection.size().getInfo() != 0

    def test_deprecated_make_equal_interval(self, jaxa_rainfall):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        with pytest.deprecated_call():
            grouped = geetools.imagecollection.makeEqualInterval(ic)
            assert grouped.size().getInfo() == 3
            assert ee.ImageCollection(grouped.get(0)).size().getInfo() == 720

    def test_deprecated_make_day_intervals(self, jaxa_rainfall):
        # get 3 days worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-01-04")
        with pytest.deprecated_call():
            grouped = geetools.imagecollection.makeDayIntervals(ic)
            assert grouped.size().getInfo() == 3
            assert ee.ImageCollection(grouped.get(0)).size().getInfo() == 24


class TestReduceInterval:
    """Test the ``reduceInterval`` method."""

    def test_reduce_interval(self, jaxa_rainfall, amazonas, num_regression):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        reduced = ic.geetools.reduceInterval()
        values = {
            k: np.nan if v is None else v for k, v in reduce(reduced, amazonas).getInfo().items()
        }
        num_regression.check(values)

    def test_reduce_interval_with_reducer(self, jaxa_rainfall, amazonas, num_regression):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        reduced = ic.geetools.reduceInterval("max")
        values = reduce(reduced, amazonas).getInfo()
        values = {k: np.nan if v is None else v for k, v in values.items()}
        num_regression.check(values)

    def test_reduce_interval_with_non_existing_reducer_and_properties(self, jaxa_rainfall):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        with pytest.raises(AttributeError):
            ic.geetools.reduceInterval("toto")

    def test_reduce_interval_with_empty_days(self, s2_sr):
        ic = s2_sr.filterDate("2021-01-01", "2021-01-07")
        resultSize = ic.geetools.reduceInterval("mean", duration=1, unit="day").size().getInfo()
        assert resultSize == 3

    def test_reduce_interval_image_collection_with_system_id(self, s2_sr):
        originalIc = s2_sr.filterDate("2021-01-01", "2021-01-07")
        ic = originalIc.geetools.reduceInterval("mean", duration=1, unit="day")
        assert "system:id" in ic.propertyNames().getInfo()

    def test_reduce_interval_image_with_system_id(self, s2_sr):
        originalIc = s2_sr.filterDate("2021-01-01", "2021-01-07")
        ic = originalIc.geetools.reduceInterval("mean", duration=1, unit="day")
        firstImg = ic.first()
        assert "system:id" in firstImg.propertyNames().getInfo()

    def test_deprecated_reduce_equal_interval(self, jaxa_rainfall, amazonas, num_regression):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-31")
        with pytest.deprecated_call():
            reduced = geetools.imagecollection.reduceEqualInterval(ic, reducer="mean")
            values = reduce(reduced, amazonas).getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)

    def test_deprecated_reduce_day_intervals(self, jaxa_rainfall, amazonas, num_regression):
        # get 3 days worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-01-04")
        with pytest.deprecated_call():
            reduced = geetools.imagecollection.reduceDayIntervals(ic, reducer="mean")
            values = reduce(reduced, amazonas).getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)

    def test_deprecated_composite_regular_intervals(self, jaxa_rainfall, amazonas, num_regression):
        # get 3 days worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-01-04")
        with pytest.deprecated_call():
            reduced = geetools.composite.compositeRegularIntervals(ic, unit="day")
            values = reduce(reduced, amazonas).getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)

    def test_deprecated_composite_by_month(self, jaxa_rainfall, amazonas, num_regression):
        # get 3 month worth of data and group it with default parameters
        ic = jaxa_rainfall.filterDate("2020-01-01", "2020-03-01")
        with pytest.deprecated_call():
            reduced = geetools.composite.compositeByMonth(ic)
            values = reduce(reduced, amazonas).getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)


class TestClosestDate:
    """Test the ``closestDate`` method."""

    def test_closest_date(self, s2_sr, amazonas, num_regression):
        # we need less images as the test will fail otherwise
        filled = s2_sr.filterDate("2021-01-01", "2021-01-15").geetools.closestDate()
        values = reduce(filled, amazonas, "mean").getInfo()
        values = {k: np.nan if v is None else v for k, v in values.items()}
        num_regression.check(values)

    def test_deprecated_fill_with_last(self, s2_sr, amazonas, num_regression):
        with pytest.deprecated_call():
            filled = geetools.imagecollection.fillWithLast(
                s2_sr.filterDate("2021-01-01", "2021-01-15")
            )
            values = reduce(filled, amazonas, "mean").getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)

    def test_deprecated_closest_date(self, s2_sr, amazonas, num_regression):
        with pytest.deprecated_call():
            filled = geetools.composite.closestDate(s2_sr.filterDate("2021-01-01", "2021-01-15"))
            values = reduce(filled, amazonas, "mean").getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)


class TestMedoid:
    """Test the ``medoid`` method."""

    def test_medoid(self, s2_sr, amazonas, num_regression):
        # we need less images as the test will fail otherwise
        medoid = s2_sr.filterDate("2021-01-01", "2021-01-05").geetools.medoid()
        values = reduce(ee.ImageCollection(medoid), amazonas).getInfo()
        values = {k: np.nan if v is None else v for k, v in values.items()}
        num_regression.check(values)

    def test_deprecated_medoid(self, s2_sr, amazonas, num_regression):
        with pytest.deprecated_call():
            # we need less images as the test will fail otherwise
            medoid = geetools.composite.medoid(s2_sr.filterDate("2021-01-01", "2021-01-05"))
            values = reduce(ee.ImageCollection(medoid), amazonas).getInfo()
            values = {k: np.nan if v is None else v for k, v in values.items()}
            num_regression.check(values)


class TestPlotDatesByBands:
    """Test the ``plot_dates_by_bands`` method."""

    def test_plot_dates_by_bands(self, image_regression):
        fig, ax = plt.subplots()
        self.collection.geetools.plot_dates_by_bands(
            region=self.region.geometry(),
            reducer="mean",
            scale=500,
            bands=["NDVI", "EVI"],
            ax=ax,
            dateProperty="system:time_start",
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def region(self):
        return (
            ee.FeatureCollection("projects/google/charts_feature_example")
            .select(["label", "value", "warm"])
            .filter(ee.Filter.eq("label", "Forest"))
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .filter(ee.Filter.date("2010-01-01", "2020-01-01"))
            .select(["NDVI", "EVI"])
        )


class TestPlotDatesByRegions:
    """Test the ``plot_dates_by_regions`` method."""

    def test_plot_dates_by_regions(self, image_regression):
        fig, ax = plt.subplots()
        self.collection.geetools.plot_dates_by_regions(
            regions=self.regions,
            label="label",
            band="NDVI",
            reducer="mean",
            scale=500,
            ax=ax,
            dateProperty="system:time_start",
            colors=["#f0af07", "#0f8755", "#76b349"],
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def regions(self):
        return ee.FeatureCollection("projects/google/charts_feature_example").select(
            ["label", "value", "warm"]
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .filter(ee.Filter.date("2010-01-01", "2020-01-01"))
            .select(["NDVI", "EVI"])
        )


class TestPlotDoyByBands:
    """Test the ``plot_doy_by_bands`` method."""

    def test_plot_doy_by_bands(self, image_regression):
        fig, ax = plt.subplots()
        self.collection.geetools.plot_doy_by_bands(
            region=self.region.geometry(),
            spatialReducer="mean",
            timeReducer="mean",
            scale=500,
            bands=["NDVI", "EVI"],
            ax=ax,
            dateProperty="system:time_start",
            colors=["#e37d05", "#1d6b99"],
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def region(self):
        return (
            ee.FeatureCollection("projects/google/charts_feature_example")
            .select(["label", "value", "warm"])
            .filter(ee.Filter.eq("label", "Grassland"))
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .filter(ee.Filter.date("2010-01-01", "2020-01-01"))
            .select(["NDVI", "EVI"])
        )


class TestPlotDoyByRegions:
    """Test the ``plot_doy_by_regions`` method."""

    def test_plot_doy_by_regions(self, image_regression):
        fig, ax = plt.subplots()
        self.collection.geetools.plot_doy_by_regions(
            regions=self.regions,
            label="label",
            band="NDVI",
            spatialReducer="mean",
            timeReducer="mean",
            scale=500,
            ax=ax,
            dateProperty="system:time_start",
            colors=["#f0af07", "#0f8755", "#76b349"],
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def regions(self):
        return ee.FeatureCollection("projects/google/charts_feature_example").select(
            ["label", "value", "warm"]
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .filter(ee.Filter.date("2010-01-01", "2020-01-01"))
            .select(["NDVI", "EVI"])
        )


class TestPlotDoyByYears:
    """Test the ``plot_doy_by_years`` method."""

    def test_plot_doy_by_years(self, image_regression):
        fig, ax = plt.subplots()
        self.collection.geetools.plot_doy_by_years(
            region=self.region.geometry(),
            band="NDVI",
            reducer="mean",
            scale=500,
            ax=ax,
            colors=["#39a8a7", "#9c4f97"],
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def region(self):
        return (
            ee.FeatureCollection("projects/google/charts_feature_example")
            .select(["label", "value", "warm"])
            .filter(ee.Filter.eq("label", "Grassland"))
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .select(["NDVI", "EVI"])
            .filter(
                ee.Filter.Or(
                    ee.Filter.date("2012-01-01", "2012-12-31"),
                    ee.Filter.date("2019-01-01", "2019-12-31"),
                )
            )
        )


class TestPlotDoyBySeasons:
    """Test the ``plot_doy_by_seasons`` method."""

    def test_plot_doy_by_seasons(self, image_regression):
        fig, ax = plt.subplots()
        self.collection.geetools.plot_doy_by_seasons(
            region=self.region.geometry(),
            seasonStart=ee.Date("2019-04-15").getRelative("day", "year"),
            seasonEnd=ee.Date("2019-09-15").getRelative("day", "year"),
            band="NDVI",
            reducer="mean",
            scale=500,
            ax=ax,
            colors=["#39a8a7", "#9c4f97"],
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def region(self):
        return (
            ee.FeatureCollection("projects/google/charts_feature_example")
            .select(["label", "value", "warm"])
            .filter(ee.Filter.eq("label", "Grassland"))
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .select(["NDVI", "EVI"])
            .filter(
                ee.Filter.Or(
                    ee.Filter.date("2012-01-01", "2012-12-31"),
                    ee.Filter.date("2019-01-01", "2019-12-31"),
                )
            )
        )


class TestReduceRegion:
    """Test the reduceRegion method."""

    def test_reduce_region_by_dates(self, data_regression):
        values = self.collection.geetools.reduceRegion(
            reducer=ee.Reducer.mean(),
            idProperty="system:time_start",
            idType=ee.Date,
            geometry=self.region.geometry(),
            scale=500,
        ).getInfo()
        data_regression.check(round_dict(values, 4))

    def test_reduce_region_by_date_property(self, data_regression):
        values = self.collection.geetools.reduceRegion(
            reducer=ee.Reducer.mean(),
            idProperty="system:time_start",
            idType=ee.Date,
            idReducer="mean",
            geometry=self.region.geometry(),
            scale=500,
        ).getInfo()
        data_regression.check(round_dict(values, 4))

    def test_reduce_region_by_doy(self, data_regression):
        values = self.year_collection.geetools.reduceRegion(
            reducer=ee.Reducer.mean(),
            idProperty="system:time_start",
            idType=ee.Date,
            idFormat="DDD",
            geometry=self.region.geometry(),
            scale=500,
        ).getInfo()
        data_regression.check(round_dict(values, 4))

    @property
    def region(self):
        return (
            ee.FeatureCollection("projects/google/charts_feature_example")
            .select(["label", "value", "warm"])
            .filter(ee.Filter.eq("label", "Forest"))
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .filter(ee.Filter.date("2010-01-01", "2010-02-28"))
            .select(["NDVI", "EVI"])
        )

    @property
    def year_collection(self):
        return (
            ee.ImageCollection("MODIS/006/MOD13Q1")
            .filter(
                ee.Filter.Or(
                    ee.Filter.date("2010-01-01", "2010-02-28"),
                    ee.Filter.date("2011-01-01", "2011-02-28"),
                )
            )
            .select(["NDVI", "EVI"])
        )


class TestReduceRegions:
    """Test the ``reduceRegion`` method."""

    def test_reduce_regions_by_dates(self, ee_dictionary_regression):
        values = self.collection.geetools.reduceRegions(
            reducer=ee.Reducer.mean(),
            idProperty="system:time_start",
            idType=ee.Date,
            collection=self.region,
            scale=500,
        )
        values = values.geetools.toDictionary()
        ee_dictionary_regression.check(values)

    def test_reduce_regions_by_date_property(self, ee_dictionary_regression):
        values = self.collection.geetools.reduceRegions(
            reducer=ee.Reducer.mean(),
            idProperty="system:time_start",
            idType=ee.Date,
            idReducer="mean",
            collection=self.region,
            scale=500,
        )
        values = values.geetools.toDictionary()
        ee_dictionary_regression.check(values)

    def test_reduce_regions_by_doy(self, ee_dictionary_regression):
        values = self.year_collection.geetools.reduceRegions(
            reducer=ee.Reducer.mean(),
            idProperty="system:time_start",
            idType=ee.Date,
            idFormat="DDD",
            collection=self.region,
            scale=500,
        )
        values = values.geetools.toDictionary()
        ee_dictionary_regression.check(values)

    @property
    def region(self):
        return ee.FeatureCollection("projects/google/charts_feature_example").select(
            ["label", "value", "warm"]
        )

    @property
    def collection(self):
        return (
            ee.ImageCollection("MODIS/061/MOD13A1")
            .filter(ee.Filter.date("2010-01-01", "2010-02-28"))
            .select(["NDVI", "EVI"])
        )

    @property
    def year_collection(self):
        return (
            ee.ImageCollection("MODIS/006/MOD13Q1")
            .filter(
                ee.Filter.Or(
                    ee.Filter.date("2010-01-01", "2010-02-28"),
                    ee.Filter.date("2011-01-01", "2011-02-28"),
                )
            )
            .select(["NDVI", "EVI"])
        )
