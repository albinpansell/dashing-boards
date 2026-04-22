from __future__ import annotations

from typing import Any

from dash import MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


class Tree(DataBoundComponent):
    """Tree visualization over TREE_ROWS data (id / parent_id / label / value).

    `kind`:
      - "treemap" | "sunburst" | "icicle": Plotly hierarchical charts.
        Good for displaying a metric sized by node (`value=...`).
      - "node_link": dash-cytoscape with a dagre layout, shows parent→child edges.
    """

    ACCEPTED_TYPES = frozenset({DataType.TREE_ROWS})

    def __init__(
        self,
        source: Any,
        kind: str = "treemap",
        label: str = "name",
        value: str | None = None,
        height: int = 400,
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        if kind not in {"treemap", "sunburst", "icicle", "node_link"}:
            raise ValueError(f"Tree kind must be treemap|sunburst|icicle|node_link; got '{kind}'")
        self._kind = kind
        self._label = label
        self._value = value
        self._height = height
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _graph_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Tree", "sub": "graph", "source_id": source_id, "aio_id": aio_id}

    @staticmethod
    def _config_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Tree", "sub": "config", "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        config = {"kind": self._kind, "label": self._label, "value": self._value, "height": self._height}
        if self._kind == "node_link":
            import dash_cytoscape as cyto

            cyto.load_extra_layouts()
            return [
                dcc.Store(id=self._config_id(self.source.source_id, self.aio_id), data=config),
                cyto.Cytoscape(
                    id=self._graph_id(self.source.source_id, self.aio_id),
                    elements=_tree_elements(self.source.initial(), self._label),
                    layout={"name": "dagre"},
                    style={"width": "100%", "height": f"{self._height}px"},
                    stylesheet=[
                        {"selector": "node", "style": {"label": "data(label)"}},
                        {"selector": "edge", "style": {"curve-style": "bezier", "target-arrow-shape": "triangle"}},
                    ],
                ),
            ]
        return [
            dcc.Store(id=self._config_id(self.source.source_id, self.aio_id), data=config),
            dcc.Graph(
                id=self._graph_id(self.source.source_id, self.aio_id),
                figure=_plotly_tree(self.source.initial(), self._kind, self._label, self._value),
                style={"height": f"{self._height}px"},
            ),
        ]

    @callback(
        Output(
            {"component": "Tree", "sub": "graph", "source_id": MATCH, "aio_id": MATCH}, "figure", allow_duplicate=True
        ),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        Input({"component": "Tree", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
        prevent_initial_call=True,
    )
    def _render_plotly(data: Any, config: dict[str, Any]) -> Any:
        if not config or config.get("kind") == "node_link":
            from dash.exceptions import PreventUpdate

            raise PreventUpdate
        return _plotly_tree(data, config["kind"], config.get("label", "name"), config.get("value"))

    @callback(
        Output(
            {"component": "Tree", "sub": "graph", "source_id": MATCH, "aio_id": MATCH}, "elements", allow_duplicate=True
        ),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        Input({"component": "Tree", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
        prevent_initial_call=True,
    )
    def _render_cyto(data: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
        if not config or config.get("kind") != "node_link":
            from dash.exceptions import PreventUpdate

            raise PreventUpdate
        return _tree_elements(data, config.get("label", "name"))


def _plotly_tree(rows: Any, kind: str, label_col: str, value_col: str | None) -> Any:
    import plotly.express as px
    import plotly.graph_objects as go

    if not rows:
        return go.Figure()
    df_rows = []
    for r in rows:
        df_rows.append(
            {
                "id": str(r.get("id")),
                "parent": "" if r.get("parent_id") in (None, "") else str(r.get("parent_id")),
                "label": str(r.get(label_col, r.get("id"))),
                "value": r.get(value_col) if value_col else 1,
            }
        )
    kwargs = dict(
        ids=[r["id"] for r in df_rows],
        parents=[r["parent"] for r in df_rows],
        names=[r["label"] for r in df_rows],
        values=[r["value"] for r in df_rows],
    )
    if kind == "treemap":
        return go.Figure(go.Treemap(**kwargs))
    if kind == "sunburst":
        return go.Figure(go.Sunburst(**kwargs))
    if kind == "icicle":
        return go.Figure(go.Icicle(**kwargs))
    return go.Figure()


def _tree_elements(rows: Any, label_col: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    elements: list[dict[str, Any]] = []
    for r in rows:
        node_id = str(r.get("id"))
        elements.append({"data": {"id": node_id, "label": str(r.get(label_col, node_id))}})
    for r in rows:
        parent = r.get("parent_id")
        if parent not in (None, ""):
            elements.append({"data": {"source": str(parent), "target": str(r.get("id"))}})
    return elements
