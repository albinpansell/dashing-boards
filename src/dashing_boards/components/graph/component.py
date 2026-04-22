from __future__ import annotations

from typing import Any

from dash import MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


def _to_elements(
    payload: Any,
    node_id: str,
    node_label: str,
    node_group: str | None,
    edge_source: str,
    edge_target: str,
    edge_weight: str | None,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    nodes = payload.get("nodes") or []
    edges = payload.get("edges") or []
    elements: list[dict[str, Any]] = []
    for n in nodes:
        data = {"id": str(n[node_id]), "label": str(n.get(node_label, n[node_id]))}
        if node_group and node_group in n:
            data["group"] = str(n[node_group])
        elements.append({"data": data})
    for e in edges:
        data = {"source": str(e[edge_source]), "target": str(e[edge_target])}
        if edge_weight and edge_weight in e:
            data["weight"] = e[edge_weight]
        elements.append({"data": data})
    return elements


class Graph(DataBoundComponent):
    """Node-edge graph using dash-cytoscape.

    Source payload shape: {"nodes": [...], "edges": [...]}.
    Column/key names for id, label, edge endpoints, etc. are configurable.
    """

    ACCEPTED_TYPES = frozenset({DataType.GRAPH})

    def __init__(
        self,
        source: Any,
        node_id: str = "id",
        node_label: str = "name",
        node_group: str | None = None,
        edge_source: str = "source",
        edge_target: str = "target",
        edge_weight: str | None = None,
        layout: str = "cose",
        height: int = 400,
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        self._opts = {
            "node_id": node_id,
            "node_label": node_label,
            "node_group": node_group,
            "edge_source": edge_source,
            "edge_target": edge_target,
            "edge_weight": edge_weight,
        }
        self._layout = layout
        self._height = height
        super().__init__(source, aio_id=aio_id, container_props=container_props)

    @staticmethod
    def _cy_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Graph", "sub": "cy", "source_id": source_id, "aio_id": aio_id}

    @staticmethod
    def _config_id(source_id: str, aio_id: str) -> dict[str, str]:
        return {"component": "Graph", "sub": "config", "source_id": source_id, "aio_id": aio_id}

    def _build(self) -> list[Any]:
        import dash_cytoscape as cyto

        elements = _to_elements(self.source.initial(), **self._opts)
        return [
            dcc.Store(
                id=self._config_id(self.source.source_id, self.aio_id),
                data=self._opts,
            ),
            cyto.Cytoscape(
                id=self._cy_id(self.source.source_id, self.aio_id),
                elements=elements,
                layout={"name": self._layout},
                style={"width": "100%", "height": f"{self._height}px"},
                stylesheet=[
                    {"selector": "node", "style": {"label": "data(label)", "background-color": "#6fa8dc"}},
                    {"selector": "edge", "style": {"curve-style": "bezier", "target-arrow-shape": "triangle"}},
                ],
            ),
        ]

    @callback(
        Output({"component": "Graph", "sub": "cy", "source_id": MATCH, "aio_id": MATCH}, "elements"),
        Input({"component": "DataSource", "source_id": MATCH}, "data"),
        Input({"component": "Graph", "sub": "config", "source_id": MATCH, "aio_id": MATCH}, "data"),
    )
    def _render(data: Any, opts: dict[str, Any]) -> list[dict[str, Any]]:
        return _to_elements(data, **(opts or {}))
