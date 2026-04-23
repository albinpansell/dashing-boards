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
    def _plotly_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Tree", "sub": "plotly", "source_id": source_id, "aio_id": aio_id}

    @staticmethod
    def _cyto_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Tree", "sub": "cyto", "source_id": source_id, "aio_id": aio_id}

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
                    id=self._cyto_id(self.source.source_id, self.aio_id),
                    elements=_tree_elements(self.source.initial(), self._label),
                    layout={"name": "preset", "animate": False, "fit": True, "padding": 20},
                    style={"width": "100%", "height": f"{self._height}px"},
                    stylesheet=_cyto_stylesheet(),
                ),
            ]
        return [
            dcc.Store(id=self._config_id(self.source.source_id, self.aio_id), data=config),
            dcc.Graph(
                id=self._plotly_id(self.source.source_id, self.aio_id),
                figure=_plotly_tree(self.source.initial(), self._kind, self._label, self._value),
                style={"height": f"{self._height}px"},
            ),
        ]

    @callback(
        Output({"component": "Tree", "sub": "plotly", "source_id": MATCH, "aio_id": MATCH}, "figure"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        Input({"component": "Tree", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
    )
    def _render_plotly(data: Any, config: dict[str, Any]) -> Any:
        config = config or {}
        return _plotly_tree(data, config.get("kind", "treemap"), config.get("label", "name"), config.get("value"))

    @callback(
        Output({"component": "Tree", "sub": "cyto", "source_id": MATCH, "aio_id": MATCH}, "elements"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        Input({"component": "Tree", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
    )
    def _render_cyto(data: Any, config: dict[str, Any]) -> list[dict[str, Any]]:
        return _tree_elements(data, (config or {}).get("label", "name"))


def _cyto_stylesheet() -> list[dict[str, Any]]:
    return [
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "shape": "round-rectangle",
                "background-color": "#ffffff",
                "border-color": "#4a7bb7",
                "border-width": 1.5,
                "color": "#1f2937",
                "text-valign": "center",
                "text-halign": "center",
                "text-wrap": "wrap",
                "text-max-width": 160,
                "font-size": 12,
                "padding": "10px",
                "width": "label",
                "height": "label",
            },
        },
        {
            "selector": "edge",
            "style": {
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
                "line-color": "#9ca3af",
                "target-arrow-color": "#9ca3af",
                "width": 1.5,
            },
        },
    ]


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
        labels=[r["label"] for r in df_rows],
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
    from ..graph.component import _layered_positions

    nodes = [{"id": str(r.get("id")), "_label": str(r.get(label_col, r.get("id")))} for r in rows]
    edges = [
        {"source": str(r.get("parent_id")), "target": str(r.get("id"))}
        for r in rows
        if r.get("parent_id") not in (None, "")
    ]
    positions = _layered_positions(nodes, edges, "id", "source", "target")
    elements: list[dict[str, Any]] = []
    for n in nodes:
        nid = n["id"]
        entry: dict[str, Any] = {"data": {"id": nid, "label": n["_label"]}}
        if nid in positions:
            x, y = positions[nid]
            entry["position"] = {"x": x, "y": y}
        elements.append(entry)
    for e in edges:
        elements.append({"data": {"source": e["source"], "target": e["target"]}})
    return elements
