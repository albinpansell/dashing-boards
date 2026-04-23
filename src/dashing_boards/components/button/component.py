from __future__ import annotations

import uuid
from typing import Any

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, callback, html


class Button(html.Div):
    """Simple button. Optionally bind click count to a NUMBER DataSource.

    The DataSource approach for buttons is usually not needed — direct
    `Input(button.id, "n_clicks")` callbacks work fine. The `source`
    kwarg is provided for consistency; when set, the click count is
    written into the source's Store.
    """

    def __init__(
        self,
        label: str,
        source: Any = None,
        color: str = "primary",
        size: str = "sm",
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        self.aio_id = aio_id or f"aio-{uuid.uuid4().hex[:8]}"
        self.source = source
        btn_id = (
            self._btn_id(self.aio_id)
            if source is None
            else {
                "component": "Button",
                "sub": "btn",
                "source_id": source.source_id,
                "aio_id": self.aio_id,
            }
        )
        self.id_dict = btn_id
        children = [dbc.Button(label, id=btn_id, color=color, size=size)]
        props = dict(container_props or {})
        super().__init__(children=children, **props)

    @staticmethod
    def _btn_id(aio_id: str) -> dict[str, str]:
        return {"component": "Button", "sub": "btn", "aio_id": aio_id, "source_id": "__none__"}

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "Button", "sub": "btn", "source_id": MATCH, "aio_id": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _write_clicks(_clicks: list[int | None]) -> int:
        from .._writable import triggered_value

        return int(triggered_value() or 0)
