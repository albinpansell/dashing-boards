from __future__ import annotations

from dash import Dash, html
import dash_bootstrap_components as dbc

from dashing_boards import TreeTableAIO


def build_rows() -> list[dict[str, object]]:
    return [
        {"id": "project", "parent_id": None, "name": "Project", "budget": 0, "status": "open"},
        {"id": "design", "parent_id": "project", "name": "Design", "budget": 120, "status": "open"},
        {"id": "build", "parent_id": "project", "name": "Build", "budget": 250, "status": "open"},
        {"id": "qa", "parent_id": "project", "name": "QA", "budget": 80, "status": "open"},
    ]


def main() -> int:
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = html.Div(
        [
            html.H3("TreeTableAIO Demo"),
            TreeTableAIO(
                rows=build_rows(),
                editable=True,
                aggregations={"budget": "sum", "status": "equal"},
                column_labels={"budget": "Budget", "status": "Status"},
                aio_id="demo-tree",
            ),
        ],
        style={"maxWidth": "900px", "margin": "24px auto"},
    )
    app.run(debug=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
