from __future__ import annotations

import json
from typing import Any

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, callback, callback_context, clientside_callback, dcc, html
from dash.exceptions import PreventUpdate

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class KanbanBoard(DataBoundComponent):
    """Kanban board with real drag-and-drop across columns.

    Drag-and-drop is implemented with SortableJS (loaded via
    `make_app`). Each column is a Sortable list; dragging a card
    between columns fires `onEnd`, which serialises the new
    column-to-cardIds mapping into a hidden dcc.Store, which a
    Python callback consumes to update the DataSource.

    Source: DATAFRAME of rows, each with at minimum:
      - `id`     (unique identifier)
      - `status` (or the column configured via `column_key`)
      - `title`  (or the column configured via `title_key`)

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
    def _snapshot_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "KanbanBoard", "sub": "snapshot", "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        rows = self.source.initial() or []
        columns = self._resolve_columns(rows)
        config = {
            "columns": columns,
            "column_key": self._column_key,
            "title_key": self._title_key,
            "id_key": self._id_key,
        }
        snapshot_id = self._snapshot_id(self.source.source_id, self.aio_id)
        return [
            dcc.Store(id=self._config_id(self.source.source_id, self.aio_id), data=config),
            dcc.Store(id=snapshot_id),
            html.Div(
                id=self._root_id(self.source.source_id, self.aio_id),
                className="dbd-kanban-board",
                **{"data-store-id": json.dumps(snapshot_id), "data-group": f"kanban-{self.source.source_id}-{self.aio_id}"},
                children=_render_board(
                    rows, columns, self._column_key, self._title_key, self._id_key
                ),
                style={
                    "display": "grid",
                    "gridTemplateColumns": f"repeat({len(columns) or 1}, 1fr)",
                    "gap": "12px",
                },
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
    )
    def _render(data: Any, config: dict[str, Any]) -> list[Any]:
        config = config or {}
        columns = config.get("columns") or []
        return _render_board(
            data or [],
            columns,
            config.get("column_key", "status"),
            config.get("title_key", "title"),
            config.get("id_key", "id"),
        )

    @callback(
        Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
        Input({"component": "KanbanBoard", "sub": "snapshot", "source_id": MATCH, "aio_id": ALL}, "data"),
        State({"component": "DataSource", "source_id": MATCH}, "data"),
        State({"component": "KanbanBoard", "sub": "config", "source_id": MATCH, "aio_id": ALL}, "data"),
        prevent_initial_call=True,
    )
    def _apply_drag(
        snapshots: list[dict[str, Any] | None],
        rows: list[dict[str, Any]],
        configs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        trigger = callback_context.triggered_id
        if not isinstance(trigger, dict):
            raise PreventUpdate
        aio_id = trigger.get("aio_id")
        inputs_list = callback_context.inputs_list[0]
        idx = next((i for i, inp in enumerate(inputs_list) if inp.get("id", {}).get("aio_id") == aio_id), None)
        if idx is None:
            raise PreventUpdate
        snapshot = snapshots[idx]
        if not snapshot or "snapshot" not in snapshot:
            raise PreventUpdate
        config_states = callback_context.states_list[1]
        config = next(
            (s.get("value") for s in config_states if s.get("id", {}).get("aio_id") == aio_id),
            None,
        )
        config = config or {}
        col_key = config.get("column_key", "status")
        id_key = config.get("id_key", "id")
        rows = rows or []
        by_id = {str(r.get(id_key)): r for r in rows}
        new_rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for col, ids in (snapshot.get("snapshot") or {}).items():
            for cid in ids:
                cid_s = str(cid)
                original = by_id.get(cid_s)
                if original is None:
                    continue
                updated = dict(original)
                updated[col_key] = col
                new_rows.append(updated)
                seen.add(cid_s)
        for r in rows:
            if str(r.get(id_key)) not in seen:
                new_rows.append(r)
        if new_rows == rows:
            raise PreventUpdate

        from .._writable import mirror_to_backing

        mirror_to_backing(new_rows)
        return new_rows


clientside_callback(
    """
    function(_children, _id) {
        if (window.__dbKanbanInstalled) return window.dash_clientside.no_update;
        window.__dbKanbanInstalled = true;

        if (!document.getElementById('dbd-kanban-style')) {
            const s = document.createElement('style');
            s.id = 'dbd-kanban-style';
            s.textContent = (
                '.dbd-kanban-ghost { opacity: 0.35; background: #dbeafe !important; }' +
                '.dbd-kanban-chosen { opacity: 0 !important; }' +
                '.dbd-kanban-fallback { opacity: 0.9 !important; transform: rotate(1deg); ' +
                'box-shadow: 0 6px 16px rgba(0,0,0,0.2); pointer-events: none; }'
            );
            document.head.appendChild(s);
        }

        function collectSnapshot(board) {
            const snapshot = {};
            board.querySelectorAll('.dbd-kanban-column').forEach(function(c) {
                snapshot[c.dataset.column] = Array.from(
                    c.querySelectorAll('.dbd-kanban-card')
                ).map(function(x) { return x.dataset.cardId; });
            });
            return snapshot;
        }

        function initCol(col) {
            if (col._dbdSortable || !window.Sortable) return;
            const board = col.closest('.dbd-kanban-board');
            if (!board) return;
            const group = board.dataset.group || 'kanban';
            const storeIdRaw = board.dataset.storeId;
            if (!storeIdRaw) return;
            let storeId;
            try { storeId = JSON.parse(storeIdRaw); } catch (_) { return; }
            col._dbdSortable = new Sortable(col, {
                group: group,
                animation: 150,
                forceFallback: true,
                ghostClass: 'dbd-kanban-ghost',
                chosenClass: 'dbd-kanban-chosen',
                fallbackClass: 'dbd-kanban-fallback',
                onEnd: function(evt) {
                    if (!window.dash_clientside || !window.dash_clientside.set_props) return;
                    const snapshot = collectSnapshot(board);
                    // Undo Sortable's DOM mutation so React's reconciler
                    // can replace the children cleanly when Dash re-renders.
                    const item = evt.item;
                    const from = evt.from;
                    const oldIndex = evt.oldIndex;
                    if (item && from) {
                        if (item.parentNode) item.parentNode.removeChild(item);
                        const siblings = from.children;
                        if (oldIndex == null || oldIndex >= siblings.length) {
                            from.appendChild(item);
                        } else {
                            from.insertBefore(item, siblings[oldIndex]);
                        }
                    }
                    window.dash_clientside.set_props(storeId, {
                        data: {snapshot: snapshot, ts: Date.now()}
                    });
                }
            });
        }

        function initAll() {
            if (!window.Sortable) return;
            document.querySelectorAll('.dbd-kanban-column').forEach(initCol);
        }

        initAll();
        const tryAgain = setInterval(function() {
            if (window.Sortable) {
                clearInterval(tryAgain);
                initAll();
            }
        }, 100);

        new MutationObserver(function() {
            initAll();
        }).observe(document.body, {childList: true, subtree: true});

        return window.dash_clientside.no_update;
    }
    """,
    Output({"component": "KanbanBoard", "sub": "root", "source_id": MATCH, "aio_id": MATCH}, "style"),
    Input({"component": "KanbanBoard", "sub": "root", "source_id": MATCH, "aio_id": MATCH}, "children"),
    State({"component": "KanbanBoard", "sub": "root", "source_id": MATCH, "aio_id": MATCH}, "id"),
)


def _render_board(
    rows: list[dict[str, Any]],
    columns: list[str],
    column_key: str,
    title_key: str,
    id_key: str,
) -> list[Any]:
    result: list[Any] = []
    for col in columns:
        col_rows = [r for r in rows if str(r.get(column_key, "")) == col]
        cards: list[Any] = [_render_card(r, str(r.get(id_key)), title_key) for r in col_rows]
        result.append(
            html.Div(
                [
                    html.Div(col, className="dbd-kanban-col-title", style={"fontWeight": 600, "marginBottom": "8px"}),
                    html.Div(
                        cards,
                        className="dbd-kanban-column",
                        **{"data-column": col},
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "6px",
                            "flex": "1 1 auto",
                            "minHeight": "240px",
                        },
                    ),
                ],
                style={
                    "background": "#f5f5f5",
                    "padding": "10px",
                    "borderRadius": "6px",
                    "display": "flex",
                    "flexDirection": "column",
                    "minHeight": "280px",
                },
            )
        )
    return result


def _render_card(row: dict[str, Any], card_id: str, title_key: str) -> Any:
    title = str(row.get(title_key, card_id))
    return html.Div(
        dbc.Card(
            dbc.CardBody(html.Div(title), style={"padding": "8px 10px"}),
            style={"padding": "0"},
        ),
        className="dbd-kanban-card",
        **{"data-card-id": card_id},
        style={"cursor": "grab"},
    )
