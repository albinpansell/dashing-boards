from __future__ import annotations

from dashing_boards.components.graph.component import _to_elements
from dashing_boards.components.tree.component import _tree_elements


def test_graph_to_elements_includes_nodes_and_edges() -> None:
    payload = {
        "nodes": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
        "edges": [{"source": "a", "target": "b"}],
    }
    elements = _to_elements(
        payload,
        node_id="id",
        node_label="name",
        node_group=None,
        edge_source="source",
        edge_target="target",
        edge_weight=None,
    )
    assert {"data": {"id": "a", "label": "A"}} in elements
    assert {"data": {"source": "a", "target": "b"}} in elements


def test_tree_elements_builds_parent_edges() -> None:
    rows = [
        {"id": "r", "parent_id": None, "name": "Root"},
        {"id": "c", "parent_id": "r", "name": "Child"},
    ]
    elements = _tree_elements(rows, "name")
    assert {"data": {"id": "r", "label": "Root"}} in elements
    assert {"data": {"id": "c", "label": "Child"}} in elements
    assert {"data": {"source": "r", "target": "c"}} in elements


def test_tree_elements_empty() -> None:
    assert _tree_elements([], "name") == []
