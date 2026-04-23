from __future__ import annotations

import pytest

from dashing_boards.components.diagram.component import _apply_filter, _to_dataframe

pd = pytest.importorskip("pandas")


def test_to_dataframe_from_records() -> None:
    df = _to_dataframe([{"a": 1}, {"a": 2}])
    assert list(df["a"]) == [1, 2]


def test_to_dataframe_from_table_2d() -> None:
    df = _to_dataframe([["a", "b"], [1, 2], [3, 4]])
    assert list(df.columns) == ["a", "b"]
    assert list(df["a"]) == [1, 3]


def test_apply_filter_dict() -> None:
    df = pd.DataFrame([{"type": "A", "v": 1}, {"type": "B", "v": 2}])
    assert list(_apply_filter(df, {"type": "A"})["v"]) == [1]


def test_apply_filter_callable() -> None:
    df = pd.DataFrame([{"v": 1}, {"v": 2}, {"v": 3}])
    assert list(_apply_filter(df, lambda d: d[d["v"] > 1])["v"]) == [2, 3]


def test_apply_filter_query_string() -> None:
    df = pd.DataFrame([{"type": "A", "v": 1}, {"type": "B", "v": 2}])
    assert list(_apply_filter(df, "type == 'B'")["v"]) == [2]
