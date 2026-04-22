from __future__ import annotations

from dashing_boards.components.table.component import _to_records


def test_to_records_from_list_of_dicts_is_passthrough() -> None:
    rows = [{"a": 1}, {"a": 2}]
    assert _to_records(rows, None) == rows


def test_to_records_from_table_2d() -> None:
    assert _to_records([["a", "b"], [1, 2], [3, 4]], None) == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]


def test_to_records_from_dict() -> None:
    assert _to_records({"a": 1}, None) == [{"a": 1}]


def test_to_records_from_none() -> None:
    assert _to_records(None, None) == []
