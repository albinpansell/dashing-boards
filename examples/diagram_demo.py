"""Diagram family demo laid out in a Grid."""

from __future__ import annotations


from dashing_boards import (
    BarChart,
    DataType,
    Grid,
    Histogram,
    LineChart,
    Page,
    PieChart,
    ScatterChart,
    StaticData,
    make_app,
)

rows = [
    {"region": "north", "product": "A", "revenue": 10, "month": "Jan"},
    {"region": "north", "product": "B", "revenue": 20, "month": "Jan"},
    {"region": "south", "product": "A", "revenue": 15, "month": "Feb"},
    {"region": "south", "product": "B", "revenue": 25, "month": "Feb"},
    {"region": "north", "product": "A", "revenue": 30, "month": "Mar"},
    {"region": "south", "product": "B", "revenue": 12, "month": "Mar"},
]
source = StaticData(rows, DataType.DATAFRAME, source_id="sales")

app = make_app(__name__)
app.layout = Page(
    [
        Grid(
            [
                [BarChart(source, dimensions={"x": "region", "y": "revenue", "color": "product"})],
                [LineChart(source, dimensions={"x": "month", "y": "revenue", "color": "product"})],
                [PieChart(source, dimensions={"names": "product", "values": "revenue"})],
                [ScatterChart(source, dimensions={"x": "revenue", "y": "region", "color": "product"})],
                [Histogram(source, dimensions={"x": "revenue"})],
            ],
            columns=2,
        ),
        source.store(),
    ],
    title="Diagram family demo",
)

if __name__ == "__main__":
    app.run(debug=True)
