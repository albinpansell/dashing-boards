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
    ids = [e["data"].get("id") for e in elements if "id" in e.get("data", {})]
    sources = [(e["data"].get("source"), e["data"].get("target")) for e in elements if "source" in e.get("data", {})]
    assert "a" in ids and "b" in ids
    assert ("a", "b") in sources


def test_tree_elements_builds_parent_edges() -> None:
    rows = [
        {"id": "r", "parent_id": None, "name": "Root"},
        {"id": "c", "parent_id": "r", "name": "Child"},
    ]
    elements = _tree_elements(rows, "name")
    ids = {e["data"].get("id") for e in elements if "id" in e.get("data", {})}
    pairs = {(e["data"].get("source"), e["data"].get("target")) for e in elements if "source" in e.get("data", {})}
    assert ids == {"r", "c"}
    assert ("r", "c") in pairs


def test_tree_elements_empty() -> None:
    assert _tree_elements([], "name") == []
