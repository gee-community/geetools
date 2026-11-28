"""Unit tests for Asset.delete() recursive ordering and parallel execution."""
from __future__ import annotations

from unittest.mock import patch

import ee

import geetools  # noqa: F401


def test_delete_recursive_deletes_children_before_parents():
    root = ee.Asset("projects/p/assets/root")
    child_a = ee.Asset("projects/p/assets/root/a")
    child_b = ee.Asset("projects/p/assets/root/b")
    grandchild = ee.Asset("projects/p/assets/root/a/leaf")

    deleted_order: list[str] = []

    with (
        patch.object(ee.Asset, "is_folder", return_value=True),
        patch.object(ee.Asset, "is_image_collection", return_value=False),
        patch.object(ee.Asset, "iterdir", return_value=[child_a, grandchild, child_b]),
        patch.object(ee.data, "deleteAsset", side_effect=deleted_order.append),
    ):
        result = root.delete(recursive=True, dry_run=False, max_workers=2)

    assert result == [
        "projects/p/assets/root/a/leaf",
        "projects/p/assets/root/a",
        "projects/p/assets/root/b",
        "projects/p/assets/root",
    ]
    # Deepest level deleted first, root deleted last
    assert deleted_order[0] == "projects/p/assets/root/a/leaf"
    assert set(deleted_order[1:3]) == {"projects/p/assets/root/a", "projects/p/assets/root/b"}
    assert deleted_order[-1] == "projects/p/assets/root"


def test_delete_recursive_dry_run_does_not_call_api():
    root = ee.Asset("projects/p/assets/root")
    child = ee.Asset("projects/p/assets/root/a")

    with (
        patch.object(ee.Asset, "is_folder", return_value=True),
        patch.object(ee.Asset, "is_image_collection", return_value=False),
        patch.object(ee.Asset, "iterdir", return_value=[child]),
        patch.object(ee.data, "deleteAsset") as mock_delete,
    ):
        result = root.delete(recursive=True)

    assert result == ["projects/p/assets/root/a", "projects/p/assets/root"]
    mock_delete.assert_not_called()
