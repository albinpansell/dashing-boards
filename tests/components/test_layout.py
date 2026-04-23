from __future__ import annotations

from dash import html

from dashing_boards.components.layout.grid import _normalize


def test_grid_normalize_flat_uses_explicit_columns() -> None:
    cells, cols = _normalize([html.Div("a"), html.Div("b")], columns=2)
    assert len(cells) == 2
    assert cols == "repeat(2, 1fr)"


def test_grid_normalize_rows_computes_max_cols() -> None:
    cells, cols = _normalize([[html.Div("a"), html.Div("b")], [html.Div("c")]], columns=None)
    assert len(cells) == 4
    assert cols == "repeat(2, 1fr)"
