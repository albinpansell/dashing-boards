from __future__ import annotations

from typing import Any

from dash import ALL, MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.source import WritableDataSource
from ...binding.types import DataType


class TextField(DataBoundComponent):
    """Editable text bound to a STRING/NUMBER source.

    Writes back to the source's Store on blur or Enter (debounce=True).
    If the underlying source is also a WritableDataSource, also persists.
    """

    ACCEPTED_TYPES = frozenset({DataType.STRING, DataType.NUMBER})

    def __init__(
        self,
        source: Any,
        multiline: bool = False,
        placeholder: str = "",
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        self._multiline = multiline
        self._placeholder = placeholder
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _input_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "TextField", "sub": "input", "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        initial = self.source.initial()
        value = "" if initial is None else str(initial)
        if self._multiline:
            return [
                dcc.Textarea(
                    id=self._input_id(self.source.source_id, self.aio_id),
                    value=value,
                    placeholder=self._placeholder,
                    style={"width": "100%", "minHeight": "80px"},
                    persistence=True,
                )
            ]
        return [
            dcc.Input(
                id=self._input_id(self.source.source_id, self.aio_id),
                value=value,
                placeholder=self._placeholder,
                type="text",
                debounce=True,
                persistence=True,
                style={"width": "100%"},
            )
        ]

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "TextField", "sub": "input", "source_id": MATCH, "aio_id": ALL}, "value"),
        prevent_initial_call=True,
    )
    def _write_back(_values: list[Any]) -> Any:
        from .._writable import mirror_to_backing, triggered_value

        value = triggered_value()
        mirror_to_backing(value)
        return value
