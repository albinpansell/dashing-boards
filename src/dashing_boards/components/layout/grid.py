from __future__ import annotations

from typing import Any, Sequence

from dash import html


class Grid(html.Div):
    """Pure layout: a CSS-grid container.

    Pass `children=[[cell, cell, ...], [cell, ...]]` for explicit row/col
    layout, or `children=[cell, cell, ...]` with `columns=N` for a flat
    list that auto-wraps.

    Parent-child data dependencies (children derived from a shared
    parent source) are out of scope; construct pre-filtered
    DataSources in Python and pass them in.
    """

    def __init__(
        self,
        children: Sequence[Any] | Sequence[Sequence[Any]],
        columns: int | None = None,
        gap: str = "12px",
        container_props: dict[str, Any] | None = None,
    ) -> None:
        cells, template_cols = _normalize(children, columns)
        style = {
            "display": "grid",
            "gridTemplateColumns": template_cols,
            "gap": gap,
        }
        props = dict(container_props or {})
        props.setdefault("style", {}).update(style)
        super().__init__(children=cells, **props)


def _normalize(
    children: Sequence[Any] | Sequence[Sequence[Any]],
    columns: int | None,
) -> tuple[list[Any], str]:
    if children and all(isinstance(row, (list, tuple)) for row in children):
        num_cols = max(len(row) for row in children) if children else 1
        flat: list[Any] = []
        for row in children:
            padded = list(row) + [html.Div()] * (num_cols - len(row))
            flat.extend(padded)
        return flat, f"repeat({num_cols}, 1fr)"
    cols = columns or len(children) or 1
    return list(children), f"repeat({cols}, 1fr)"
