from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import Dash, html

from dashing_boards import TreeTableAIO


def build_rows() -> list[dict[str, object]]:
    return [
        {"id": "project", "parent_id": None, "name": "Project", "owner": "Alex", "budget": 0},
        {"id": "design", "parent_id": "project", "name": "Design", "owner": "Mia", "budget": 120},
        {"id": "build", "parent_id": "project", "name": "Build", "owner": "Noah", "budget": 250},
        {"id": "qa", "parent_id": "project", "name": "QA", "owner": "Sara", "budget": 80},
    ]


def main() -> int:
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = html.Div(
        [
            html.H3("TreeTableAIO Edit Mode Demo"),
            html.P("Edit any visible cell and press Enter to apply changes."),
            TreeTableAIO(
                rows=build_rows(),
                editable=True,
                aggregations={"budget": "sum"},
                column_labels={"owner": "Owner", "budget": "Budget"},
                aio_id="edit-demo-tree",
            ),
        ],
        style={"maxWidth": "1000px", "margin": "24px auto"},
    )
    app.run(debug=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
