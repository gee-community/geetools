"""Test the ``Export`` class."""
import ee
import pytest
from ee.cli.utils import wait_for_task

import geetools  # noqa F401


class TestImageCollection:
    """Test the ``imagecollection`` namespace."""

    @pytest.mark.skip(reason="The export task timeout when to many tests are run at the same time")
    def test_toAsset(self, gee_test_folder):
        task_list = ee.batch.Export.geetools.imagecollection.toAsset(
            imagecollection=self.ic,
            description="ic_to_asset",
            index_property="index",
            assetId=(gee_test_folder / "ic_to_asset").as_posix(),
            region=ee.Geometry.Point([0, 0]).buffer(100).bounds(),
            scale=50,
        )
        [task.start() for task in task_list]
        [wait_for_task(task.id, timeout=50) for task in task_list]

        ic = ee.ImageCollection((gee_test_folder / "ic_to_asset").as_posix())
        assert ic.size().getInfo() == 2

    @property
    def ic(self):
        """Return a test image collection."""
        image_list = [ee.Image(i).set("index", f"image_{i}") for i in range(2)]
        return ee.ImageCollection(image_list)
