from __future__ import annotations

from typing import Any

from dash import (
    ALL,
    MATCH,
    Input,
    Output,
    State,
    callback,
    callback_context,
    clientside_callback,
    dash_table,
    html,
    no_update,
)
from dash.exceptions import PreventUpdate

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class Table(DataBoundComponent):
    """Flat 2D table over `dash_table.DataTable`.

    Accepts DATAFRAME (list[dict]), TABLE_2D (list[list]), or DICT (single row).
    Edits propagate back to the source's Store (and, if the source is a
    WritableDataSource, to its backing system).
    """

    ACCEPTED_TYPES = frozenset({DataType.DATAFRAME, DataType.TABLE_2D, DataType.DICT})

    def __init__(
        self,
        source: Any,
        editable: bool = False,
        columns: list[str] | None = None,
        page_size: int = 25,
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        self._editable = editable
        self._columns = columns
        self._page_size = page_size
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _table_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Table", "sub": "tbl", "source_id": source_id, "aio_id": aio_id}

    def _records(self) -> list[dict[str, Any]]:
        return _to_records(self.source.initial(), self.source.data_type)

    def _column_defs(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self._columns:
            names = self._columns
        else:
            names = list(records[0].keys()) if records else []
        return [{"name": n, "id": n, "editable": self._editable} for n in names]

    def _build(self) -> list[Any]:
        records = self._records()
        return [
            dash_table.DataTable(
                id=self._table_id(self.source.source_id, self.aio_id),
                data=records,
                columns=self._column_defs(records),
                editable=self._editable,
                page_size=self._page_size,
                sort_action="native",
                filter_action="native",
                persistence=True,
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "6px",
                    "fontFamily": "inherit",
                    "fontSize": "inherit",
                },
                style_header={"fontFamily": "inherit", "fontWeight": 600},
                style_data_conditional=[],
                css=[
                    {
                        "selector": ".dash-cell-value, .dash-cell-value input, td.focused input",
                        "rule": (
                            "padding: 0 !important; margin: 0 !important; border: 0 !important; "
                            "font: inherit !important; background: transparent !important; "
                            "text-align: left !important; box-sizing: border-box !important; "
                            "width: 100% !important; height: 100% !important;"
                        ),
                    },
                    {
                        "selector": "td.dash-cell",
                        "rule": "padding: 6px !important;",
                    },
                    {
                        "selector": "td.dash-cell.focused",
                        "rule": "padding: 6px !important; outline: 2px solid #0d6efd; outline-offset: -2px;",
                    },
                ],
            )
        ]

    _install_single_click_edit = clientside_callback(
        """
        function(_id) {
            if (window.__dbTableClickInstalled) {
                return window.dash_clientside.no_update;
            }
            window.__dbTableClickInstalled = true;
            document.addEventListener('click', function(e) {
                const td = e.target.closest('td.dash-cell');
                if (!td) return;
                const table = td.closest('.dash-spreadsheet');
                if (!table) return;
                if (td.querySelector('input')) return;
                setTimeout(function() {
                    td.dispatchEvent(new MouseEvent('dblclick', {bubbles: true, cancelable: true, view: window}));
                    setTimeout(function() {
                        const input = td.querySelector('input');
                        if (input) {
                            input.focus();
                            const len = (input.value || '').length;
                            try { input.setSelectionRange(len, len); } catch (_) {}
                        }
                    }, 0);
                }, 0);
            }, true);
            return window.dash_clientside.no_update;
        }
        """,
        Output({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "style_table"),
        Input({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "id"),
    )

    @callback(
        Output({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "data"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        State({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "data"),
    )
    def _render(data: Any, current: list[dict[str, Any]] | None) -> Any:
        new = _to_records(data, None)
        if new == (current or []):
            return no_update
        return new

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": ALL}, "data_timestamp"),
        State({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": ALL}, "data"),
        prevent_initial_call=True,
    )
    def _write(_ts: list[Any], data_list: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
        from .._writable import mirror_to_backing

        trigger = callback_context.triggered_id
        if not isinstance(trigger, dict):
            raise PreventUpdate
        inputs_list = callback_context.inputs_list[0]
        idx = next((i for i, inp in enumerate(inputs_list) if inp.get("id") == trigger), None)
        if idx is None:
            raise PreventUpdate
        data = data_list[idx]
        mirror_to_backing(data)
        return data


def _to_records(value: Any, data_type: DataType | None) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list) and value and isinstance(value[0], list):
        header, *rows = value
        return [dict(zip(header, row)) for row in rows]
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return list(value)
    return []
