"""Test the ``FeatureCollection`` class."""
import io

import ee
import geopandas as gpd
import pytest
from matplotlib import pyplot as plt

import geetools  # noqa: F401


class TestToImage:
    """Test the ``toImage`` method."""

    def test_to_image(self, fc_instance, vatican):
        image = fc_instance.geetools.toImage()
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"constant": 0}

    def test_to_image_with_color(self, fc_instance, vatican):
        image = fc_instance.geetools.toImage(color="ADM0_CODE")
        values = image.reduceRegion(ee.Reducer.mean(), vatican, 1)
        assert values.getInfo() == {"constant": 110}

    @pytest.fixture
    def fc_instance(self):
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level0")
        return gaul.filter(ee.Filter.eq("ADM0_CODE", 110))

    @pytest.fixture
    def vatican(self):
        """Return a buffer around the Vatican City."""
        return ee.Geometry.Point([12.453386, 41.903282]).buffer(1)


class TestToDictionary:
    """Test the ``toDictionary`` method."""

    def test_to_dictionary(self, data_regression):
        output = self.table.geetools.toDictionary("ADM0_NAME", ["ADM0_CODE", "Shape_Area"])
        data_regression.check(output.getInfo())

    @property
    def table(self):
        return ee.FeatureCollection("FAO/GAUL/2015/level0").filter(
            ee.Filter.stringStartsWith(leftField="ADM0_NAME", rightValue="Ar")
        )


class TestAddId:
    """Test the ``addId`` method."""

    def test_add_id(self, fc_instance):
        fc = fc_instance.geetools.addId()
        assert fc.first().get("id").getInfo() == 1

    @pytest.fixture
    def fc_instance(self):
        return ee.FeatureCollection("FAO/GAUL/2015/level0").limit(10)


class TestMergeGeometries:
    """Test the ``mergeGeometries`` method."""

    def test_merge_geometries(self, gaul_3_countries, data_regression):
        geom = gaul_3_countries.geetools.mergeGeometries()
        data_regression.check(geom.getInfo())


class TestToPolygons:
    """Test the ``toPolygons`` method."""

    def test_to_polygons(self, fc_instance, dataframe_regression):
        fc = fc_instance.geetools.toPolygons()
        gdf = gpd.GeoDataFrame.from_features(fc.getInfo())
        vertex = gdf.geometry.apply(lambda g: sum(len(p.exterior.coords) for p in g.geoms))
        assert vertex.sum() == 66


class TestByProperties:
    """Test the ``byProperties`` method."""

    def test_by_properties(self, ecoregions, data_regression):
        fc = ecoregions.geetools.byProperties()
        data_regression.check(fc.getInfo())

    def test_by_properties_with_id(self, ecoregions, data_regression):
        fc = ecoregions.geetools.byProperties("label")
        data_regression.check(fc.getInfo())

    def test_by_properties_with_properties(self, ecoregions, data_regression):
        fc = ecoregions.geetools.byProperties("label", properties=["01_tmean", "02_tmean"])
        data_regression.check(fc.getInfo())


class TestByFeatures:
    """Test the ``byFeatures`` method."""

    def test_by_features(self, ecoregions, data_regression):
        fc = ecoregions.geetools.byFeatures()
        data_regression.check(fc.getInfo())

    def test_by_features_with_id(self, ecoregions, data_regression):
        fc = ecoregions.geetools.byFeatures("label")
        data_regression.check(fc.getInfo())

    def test_by_features_with_properties(self, ecoregions, data_regression):
        fc = ecoregions.geetools.byFeatures("label", properties=["01_tmean", "02_tmean"])
        data_regression.check(fc.getInfo())


class TestPlotByFeatures:
    """Test the ``plot_by_features`` method."""

    def test_plot_by_features_bar(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregions.geetools.plot_by_features(
            type="bar",
            featureId="label",
            properties=["01_tmean", "02_tmean", "03_tmean", "04_tmean", "05_tmean", "06_tmean", "07_tmean", "08_tmean", "09_tmean", "10_tmean","11_tmean", "12_tmean"],
            labels=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors=["#604791", "#1d6b99", "#39a8a7", "#0f8755", "#76b349", "#f0af07", "#e37d05", "#cf513e", "#96356f", "#724173", "#9c4f97", "#696969"],
            ax=ax,
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_features_stacked(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregions.geetools.plot_by_features(
            type="stacked",
            featureId="label",
            properties=["01_tmean", "02_tmean", "03_tmean", "04_tmean", "05_tmean", "06_tmean", "07_tmean", "08_tmean", "09_tmean", "10_tmean","11_tmean", "12_tmean"],
            labels=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            colors=["#604791", "#1d6b99", "#39a8a7", "#0f8755", "#76b349", "#f0af07", "#e37d05", "#cf513e", "#96356f", "#724173", "#9c4f97", "#696969"],
            ax=ax,
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_features_scatter(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        ecoregions.geetools.plot_by_features(
            type="scatter",
            featureId="label",
            properties=["01_ppt", "06_ppt", "09_ppt"],
            labels=["jan", "jun", "sep"],
            ax=ax,
        )
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_features_pie(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        ecoregions.geetools.plot_by_features(
            type="pie",
            featureId="label",
            properties=["06_ppt"],
            colors=["#f0af07", "#0f8755", "#76b349"],
            ax=ax,
        )
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_features_donut(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        ecoregions.geetools.plot_by_features(
            type="donut",
            featureId="label",
            properties=["06_ppt"],
            colors=["#f0af07", "#0f8755", "#76b349"],
            ax=ax,
        )
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())


class TestPlotByPropperties:
    """Test the ``plot_by_properties`` method."""

    def test_plot_by_properties_bar(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregions.geetools.plot_by_properties(
            type="bar",
            properties=["01_ppt", "02_ppt", "03_ppt", "04_ppt", "05_ppt", "06_ppt", "07_ppt", "08_ppt", "09_ppt", "10_ppt", "11_ppt", "12_ppt"],
            labels=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            featureId="label",
            colors=["#f0af07", "#0f8755", "#76b349"],
            ax=ax,
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_properties_plot(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregions.geetools.plot_by_properties(
            type="plot",
            properties=["01_ppt", "02_ppt", "03_ppt", "04_ppt", "05_ppt", "06_ppt", "07_ppt", "08_ppt", "09_ppt", "10_ppt", "11_ppt", "12_ppt"],
            labels=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            featureId="label",
            colors=["#f0af07", "#0f8755", "#76b349"],
            ax=ax,
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_by_properties_area(self, ecoregions, image_regression):
        fig, ax = plt.subplots()
        # fmt: off
        ecoregions.geetools.plot_by_properties(
            type="fill_between",
            properties=["01_ppt", "02_ppt", "03_ppt", "04_ppt", "05_ppt", "06_ppt", "07_ppt", "08_ppt", "09_ppt", "10_ppt", "11_ppt", "12_ppt"],
            labels=["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
            featureId="label",
            colors=["#f0af07", "#0f8755", "#76b349"],
            ax=ax,
        )
        # fmt: on
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())


class TestPlotHist:
    """Test the ``plot_hist`` method."""

    def test_plot_hist(self, climSamp, image_regression):
        fig, ax = plt.subplots()
        climSamp.geetools.plot_hist(
            property="07_ppt", label="July Precipitation (mm)", color="#1d6b99", ax=ax, bins=30
        )
        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())


class TestPlot:
    """Test the ``plot`` method."""

    def test_plot(self, image_regression):
        fig, ax = plt.subplots()
        self.hydroshed.select(["UP_AREA"]).geetools.plot(ax=ax)

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_with_property(self, image_regression):
        fig, ax = plt.subplots()
        self.hydroshed.geetools.plot(ax=ax, property="UP_AREA")

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_with_cmap(self, image_regression):
        fig, ax = plt.subplots()
        self.hydroshed.geetools.plot(ax=ax, property="UP_AREA", cmap="magma")

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    def test_plot_with_boundaries(self, image_regression):
        fig, ax = plt.subplots()
        self.hydroshed.geetools.plot(
            ax=ax, property="UP_AREA", cmap="magma", boundaries=True, color="g"
        )

        with io.BytesIO() as buffer:
            fig.savefig(buffer)
            image_regression.check(buffer.getvalue())

    @property
    def hydroshed(self):
        """The level 4 hydroshed of South america."""
        dataset = "WWF/HydroATLAS/v1/Basins/level04"
        region = ee.Geometry.BBox(-80, -60, -20, 20)
        return ee.FeatureCollection(dataset).filterBounds(region)


class TestFromGeoInterface:
    """Test the ``fromGeoInterface`` method."""

    def test_from_geo_interface(self, gdf, data_regression):
        fc = ee.FeatureCollection.geetools.fromGeoInterface(gdf)
        data_regression.check(fc.getInfo())

    def test_from_geo_interface_from_dict(self, gdf, data_regression):
        fc = ee.FeatureCollection.geetools.fromGeoInterface(gdf.__geo_interface__)
        data_regression.check(fc.getInfo())

    def test_error_from_geo_interface_(self):
        with pytest.raises(ValueError):
            ee.FeatureCollection.geetools.fromGeoInterface("toto")

    @pytest.fixture
    def gdf(self):
        data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Coors Field"},
                    "geometry": {"type": "Point", "coordinates": [-104.99404, 39.75621]},
                }
            ],
        }
        return gpd.GeoDataFrame.from_features(data["features"])
