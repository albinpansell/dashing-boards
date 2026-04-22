from __future__ import annotations

from typing import Any

from dash import MATCH, Input, Output, callback, html

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class TextBox(DataBoundComponent):
    """Renders a scalar payload (string/number/bool) as plain text."""

    ACCEPTED_TYPES = frozenset({DataType.STRING, DataType.NUMBER, DataType.BOOL})

    @staticmethod
    def _text_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {
            "component": "TextBox",
            "sub": "text",
            "source_id": source_id,
            "aio_id": aio_id,
        }

    def _build(self) -> list[Any]:
        return [
            html.Span(
                id=self._text_id(self.source.source_id, self.aio_id),
                children=self._format(self.source.initial()),
            )
        ]

    @staticmethod
    def _format(value: Any) -> str:
        return "" if value is None else str(value)

    @callback(
        Output({"component": "TextBox", "sub": "text", "source_id": MATCH, "aio_id": MATCH}, "children"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
    )
    def _render(data: Any) -> str:
        return TextBox._format(data)
