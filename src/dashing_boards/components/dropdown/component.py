from __future__ import annotations

from typing import Any

from dash import ALL, MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class Dropdown(DataBoundComponent):
    """Dropdown whose selected value is bound to a STRING source.

    `options` is a static list of option strings (or {label, value} dicts).
    For dynamic options, place a STRING_LIST source and pass it via
    `options_source` instead of `options`.
    """

    ACCEPTED_TYPES = frozenset({DataType.STRING})

    def __init__(
        self,
        source: Any,
        options: list[str] | list[dict[str, str]] | None = None,
        options_source: Any = None,
        placeholder: str = "Select...",
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        if options is None and options_source is None:
            raise ValueError("Dropdown requires either options or options_source")
        self._static_options = options
        self._options_source = options_source
        self._placeholder = placeholder
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _dd_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Dropdown", "sub": "dd", "source_id": source_id, "aio_id": aio_id}

    def _normalized_options(self) -> list[dict[str, str]]:
        raw = self._static_options
        if raw is None and self._options_source is not None:
            raw = self._options_source.initial() or []
        if raw is None:
            return []
        result: list[dict[str, str]] = []
        for opt in raw:
            if isinstance(opt, dict):
                result.append(
                    {"label": str(opt.get("label", opt.get("value", ""))), "value": str(opt.get("value", ""))}
                )
            else:
                result.append({"label": str(opt), "value": str(opt)})
        return result

    def _build(self) -> list[Any]:
        return [
            dcc.Dropdown(
                id=self._dd_id(self.source.source_id, self.aio_id),
                options=self._normalized_options(),
                value=self.source.initial(),
                placeholder=self._placeholder,
                persistence=True,
            )
        ]

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "Dropdown", "sub": "dd", "source_id": MATCH, "aio_id": ALL}, "value"),
        prevent_initial_call=True,
    )
    def _write(_values: list[Any]) -> Any:
        from .._writable import mirror_to_backing, triggered_value

        value = triggered_value()
        mirror_to_backing(value)
        return value
