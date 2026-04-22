from __future__ import annotations

from typing import Any

from dash import MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class DatePicker(DataBoundComponent):
    """Single-date picker bound to a STRING source (ISO date)."""

    ACCEPTED_TYPES = frozenset({DataType.STRING})

    def __init__(self, source: Any, aio_id: str | None = None, container_props: dict[str, Any] | None = None) -> None:
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _dp_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "DatePicker", "sub": "dp", "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        return [
            dcc.DatePickerSingle(
                id=self._dp_id(self.source.source_id, self.aio_id),
                date=self.source.initial() or None,
                persistence=True,
            )
        ]

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "DatePicker", "sub": "dp", "source_id": MATCH, "aio_id": MATCH}, "date"),
        prevent_initial_call=True,
    )
    def _write(date: Any) -> Any:
        from .._writable import mirror_to_backing

        mirror_to_backing(date)
        return date
