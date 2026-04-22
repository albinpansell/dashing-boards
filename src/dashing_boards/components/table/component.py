from __future__ import annotations

from typing import Any

from dash import MATCH, Input, Output, State, callback, dash_table, html

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
                style_cell={"textAlign": "left", "padding": "6px"},
            )
        ]

    @callback(
        Output({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "data"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
    )
    def _render(data: Any) -> list[dict[str, Any]]:
        return _to_records(data, None)

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "data_timestamp"),
        State({"component": "Table", "sub": "tbl", "source_id": MATCH, "aio_id": MATCH}, "data"),
        prevent_initial_call=True,
    )
    def _write(_ts: Any, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        from .._writable import mirror_to_backing

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
