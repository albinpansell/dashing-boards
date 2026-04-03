from __future__ import annotations

import uuid
from typing import Any

from dash import ALL, MATCH, Input, Output, State, callback, callback_context, dcc, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from .aggregation import AggregationType, parse_aggregation
from .model import TreeTableModel


class TreeTableAIO(html.Div):
    FONT_SIZES = {
        "body": "14px",
        "small": "12px",
    }

    class ids:
        aio_root = staticmethod(lambda aio_id: {"component": "TreeTableAIO", "subcomponent": "root", "aio_id": aio_id})
        state = staticmethod(lambda aio_id: {"component": "TreeTableAIO", "subcomponent": "state", "aio_id": aio_id})
        config = staticmethod(lambda aio_id: {"component": "TreeTableAIO", "subcomponent": "config", "aio_id": aio_id})
        table = staticmethod(lambda aio_id: {"component": "TreeTableAIO", "subcomponent": "table", "aio_id": aio_id})
        toggle = staticmethod(
            lambda aio_id, item_id: {
                "component": "TreeTableAIO",
                "subcomponent": "toggle",
                "aio_id": aio_id,
                "item_id": item_id,
            }
        )
        cell = staticmethod(
            lambda aio_id, item_id, column: {
                "component": "TreeTableAIO",
                "subcomponent": "cell",
                "aio_id": aio_id,
                "item_id": item_id,
                "column": column,
            }
        )
        expand_all = staticmethod(
            lambda aio_id: {"component": "TreeTableAIO", "subcomponent": "expand_all", "aio_id": aio_id}
        )
        collapse_all = staticmethod(
            lambda aio_id: {"component": "TreeTableAIO", "subcomponent": "collapse_all", "aio_id": aio_id}
        )

    ids = ids

    def __init__(
        self,
        rows: list[dict[str, Any]],
        columns: list[str] | None = None,
        editable: bool = False,
        aggregations: dict[str, AggregationType | str] | None = None,
        column_labels: dict[str, str] | None = None,
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
        table_props: dict[str, Any] | None = None,
    ) -> None:
        resolved_aio_id = aio_id or str(uuid.uuid4())
        normalized_aggs = self._normalize_aggregations(aggregations or {})
        model = TreeTableModel(rows=rows, aggregation_map=normalized_aggs)

        state_data = {
            "rows": model.rows,
            "collapsed": [],
            "aggregations": {key: value.value for key, value in normalized_aggs.items()},
        }
        config_data = {
            "columns": columns,
            "editable": editable,
            "column_labels": column_labels or {},
            "table_props": table_props or {},
        }

        props = dict(container_props or {})
        props["id"] = self.ids.aio_root(resolved_aio_id)
        children = [
            dcc.Store(id=self.ids.state(resolved_aio_id), data=state_data),
            dcc.Store(id=self.ids.config(resolved_aio_id), data=config_data),
            html.Div(id=self.ids.table(resolved_aio_id)),
        ]
        super().__init__(children=children, **props)

    @staticmethod
    def _normalize_aggregations(
        aggregations: dict[str, AggregationType | str],
    ) -> dict[str, AggregationType]:
        return {key: parse_aggregation(value) for key, value in aggregations.items()}

    @staticmethod
    def _model_from_state(state_data: dict[str, Any]) -> TreeTableModel:
        aggregation_map = {
            key: parse_aggregation(value) for key, value in (state_data.get("aggregations") or {}).items()
        }
        return TreeTableModel(rows=state_data.get("rows") or [], aggregation_map=aggregation_map)

    @staticmethod
    def _state_with_model(
        model: TreeTableModel,
        collapsed: set[str],
        aggregations: dict[str, AggregationType | str],
    ) -> dict[str, Any]:
        normalized = TreeTableAIO._normalize_aggregations(aggregations)
        return {
            "rows": model.rows,
            "collapsed": sorted(collapsed),
            "aggregations": {key: value.value for key, value in normalized.items()},
        }

    @staticmethod
    def _coerce_value(existing: object, incoming: object) -> object:
        if incoming is None:
            return None
        if isinstance(existing, bool):
            if isinstance(incoming, bool):
                return incoming
            incoming_str = str(incoming).strip().lower()
            if incoming_str in {"true", "1", "yes", "on"}:
                return True
            if incoming_str in {"false", "0", "no", "off"}:
                return False
            raise ValueError(f"Invalid boolean value: {incoming}")
        if isinstance(existing, int) and not isinstance(existing, bool):
            try:
                return int(str(incoming))
            except (TypeError, ValueError):
                return incoming
        if isinstance(existing, float):
            try:
                return float(str(incoming))
            except (TypeError, ValueError):
                return incoming
        return incoming

    @staticmethod
    def _display_columns(model: TreeTableModel, configured_columns: list[str] | None) -> list[str]:
        if configured_columns:
            return configured_columns
        return ["name"] + [column for column in model.columns if column not in {"id", "parent_id", "name"}]

    @staticmethod
    def _label_for(column: str, labels: dict[str, str]) -> str:
        if column in labels:
            return labels[column]
        return column.replace("_", " ").title()

    @staticmethod
    def _format_value(value: object) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _compute_column_widths(
        items: list[dict[str, Any]], columns: list[str], labels: dict[str, str]
    ) -> dict[str, str]:
        widths: dict[str, str] = {}
        for column in columns:
            label_len = len(TreeTableAIO._label_for(column, labels))
            max_chars = label_len
            for item in items:
                if column == "name":
                    depth = int(item.get("_depth", 0))
                    name_len = len(TreeTableAIO._format_value(item.get("name")))
                    effective = depth * 3 + name_len + 4
                else:
                    effective = len(TreeTableAIO._format_value(item.get(column)))
                if effective > max_chars:
                    max_chars = effective
            if column == "name":
                width = min(max(max_chars * 7 + 20, 180), 420)
            else:
                width = min(max(max_chars * 8 + 16, 90), 320)
            widths[column] = f"{width}px"
        return widths

    @staticmethod
    def build_table(
        aio_id: str,
        state_data: dict[str, Any],
        config_data: dict[str, Any],
    ) -> html.Div:
        model = TreeTableAIO._model_from_state(state_data)
        collapsed = set(state_data.get("collapsed") or [])

        columns = TreeTableAIO._display_columns(model, config_data.get("columns"))
        editable = bool(config_data.get("editable", False))
        labels = config_data.get("column_labels") or {}
        items = model.visible_items(collapsed)
        col_widths = TreeTableAIO._compute_column_widths(items, columns, labels)

        header_cells: list[html.Th] = []
        for column in columns:
            label = TreeTableAIO._label_for(column, labels)
            agg = model.get_aggregation(column)
            suffix = f" [{agg.value}]" if agg.value != "none" else ""
            header_cells.append(
                html.Th(
                    f"{label}{suffix}",
                    style={
                        "fontSize": TreeTableAIO.FONT_SIZES["body"],
                        "whiteSpace": "nowrap",
                        "textAlign": "left",
                        "minWidth": col_widths.get(column, "auto"),
                    },
                )
            )

        body_rows: list[html.Tr] = []
        for item in items:
            item_id = str(item["id"])
            depth = int(item.get("_depth", 0))
            has_children = bool(item.get("_has_children", False))
            is_collapsed = bool(item.get("_collapsed", False))
            toggle_text = "▸" if is_collapsed else "▾"
            if not has_children:
                toggle_text = "•"

            cells: list[html.Td] = []
            for column in columns:
                value = item.get(column)
                if column == "name":
                    name_child: object
                    if editable:
                        name_child = dcc.Input(
                            id=TreeTableAIO.ids.cell(aio_id, item_id, column),
                            value=TreeTableAIO._format_value(value),
                            type="text",
                            debounce=True,
                            style={
                                "border": "1px solid transparent",
                                "background": "transparent",
                                "fontSize": TreeTableAIO.FONT_SIZES["body"],
                                "padding": "2px 4px",
                                "outline": "none",
                                "borderRadius": "3px",
                            },
                            className="editable-cell-input",
                        )
                    else:
                        name_child = html.Span(TreeTableAIO._format_value(value))
                    cell_content = html.Div(
                        [
                            html.Span(
                                toggle_text,
                                id=TreeTableAIO.ids.toggle(aio_id, item_id),
                                style={
                                    "cursor": "pointer" if has_children else "default",
                                    "userSelect": "none",
                                    "display": "inline-block",
                                    "width": "14px",
                                    "textAlign": "center",
                                    "fontSize": TreeTableAIO.FONT_SIZES["body"],
                                },
                            ),
                            name_child,
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "paddingLeft": f"{depth * 20}px",
                            "gap": "6px",
                        },
                    )
                    cells.append(
                        html.Td(
                            cell_content,
                            style={
                                "fontSize": TreeTableAIO.FONT_SIZES["body"],
                                "verticalAlign": "middle",
                                "whiteSpace": "nowrap",
                                "minWidth": col_widths.get(column, "auto"),
                            },
                        )
                    )
                    continue

                if editable:
                    cell_content = dcc.Input(
                        id=TreeTableAIO.ids.cell(aio_id, item_id, column),
                        value=TreeTableAIO._format_value(value),
                        type="text",
                        debounce=True,
                        style={
                            "border": "1px solid transparent",
                            "background": "transparent",
                            "width": "100%",
                            "fontSize": TreeTableAIO.FONT_SIZES["body"],
                            "padding": "2px 4px",
                            "outline": "none",
                            "borderRadius": "3px",
                        },
                        className="editable-cell-input",
                    )
                else:
                    cell_content = html.Span(TreeTableAIO._format_value(value))

                cells.append(
                    html.Td(
                        cell_content,
                        style={
                            "fontSize": TreeTableAIO.FONT_SIZES["body"],
                            "verticalAlign": "middle",
                            "whiteSpace": "nowrap",
                            "minWidth": col_widths.get(column, "auto"),
                        },
                    )
                )

            body_rows.append(html.Tr(cells))

        if not body_rows:
            body_rows = [
                html.Tr(
                    [
                        html.Td(
                            "No items",
                            colSpan=max(1, len(columns)),
                            style={"padding": "10px", "textAlign": "center", "color": "#666"},
                        )
                    ]
                )
            ]

        table_style = {"tableLayout": "auto"}
        table_style.update(config_data.get("table_props") or {})

        table = dbc.Table(
            [html.Thead(html.Tr(header_cells)), html.Tbody(body_rows)],
            bordered=True,
            striped=True,
            hover=True,
            size="sm",
            style=table_style,
        )

        controls = html.Div(
            [
                dbc.Button(
                    "▾ Expand All",
                    id=TreeTableAIO.ids.expand_all(aio_id),
                    color="link",
                    size="sm",
                    style={"fontSize": TreeTableAIO.FONT_SIZES["small"], "padding": "2px 8px"},
                ),
                dbc.Button(
                    "▸ Collapse All",
                    id=TreeTableAIO.ids.collapse_all(aio_id),
                    color="link",
                    size="sm",
                    style={"fontSize": TreeTableAIO.FONT_SIZES["small"], "padding": "2px 8px"},
                ),
            ],
            className="mb-1",
        )

        return html.Div(
            [controls, table],
            style={"overflowX": "auto"},
        )

    @callback(
        Output(ids.table(MATCH), "children"),
        Input(ids.state(MATCH), "data"),
        State(ids.config(MATCH), "data"),
        State(ids.aio_root(MATCH), "id"),
    )
    def _render_from_state(
        state_data: dict[str, Any],
        config_data: dict[str, Any],
        root_id: dict[str, str],
    ) -> html.Div:
        aio_id = root_id["aio_id"]
        return TreeTableAIO.build_table(aio_id, state_data or {}, config_data or {})

    @callback(
        Output(ids.state(MATCH), "data", allow_duplicate=True),
        Input(ids.toggle(MATCH, ALL), "n_clicks"),
        State(ids.state(MATCH), "data"),
        prevent_initial_call=True,
    )
    def _toggle_item(
        toggle_clicks: list[int | None],
        state_data: dict[str, Any],
    ) -> dict[str, Any]:
        del toggle_clicks
        trigger = callback_context.triggered_id
        if not trigger or not isinstance(trigger, dict):
            raise PreventUpdate

        item_id = str(trigger.get("item_id"))
        model = TreeTableAIO._model_from_state(state_data or {})
        if not model.has_children(item_id):
            raise PreventUpdate

        collapsed = set((state_data or {}).get("collapsed") or [])
        if item_id in collapsed:
            collapsed.remove(item_id)
        else:
            collapsed.add(item_id)

        aggregations = (state_data or {}).get("aggregations") or {}
        return TreeTableAIO._state_with_model(model, collapsed, aggregations)

    @callback(
        Output(ids.state(MATCH), "data", allow_duplicate=True),
        Input(ids.expand_all(MATCH), "n_clicks"),
        State(ids.state(MATCH), "data"),
        prevent_initial_call=True,
    )
    def _expand_all(
        expand_clicks: int | None,
        state_data: dict[str, Any],
    ) -> dict[str, Any]:
        if not expand_clicks:
            raise PreventUpdate
        model = TreeTableAIO._model_from_state(state_data or {})
        aggregations = (state_data or {}).get("aggregations") or {}
        return TreeTableAIO._state_with_model(model, set(), aggregations)

    @callback(
        Output(ids.state(MATCH), "data", allow_duplicate=True),
        Input(ids.collapse_all(MATCH), "n_clicks"),
        State(ids.state(MATCH), "data"),
        prevent_initial_call=True,
    )
    def _collapse_all(
        collapse_clicks: int | None,
        state_data: dict[str, Any],
    ) -> dict[str, Any]:
        if not collapse_clicks:
            raise PreventUpdate

        model = TreeTableAIO._model_from_state(state_data or {})
        collapsed = {item_id for item_id in (str(row["id"]) for row in model.rows) if model.has_children(item_id)}
        aggregations = (state_data or {}).get("aggregations") or {}
        return TreeTableAIO._state_with_model(model, collapsed, aggregations)

    @callback(
        Output(ids.state(MATCH), "data", allow_duplicate=True),
        Input(ids.cell(MATCH, ALL, ALL), "value"),
        State(ids.state(MATCH), "data"),
        prevent_initial_call=True,
    )
    def _edit_cell(
        values: list[object],
        state_data: dict[str, Any],
    ) -> dict[str, Any]:
        del values
        trigger = callback_context.triggered_id
        if not trigger or not isinstance(trigger, dict):
            raise PreventUpdate

        item_id = str(trigger.get("item_id"))
        column = str(trigger.get("column"))
        trigger_value = callback_context.triggered[0]["value"] if callback_context.triggered else None

        model = TreeTableAIO._model_from_state(state_data or {})
        try:
            current_item = model.get_item(item_id)
        except ValueError as error:
            raise PreventUpdate from error

        current_value = current_item.get(column)
        next_value = TreeTableAIO._coerce_value(current_value, trigger_value)
        if current_value == next_value:
            raise PreventUpdate

        model.update_field(item_id, column, next_value)
        collapsed = set((state_data or {}).get("collapsed") or [])
        aggregations = (state_data or {}).get("aggregations") or {}
        return TreeTableAIO._state_with_model(model, collapsed, aggregations)
