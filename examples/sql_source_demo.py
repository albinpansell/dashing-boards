"""SqlDataSource demo backed by an in-memory SQLite DB.

Shows a Table and a BarChart both bound to the same source.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from dashing_boards import BarChart, DataType, Page, SqlDataSource, Table, make_app


def make_source() -> SqlDataSource:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sales (region TEXT, product TEXT, revenue REAL)"))
        conn.execute(
            text("INSERT INTO sales VALUES ('north', 'A', 10),('north', 'B', 20),('south', 'A', 15),('south', 'B', 25)")
        )
    return SqlDataSource(
        engine,
        "SELECT region, product, revenue FROM sales",
        data_type=DataType.DATAFRAME,
        source_id="sales",
    )


source = make_source()
app = make_app(__name__)
app.layout = Page(
    [
        Table(source),
        BarChart(source, dimensions={"x": "region", "y": "revenue", "color": "product"}),
        source.store(),
    ],
    title="SQL source demo",
)

if __name__ == "__main__":
    app.run(debug=True)
