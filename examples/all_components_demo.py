"""Every component mounted in a single Dash app.

Exercises every component in the library on one scrollable page so we
can verify they coexist, register their callbacks without collision,
and render correctly side-by-side.
"""

from __future__ import annotations

from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html
from sqlalchemy import create_engine, text

from dashing_boards import (
    BarChart,
    BoxChart,
    Button,
    DataType,
    DatePicker,
    Dropdown,
    FileDataSource,
    Graph,
    Grid,
    Heatmap,
    Histogram,
    KanbanBoard,
    LineChart,
    Loading,
    Modal,
    Page,
    PieChart,
    Sankey,
    ScatterChart,
    SqlDataSource,
    StaticData,
    Tab,
    Table,
    Tabs,
    TagList,
    TextBox,
    TextField,
    Toast,
    Toggle,
    Tree,
    Treemap,
    TreeTableAIO,
    make_app,
)


# ---------- Data sources ----------

title_src = StaticData("Dashing Boards — everything demo", DataType.STRING, source_id="title")
tags_src = StaticData(["python", "dash", "plotly", "cytoscape"], DataType.STRING_LIST, source_id="tags")
toggle_src = StaticData(False, DataType.BOOL, source_id="toggle")
date_src = StaticData("2026-04-23", DataType.STRING, source_id="date")
region_src = StaticData("north", DataType.STRING, source_id="region")
click_src = StaticData(0, DataType.NUMBER, source_id="clicks")

sales_rows = [
    {"region": "north", "product": "A", "revenue": 10, "month": "Jan"},
    {"region": "north", "product": "B", "revenue": 20, "month": "Jan"},
    {"region": "south", "product": "A", "revenue": 15, "month": "Feb"},
    {"region": "south", "product": "B", "revenue": 25, "month": "Feb"},
    {"region": "north", "product": "A", "revenue": 30, "month": "Mar"},
    {"region": "south", "product": "B", "revenue": 12, "month": "Mar"},
]
sales_src = StaticData(sales_rows, DataType.DATAFRAME, source_id="sales")

heat_rows = [
    {"x": "Mon", "y": "AM", "count": 3},
    {"x": "Mon", "y": "PM", "count": 5},
    {"x": "Tue", "y": "AM", "count": 6},
    {"x": "Tue", "y": "PM", "count": 2},
    {"x": "Wed", "y": "AM", "count": 4},
    {"x": "Wed", "y": "PM", "count": 8},
]
heat_src = StaticData(heat_rows, DataType.DATAFRAME, source_id="heat")

flow_rows = [
    {"source": "Ads", "target": "Signup", "value": 50},
    {"source": "Organic", "target": "Signup", "value": 80},
    {"source": "Signup", "target": "Paid", "value": 40},
    {"source": "Signup", "target": "Churn", "value": 90},
]
flow_src = StaticData(flow_rows, DataType.DATAFRAME, source_id="flow")

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
graph_src = StaticData(graph_payload, DataType.GRAPH, source_id="graph")

tree_rows = [
    {"id": "root", "parent_id": None, "name": "Root", "size": 100},
    {"id": "eng", "parent_id": "root", "name": "Engineering", "size": 60},
    {"id": "design", "parent_id": "root", "name": "Design", "size": 40},
    {"id": "fe", "parent_id": "eng", "name": "Frontend", "size": 25},
    {"id": "be", "parent_id": "eng", "name": "Backend", "size": 35},
]
tree_src = StaticData(tree_rows, DataType.TREE_ROWS, source_id="tree")

kanban_rows = [
    {"id": "k1", "title": "Write requirements", "status": "done"},
    {"id": "k2", "title": "Build MVP", "status": "doing"},
    {"id": "k3", "title": "Polish drag-and-drop", "status": "todo"},
    {"id": "k4", "title": "Write docs", "status": "todo"},
]
kanban_src = StaticData(kanban_rows, DataType.DATAFRAME, source_id="kanban")

csv_path = Path(__file__).parent / "_tasks.csv"
if not csv_path.exists():
    csv_path.write_text("id,title,status\n1,Write docs,todo\n2,Ship PR,doing\n3,Take break,done\n")
file_src = FileDataSource(csv_path, writable=True, watch=False, source_id="file_tasks")


def _make_sql_source() -> SqlDataSource:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sql_sales (region TEXT, product TEXT, revenue REAL)"))
        conn.execute(
            text(
                "INSERT INTO sql_sales VALUES "
                "('north', 'A', 10),('north', 'B', 20),('south', 'A', 15),('south', 'B', 25)"
            )
        )
    return SqlDataSource(
        engine,
        "SELECT region, product, revenue FROM sql_sales",
        data_type=DataType.DATAFRAME,
        source_id="sql_sales",
    )


sql_src = _make_sql_source()

tree_table_rows = [
    {"id": "project", "parent_id": None, "name": "Project", "owner": "Alex", "budget": 0, "status": "open"},
    {"id": "design", "parent_id": "project", "name": "Design", "owner": "Mia", "budget": 120, "status": "open"},
    {"id": "build", "parent_id": "project", "name": "Build", "owner": "Noah", "budget": 250, "status": "open"},
    {"id": "qa", "parent_id": "project", "name": "QA", "owner": "Sara", "budget": 80, "status": "open"},
]


# ---------- Layout helpers ----------


def _section(title: str, *content: object) -> html.Div:
    return html.Div([html.H4(title, className="mt-4 mb-2"), html.Hr(className="mb-3"), *content])


def _labelled(label: str, *content: object) -> html.Div:
    return html.Div(
        [html.Small(label, className="text-muted d-block mb-1"), *content],
        className="mb-3",
    )


app = make_app(__name__)
app.layout = Page(
    [
        _section(
            "Scalar bindings",
            Grid(
                [
                    [_labelled("TextBox (read-only view of title)", TextBox(title_src))],
                    [_labelled("TextField (editable, writes back to title)", TextField(title_src))],
                    [_labelled("TagList", TagList(tags_src))],
                    [
                        _labelled(
                            "Dropdown",
                            Dropdown(region_src, options=["north", "south", "east", "west"]),
                        )
                    ],
                    [_labelled("Toggle", Toggle(toggle_src, label="Enabled"))],
                    [_labelled("DatePicker", DatePicker(date_src))],
                    [
                        _labelled(
                            "Button (click count mirrors into a NUMBER source)",
                            Button("Click me", source=click_src),
                            html.Span(" Clicks: ", className="ms-2"),
                            TextBox(click_src),
                        )
                    ],
                ],
                columns=2,
            ),
        ),
        _section(
            "Plotly charts",
            Grid(
                [
                    [BarChart(sales_src, dimensions={"x": "region", "y": "revenue", "color": "product"})],
                    [LineChart(sales_src, dimensions={"x": "month", "y": "revenue", "color": "product"})],
                    [ScatterChart(sales_src, dimensions={"x": "revenue", "y": "region", "color": "product"})],
                    [PieChart(sales_src, dimensions={"names": "product", "values": "revenue"})],
                    [Histogram(sales_src, dimensions={"x": "revenue"})],
                    [BoxChart(sales_src, dimensions={"x": "region", "y": "revenue", "color": "product"})],
                    [Heatmap(heat_src, dimensions={"x": "x", "y": "y", "z": "count"})],
                    [Treemap(sales_src, dimensions={"path": ["region", "product"], "values": "revenue"})],
                    [Sankey(flow_src, dimensions={"source": "source", "target": "target", "value": "value"})],
                ],
                columns=3,
            ),
        ),
        _section(
            "Graph & Tree",
            Grid(
                [
                    [_labelled("Graph (cytoscape, preset layout)", Graph(graph_src, node_label="name"))],
                    [_labelled("Tree — treemap", Tree(tree_src, kind="treemap", label="name", value="size"))],
                    [_labelled("Tree — node_link", Tree(tree_src, kind="node_link", label="name"))],
                ],
                columns=3,
            ),
        ),
        _section(
            "Table bound to a writable CSV (FileDataSource)",
            Table(file_src, editable=True),
        ),
        _section(
            "Table bound to an in-memory SQLite (SqlDataSource)",
            Table(sql_src),
        ),
        _section(
            "TreeTable (editable, with aggregations)",
            TreeTableAIO(
                rows=tree_table_rows,
                editable=True,
                aggregations={"budget": "sum", "status": "equal"},
                column_labels={"owner": "Owner", "budget": "Budget", "status": "Status"},
                aio_id="everything-tree",
            ),
        ),
        _section(
            "Kanban (drag-and-drop)",
            KanbanBoard(kanban_src, columns=["todo", "doing", "done"]),
        ),
        _section(
            "Tabs / Loading / Modal / Toast",
            Tabs(
                [
                    Tab(
                        "Bar",
                        [BarChart(sales_src, dimensions={"x": "region", "y": "revenue", "color": "product"})],
                    ),
                    Tab(
                        "Line",
                        [LineChart(sales_src, dimensions={"x": "month", "y": "revenue", "color": "product"})],
                    ),
                    Tab("Raw table", [Table(sales_src)]),
                ]
            ),
            html.Div(
                [
                    dbc.Button("Open modal", id="open-modal", color="secondary", size="sm", className="me-2 mt-2"),
                    dbc.Button("Show toast", id="show-toast", color="info", size="sm", className="mt-2"),
                ]
            ),
            Modal(
                "Hello from a Modal",
                [html.P("This modal is part of the same demo app."), TextBox(title_src)],
                modal_id="demo-modal",
            ),
            Toast(
                "This is a toast notification.",
                header="Info",
                is_open=False,
                duration_ms=3000,
                toast_id="demo-toast",
            ),
            Loading(
                [
                    html.Div(
                        "Loading container (wraps children and shows spinner while callbacks run)",
                        className="text-muted mt-2",
                    )
                ]
            ),
        ),
        title_src.store(),
        tags_src.store(),
        toggle_src.store(),
        date_src.store(),
        region_src.store(),
        click_src.store(),
        sales_src.store(),
        heat_src.store(),
        flow_src.store(),
        graph_src.store(),
        tree_src.store(),
        kanban_src.store(),
        file_src.store(),
        sql_src.store(),
    ],
    title="Dashing Boards — Every Component Demo",
    subtitle="Every component mounted in one page to verify coexistence and callback registration.",
)


@callback(
    Output("demo-modal", "is_open"),
    Input("open-modal", "n_clicks"),
    prevent_initial_call=True,
)
def _open_modal(_n: int | None) -> bool:
    return True


@callback(
    Output("demo-toast", "is_open"),
    Input("show-toast", "n_clicks"),
    prevent_initial_call=True,
)
def _open_toast(_n: int | None) -> bool:
    return True


if __name__ == "__main__":
    app.run(debug=True)
