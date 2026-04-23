from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, callback

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class Toggle(DataBoundComponent):
    """Boolean toggle bound to a BOOL source."""

    ACCEPTED_TYPES = frozenset({DataType.BOOL})

    def __init__(
        self, source: Any, label: str = "", aio_id: str | None = None, container_props: dict[str, Any] | None = None
    ) -> None:
        self._label = label
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _switch_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Toggle", "sub": "switch", "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        return [
            dbc.Switch(
                id=self._switch_id(self.source.source_id, self.aio_id),
                label=self._label,
                value=bool(self.source.initial()),
                persistence=True,
            )
        ]

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "Toggle", "sub": "switch", "source_id": MATCH, "aio_id": ALL}, "value"),
        prevent_initial_call=True,
    )
    def _write(_values: list[bool]) -> bool:
        from .._writable import mirror_to_backing, triggered_value

        value = triggered_value()
        mirror_to_backing(value)
        return bool(value)
