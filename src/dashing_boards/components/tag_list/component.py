from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import MATCH, Input, Output, callback, html

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class TagList(DataBoundComponent):
    """Renders a list of strings as inline badges."""

    ACCEPTED_TYPES = frozenset({DataType.STRING_LIST})

    @staticmethod
    def _root_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {
            "component": "TagList",
            "sub": "root",
            "source_id": source_id,
            "aio_id": aio_id,
        }

    def _build(self) -> list[Any]:
        return [
            html.Div(
                id=self._root_id(self.source.source_id, self.aio_id),
                children=self._badges(self.source.initial()),
                style={"display": "flex", "flexWrap": "wrap", "gap": "4px"},
            )
        ]

    @staticmethod
    def _badges(values: Any) -> list[Any]:
        if not values:
            return []
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise TypeError(f"TagList requires list[str]; got {type(values).__name__}")
        return [dbc.Badge(v, color="secondary", className="me-1") for v in values]

    @callback(
        Output({"component": "TagList", "sub": "root", "source_id": MATCH, "aio_id": MATCH}, "children"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
    )
    def _render(data: Any) -> list[Any]:
        return TagList._badges(data)
