from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, callback, callback_context, html
from dash.exceptions import PreventUpdate

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class KanbanBoard(DataBoundComponent):
    """Python-only Kanban MVP.

    Each card has ◀/▶ buttons to move between columns — no native
    drag-and-drop yet (would require a React component wrapping
    dnd-kit; planned follow-up).

    Source: DATAFRAME of rows, each with at minimum:
      - `id`   (unique identifier)
      - `status` (or the column configured via `column_key`)
      - `title` (or the column configured via `title_key`)

    Column set is either `columns=["todo", "doing", "done"]` or
    auto-detected from the data when `columns=None`.
    """

    ACCEPTED_TYPES = frozenset({DataType.DATAFRAME})

    def __init__(
        self,
        source: Any,
        columns: list[str] | None = None,
        column_key: str = "status",
        title_key: str = "title",
        id_key: str = "id",
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        self._columns = columns
        self._column_key = column_key
        self._title_key = title_key
        self._id_key = id_key
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _root_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "KanbanBoard", "sub": "root", "source_id": source_id, "aio_id": aio_id}

    @staticmethod
    def _config_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "KanbanBoard", "sub": "config", "source_id": source_id, "aio_id": aio_id}

    @staticmethod
    def _move_id(source_id: str, aio_id: str, card_id: str, direction: str) -> dict[str, str]:
        return {
            "component": "KanbanBoard",
            "sub": "move",
            "source_id": source_id,
            "aio_id": aio_id,
            "card_id": card_id,
            "direction": direction,
        }

    def _build(self) -> list[Any]:
        from dash import dcc

        rows = self.source.initial() or []
        columns = self._resolve_columns(rows)
        config = {
            "columns": columns,
            "column_key": self._column_key,
            "title_key": self._title_key,
            "id_key": self._id_key,
        }
        return [
            dcc.Store(id=self._config_id(self.source.source_id, self.aio_id), data=config),
            html.Div(
                id=self._root_id(self.source.source_id, self.aio_id),
                children=_render_board(
                    rows,
                    columns,
                    self._column_key,
                    self._title_key,
                    self._id_key,
                    self.source.source_id,
                    self.aio_id,
                ),
                style={"display": "grid", "gridTemplateColumns": f"repeat({len(columns) or 1}, 1fr)", "gap": "12px"},
            ),
        ]

    def _resolve_columns(self, rows: list[dict[str, Any]]) -> list[str]:
        if self._columns:
            return self._columns
        seen: list[str] = []
        for r in rows:
            s = str(r.get(self._column_key, ""))
            if s and s not in seen:
                seen.append(s)
        return seen

    @callback(
        Output({"component": "KanbanBoard", "sub": "root", "source_id": MATCH, "aio_id": MATCH}, "children"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        State({"component": "KanbanBoard", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
        State({"component": "KanbanBoard", "sub": "root", "source_id": MATCH, "aio_id": MATCH}, "id"),
    )
    def _render(data: Any, config: dict[str, Any], root_id: dict[str, str]) -> list[Any]:
        config = config or {}
        columns = config.get("columns") or []
        return _render_board(
            data or [],
            columns,
            config.get("column_key", "status"),
            config.get("title_key", "title"),
            config.get("id_key", "id"),
            root_id["source_id"],
            root_id["aio_id"],
        )

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input(
            {
                "component": "KanbanBoard",
                "sub": "move",
                "source_id": MATCH,
                "aio_id": MATCH,
                "card_id": ALL,
                "direction": ALL,
            },
            "n_clicks",
        ),
        State({"component": "DataSource", "source_id": MATCH}, "data"),
        State({"component": "KanbanBoard", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
        prevent_initial_call=True,
    )
    def _move(_clicks: list[int | None], rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
        trigger = callback_context.triggered_id
        if not isinstance(trigger, dict):
            raise PreventUpdate
        clicks = callback_context.triggered[0]["value"] if callback_context.triggered else None
        if not clicks:
            raise PreventUpdate
        config = config or {}
        columns = config.get("columns") or []
        col_key = config.get("column_key", "status")
        id_key = config.get("id_key", "id")
        card_id = trigger.get("card_id")
        direction = trigger.get("direction")
        if not columns or card_id is None:
            raise PreventUpdate

        updated = [dict(r) for r in (rows or [])]
        for r in updated:
            if str(r.get(id_key)) != str(card_id):
                continue
            current = str(r.get(col_key, columns[0]))
            try:
                idx = columns.index(current)
            except ValueError:
                idx = 0
            new_idx = max(0, min(len(columns) - 1, idx + (1 if direction == "right" else -1)))
            r[col_key] = columns[new_idx]
            break

        from .._writable import mirror_to_backing

        mirror_to_backing(updated)
        return updated


def _render_board(
    rows: list[dict[str, Any]],
    columns: list[str],
    column_key: str,
    title_key: str,
    id_key: str,
    source_id: str,
    aio_id: str,
) -> list[Any]:
    result: list[Any] = []
    for col in columns:
        col_rows = [r for r in rows if str(r.get(column_key, "")) == col]
        cards: list[Any] = []
        for r in col_rows:
            card_id = str(r.get(id_key))
            cards.append(_render_card(r, card_id, title_key, source_id, aio_id))
        result.append(
            html.Div(
                [
                    html.Div(col, style={"fontWeight": 600, "marginBottom": "8px"}),
                    html.Div(cards, style={"display": "flex", "flexDirection": "column", "gap": "6px"}),
                ],
                style={"background": "#f5f5f5", "padding": "10px", "borderRadius": "6px", "minHeight": "80px"},
            )
        )
    return result


def _render_card(row: dict[str, Any], card_id: str, title_key: str, source_id: str, aio_id: str) -> Any:
    title = str(row.get(title_key, card_id))
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(title, style={"marginBottom": "6px"}),
                html.Div(
                    [
                        dbc.Button(
                            "◀",
                            id=KanbanBoard._move_id(source_id, aio_id, card_id, "left"),
                            size="sm",
                            color="light",
                            style={"marginRight": "4px"},
                        ),
                        dbc.Button(
                            "▶",
                            id=KanbanBoard._move_id(source_id, aio_id, card_id, "right"),
                            size="sm",
                            color="light",
                        ),
                    ],
                    style={"display": "flex", "justifyContent": "flex-end"},
                ),
            ]
        ),
        style={"padding": "0"},
    )
