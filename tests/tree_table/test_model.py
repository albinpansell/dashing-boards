from __future__ import annotations

import pytest

from dashing_boards.tree_table import AggregationType, TreeTableModel


def sample_rows() -> list[dict[str, object]]:
    return [
        {"id": "r1", "parent_id": None, "name": "Root", "cost": 0},
        {"id": "c1", "parent_id": "r1", "name": "Child 1", "cost": 10},
        {"id": "c2", "parent_id": "r1", "name": "Child 2", "cost": 20},
        {"id": "g1", "parent_id": "c1", "name": "Grandchild", "cost": 5},
    ]


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        TreeTableModel(rows=[{"id": "x", "name": "X"}])


def test_duplicate_ids_raise() -> None:
    with pytest.raises(ValueError, match="Duplicate ids"):
        TreeTableModel(
            rows=[
                {"id": "x", "parent_id": None, "name": "A"},
                {"id": "x", "parent_id": None, "name": "B"},
            ]
        )


def test_required_field_aggregation_raises_on_init() -> None:
    with pytest.raises(ValueError, match="Cannot set aggregation on required field"):
        TreeTableModel(rows=sample_rows(), aggregation_map={"name": AggregationType.SUM})


def test_visibility_respects_collapsed_nodes() -> None:
    model = TreeTableModel(rows=sample_rows())
    all_visible = model.visible_items()
    assert [item["id"] for item in all_visible] == ["r1", "c1", "g1", "c2"]

    collapsed_visible = model.visible_items({"c1"})
    assert [item["id"] for item in collapsed_visible] == ["r1", "c1", "c2"]


def test_sum_aggregation_propagates_up() -> None:
    model = TreeTableModel(rows=sample_rows(), aggregation_map={"cost": AggregationType.SUM})
    assert model.get_item("c1")["cost"] == 5
    assert model.get_item("r1")["cost"] == 25


def test_equal_aggregation_propagates_down_on_update() -> None:
    model = TreeTableModel(
        rows=[
            {"id": "r", "parent_id": None, "name": "Root", "status": "open"},
            {"id": "c", "parent_id": "r", "name": "Child", "status": "open"},
        ],
        aggregation_map={"status": AggregationType.EQUAL},
    )
    model.update_field("r", "status", "done")
    assert model.get_item("c")["status"] == "done"
