from __future__ import annotations

from typing import Any

from dash import MATCH, Input, Output, callback, dcc

from ...binding.component import DataBoundComponent
from ...binding.types import DataType


def _layout_options(name: str) -> dict[str, Any]:
    if name in {"klay", "dagre", "hierarchical", "preset"}:
        # Use preset positions computed server-side for full determinism.
        return {"name": "preset", "animate": False, "fit": True, "padding": 20}
    return {"name": name, "animate": False}


def _layered_positions(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    node_id: str,
    edge_source: str,
    edge_target: str,
) -> dict[str, tuple[int, int]]:
    """Compute deterministic (x, y) for each node via a layered top-down layout.

    Roots (no incoming edges) are placed at layer 0; each child goes one layer
    deeper. Cyclic edges are ignored when computing layers (deterministic via
    sorted node-id traversal). Returns {node_id: (x, y)}.
    """
    ids = [str(n[node_id]) for n in nodes]
    id_set = set(ids)
    children: dict[str, list[str]] = {i: [] for i in ids}
    incoming: dict[str, int] = {i: 0 for i in ids}
    for e in edges:
        s, t = str(e[edge_source]), str(e[edge_target])
        if s not in id_set or t not in id_set or s == t:
            continue
        children[s].append(t)
        incoming[t] += 1
    for k in children:
        children[k].sort()

    layer: dict[str, int] = {}
    roots = sorted([i for i in ids if incoming[i] == 0])
    queue = [(r, 0) for r in roots]
    while queue:
        next_queue: list[tuple[str, int]] = []
        for nid, d in queue:
            if nid in layer and layer[nid] <= d:
                continue
            layer[nid] = d
            for c in children[nid]:
                next_queue.append((c, d + 1))
        queue = next_queue

    max_layer = max(layer.values(), default=-1)
    orphans = sorted([i for i in ids if i not in layer])
    for i in orphans:
        layer[i] = max_layer + 1

    by_layer: dict[int, list[str]] = {}
    for nid, d in layer.items():
        by_layer.setdefault(d, []).append(nid)
    for d in by_layer:
        by_layer[d].sort()

    x_spacing = 180
    y_spacing = 100
    positions: dict[str, tuple[int, int]] = {}
    for d, row in sorted(by_layer.items()):
        offset = -((len(row) - 1) * x_spacing) / 2
        for i, nid in enumerate(row):
            positions[nid] = (int(offset + i * x_spacing), d * y_spacing)
    return positions


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
    positions = _layered_positions(nodes, edges, node_id, edge_source, edge_target)
    elements: list[dict[str, Any]] = []
    for n in nodes:
        nid = str(n[node_id])
        data = {"id": nid, "label": str(n.get(node_label, nid))}
        if node_group and node_group in n:
            data["group"] = str(n[node_group])
        entry: dict[str, Any] = {"data": data}
        if nid in positions:
            x, y = positions[nid]
            entry["position"] = {"x": x, "y": y}
        elements.append(entry)
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
        layout: str = "klay",
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

        cyto.load_extra_layouts()
        elements = _to_elements(self.source.initial(), **self._opts)
        return [
            dcc.Store(
                id=self._config_id(self.source.source_id, self.aio_id),
                data=self._opts,
            ),
            cyto.Cytoscape(
                id=self._cy_id(self.source.source_id, self.aio_id),
                elements=elements,
                layout=_layout_options(self._layout),
                style={"width": "100%", "height": f"{self._height}px"},
                stylesheet=[
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
