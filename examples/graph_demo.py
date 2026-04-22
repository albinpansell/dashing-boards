"""Graph + Tree demo."""

from __future__ import annotations

from dash import Dash

from dashing_boards import DataType, Graph, Grid, Page, StaticData, Tree

graph_payload = {
    "nodes": [
        {"id": "a", "name": "Alpha"},
        {"id": "b", "name": "Beta"},
        {"id": "c", "name": "Gamma"},
        {"id": "d", "name": "Delta"},
    ],
    "edges": [
        {"source": "a", "target": "b"},
        {"source": "a", "target": "c"},
        {"source": "b", "target": "d"},
        {"source": "c", "target": "d"},
    ],
}
graph_src = StaticData(graph_payload, DataType.GRAPH, source_id="g")

tree_rows = [
    {"id": "root", "parent_id": None, "name": "Root", "size": 100},
    {"id": "a", "parent_id": "root", "name": "A", "size": 40},
    {"id": "b", "parent_id": "root", "name": "B", "size": 60},
    {"id": "a1", "parent_id": "a", "name": "A.1", "size": 15},
    {"id": "a2", "parent_id": "a", "name": "A.2", "size": 25},
]
tree_src = StaticData(tree_rows, DataType.TREE_ROWS, source_id="t")

app = Dash(__name__)
app.layout = Page(
    [
        Grid(
            [
                [Graph(graph_src, node_label="name", layout="cose")],
                [Tree(tree_src, kind="treemap", label="name", value="size")],
            ],
            columns=2,
        ),
        graph_src.store(),
        tree_src.store(),
    ],
    title="Graph + Tree demo",
)

if __name__ == "__main__":
    app.run(debug=True)
